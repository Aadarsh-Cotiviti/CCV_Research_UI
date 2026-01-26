"""
Service Utilities for APC Research

This module contains all database operations, data processing utilities,
and helper functions used by service modules.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
import re
import boto3
from io import BytesIO

# Database path configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Global variable to cache CPT descriptions
_cpt_descriptions_cache = None


# ==================== CPT Description Utilities ====================

def load_cpt_descriptions():
    """Load CPT descriptions from xlsx file and cache them"""
    global _cpt_descriptions_cache
    
    if _cpt_descriptions_cache is not None:
        return _cpt_descriptions_cache
    
    try:
        xlsx_path = os.path.join(DATA_DIR, "CPT Codes with Long Descriptions 2025.xlsx")
        
        if not os.path.exists(xlsx_path):
            _cpt_descriptions_cache = {}
            return _cpt_descriptions_cache
        
        df = pd.read_excel(xlsx_path)
        
        _cpt_descriptions_cache = {}
        for _, row in df.iterrows():
            try:
                cpt_code = str(row['CPTCd']).strip()
                description = str(row['FullDesc']).strip()
                _cpt_descriptions_cache[cpt_code] = description
            except Exception:
                continue
        
        return _cpt_descriptions_cache
    except Exception:
        _cpt_descriptions_cache = {}
        return _cpt_descriptions_cache


def get_cpt_description(cpt_code):
    """Get description for a CPT code from the xlsx file"""
    descriptions = load_cpt_descriptions()
    cpt_code_str = str(cpt_code).strip()
    return descriptions.get(cpt_code_str)


def replace_cpt_descriptions_in_text(text):
    """
    Replace CPT descriptions in text with descriptions from xlsx file.
    Looks for patterns like 'CPT XXXXX - description' or 'XXXXX - description'
    """
    modified_text = text
    replacements_made = set()
    
    lines = modified_text.split('\n')
    new_lines = []
    
    for line in lines:
        matches = re.finditer(r'(?:CPT\s+)?(\d{5})\s*[-:–—]\s*([^\n\|\*]+)', line)
        
        modified_line = line
        offset = 0
        
        for match in matches:
            cpt_code = match.group(1)
            full_match = match.group(0)
            
            xlsx_desc = get_cpt_description(cpt_code)
            
            if xlsx_desc and cpt_code not in replacements_made:
                has_cpt_prefix = 'CPT' in full_match[:10]
                prefix = 'CPT ' if has_cpt_prefix else ''
                new_text = f"{prefix}{cpt_code} - {xlsx_desc}"
                
                start = match.start() + offset
                end = match.end() + offset
                modified_line = modified_line[:start] + new_text + modified_line[end:]
                offset += len(new_text) - len(full_match)
                
                replacements_made.add(cpt_code)
        
        new_lines.append(modified_line)
    
    return '\n'.join(new_lines)


# ==================== Date/Time Utilities ====================

def compute_audit_window():
    """Compute the audit window for claims (3 years back from today)"""
    current_date = datetime.now()
    start_date = current_date - timedelta(days=1095)  # 3 years
    return start_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")


def get_timestamp():
    """Get current timestamp in standard format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================== Database: Notes ====================

def init_notes_db():
    """Initialize notes database"""
    db_path = os.path.join(DATA_DIR, "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            cpt_code TEXT,
            notes_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_notes(session_id, cpt_code, notes_text):
    """Save or update notes for a session/CPT code"""
    db_path = os.path.join(DATA_DIR, "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = get_timestamp()
    
    cursor.execute("""
        SELECT id FROM notes WHERE session_id = ? AND cpt_code = ?
    """, (session_id, cpt_code))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE notes SET notes_text = ?, updated_at = ?
            WHERE session_id = ? AND cpt_code = ?
        """, (notes_text, timestamp, session_id, cpt_code))
    else:
        cursor.execute("""
            INSERT INTO notes (session_id, cpt_code, notes_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, cpt_code, notes_text, timestamp, timestamp))
    
    conn.commit()
    conn.close()


def get_notes(session_id, cpt_code):
    """Retrieve notes for a session/CPT code"""
    db_path = os.path.join(DATA_DIR, "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT notes_text FROM notes WHERE session_id = ? AND cpt_code = ?
    """, (session_id, cpt_code))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else ""


# ==================== Database: Chat History ====================

def init_chat_db():
    """Initialize chat database for section-specific conversations"""
    db_path = os.path.join(DATA_DIR, "apc_chat.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cpt_code TEXT NOT NULL,
            section_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_chat_message(session_id, cpt_code, section_id, user_message, ai_response):
    """Save a chat message exchange"""
    db_path = os.path.join(DATA_DIR, "apc_chat.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = get_timestamp()
    
    cursor.execute("""
        INSERT INTO chat_history (session_id, cpt_code, section_id, user_message, ai_response, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, cpt_code, section_id, user_message, ai_response, timestamp))
    
    conn.commit()
    conn.close()


def get_chat_history(session_id, cpt_code, section_id):
    """Retrieve chat history for a specific section"""
    db_path = os.path.join(DATA_DIR, "apc_chat.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_message, ai_response, created_at 
        FROM chat_history 
        WHERE session_id = ? AND cpt_code = ? AND section_id = ?
        ORDER BY created_at ASC
    """, (session_id, cpt_code, section_id))
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"user": r[0], "ai": r[1], "timestamp": r[2]} for r in results]


# ==================== Database: Research Sessions ====================

def init_research_sessions_db():
    """Initialize research sessions database"""
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            topic TEXT NOT NULL,
            cpt_code TEXT NOT NULL,
            model_used TEXT NOT NULL,
            analysis_result TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_research_session(session_id, topic, cpt_code, model_used, analysis_result):
    """Save or update a research session"""
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = get_timestamp()
    
    cursor.execute("""
        SELECT id FROM research_sessions WHERE session_id = ?
    """, (session_id,))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE research_sessions 
            SET topic = ?, cpt_code = ?, model_used = ?, analysis_result = ?, updated_at = ?
            WHERE session_id = ?
        """, (topic, cpt_code, model_used, analysis_result, timestamp, session_id))
    else:
        cursor.execute("""
            INSERT INTO research_sessions 
            (session_id, topic, cpt_code, model_used, analysis_result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, topic, cpt_code, model_used, analysis_result, timestamp, timestamp))
    
    conn.commit()
    conn.close()


def get_all_research_sessions():
    """Get all research sessions ordered by most recent first"""
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, topic, cpt_code, created_at, updated_at
        FROM research_sessions
        ORDER BY updated_at DESC
    """)
    
    sessions = cursor.fetchall()
    conn.close()
    
    return sessions


def get_research_session(session_id):
    """Get a specific research session"""
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, topic, cpt_code, model_used, analysis_result, created_at, updated_at
        FROM research_sessions
        WHERE session_id = ?
    """, (session_id,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return {
            "session_id": session[0],
            "topic": session[1],
            "cpt_code": session[2],
            "model": session[3],
            "result": session[4],
            "created_at": session[5],
            "updated_at": session[6]
        }
    return None


def delete_research_session(session_id):
    """Delete a research session and all associated data"""
    # Delete from research sessions
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM research_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    
    # Delete associated chat history
    db_path = os.path.join(DATA_DIR, "apc_chat.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    
    # Delete associated notes
    db_path = os.path.join(DATA_DIR, "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    
    # Delete associated feedback
    db_path = os.path.join(DATA_DIR, "apc_feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accuracy_feedback WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def update_research_topic(session_id, new_topic):
    """Update the topic name for a research session"""
    db_path = os.path.join(DATA_DIR, "apc_research_sessions.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = get_timestamp()
    
    cursor.execute("""
        UPDATE research_sessions 
        SET topic = ?, updated_at = ?
        WHERE session_id = ?
    """, (new_topic, timestamp, session_id))
    
    conn.commit()
    conn.close()


# ==================== Database: Accuracy Feedback ====================

def init_feedback_db():
    """Initialize feedback database for accuracy ratings"""
    db_path = os.path.join(DATA_DIR, "apc_feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cpt_code TEXT NOT NULL,
            section_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_accuracy_feedback(session_id, cpt_code, section_id, rating, reason=None):
    """Save accuracy feedback for a section"""
    db_path = os.path.join(DATA_DIR, "apc_feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = get_timestamp()
    
    cursor.execute("""
        SELECT id FROM accuracy_feedback 
        WHERE session_id = ? AND cpt_code = ? AND section_id = ?
    """, (session_id, cpt_code, section_id))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE accuracy_feedback 
            SET rating = ?, reason = ?, created_at = ?
            WHERE session_id = ? AND cpt_code = ? AND section_id = ?
        """, (rating, reason, timestamp, session_id, cpt_code, section_id))
    else:
        cursor.execute("""
            INSERT INTO accuracy_feedback 
            (session_id, cpt_code, section_id, rating, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, cpt_code, section_id, rating, reason, timestamp))
    
    conn.commit()
    conn.close()


def get_accuracy_feedback(session_id, cpt_code, section_id):
    """Retrieve accuracy feedback for a section"""
    db_path = os.path.join(DATA_DIR, "apc_feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT rating, reason FROM accuracy_feedback 
        WHERE session_id = ? AND cpt_code = ? AND section_id = ?
    """, (session_id, cpt_code, section_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return {"rating": result[0], "reason": result[1]} if result else None


# ==================== Database Initialization ====================

def init_all_databases():
    """Initialize all APC research databases"""
    init_notes_db()
    init_chat_db()
    init_research_sessions_db()
    init_feedback_db()


# ==================== AWS S3 Parquet Files Loading ====================

def load_s3_parquet_files(
    s3_folder_path,
    local_cache_name=None,
    s3_bucket="ml-ccv-unrestricted",
    force_download=False
):
    """
    Load and concatenate all parquet files from S3 folder with local caching
    
    This function downloads parquet files from S3, concatenates them, and caches locally.
    Subsequent calls will use the cached version unless force_download=True.
    
    Args:
        s3_folder_path: S3 folder path (e.g., "AI-Research/data/ml_globalhccnlymedicalcodeslibrary/Ing_CPTChange/")
        local_cache_name: Name for local cache file (e.g., "ing_cpt_change.parquet")
                         If None, will auto-generate from s3_folder_path
        s3_bucket: S3 bucket name (default: "ml-ccv-unrestricted")
        force_download: If True, always download from S3 even if cache exists
        
    Returns:
        pandas.DataFrame: Concatenated dataframe from all parquet files
        
    Example:
        # Load CPT changes from S3
        df = load_s3_parquet_files(
            s3_folder_path="AI-Research/data/ml_globalhccnlymedicalcodeslibrary/Ing_CPTChange/",
            local_cache_name="ing_cpt_change.parquet"
        )
        
        # Force re-download
        df = load_s3_parquet_files(
            s3_folder_path="AI-Research/data/ml_globalhccnlymedicalcodeslibrary/Ing_CPTChange/",
            force_download=True
        )
    """
    # Auto-generate cache name if not provided
    if local_cache_name is None:
        # Extract meaningful name from path
        folder_name = s3_folder_path.rstrip('/').split('/')[-1]
        local_cache_name = f"{folder_name.lower()}_combined.parquet"
    
    # Local cache path in data directory
    local_cache_path = os.path.join(DATA_DIR, local_cache_name)
    
    # Check if local cache exists
    if os.path.exists(local_cache_path) and not force_download:
        print(f"✅ Loading from local cache: {local_cache_path}")
        try:
            df = pd.read_parquet(local_cache_path)
            print(f"📊 Loaded {len(df):,} rows, {len(df.columns)} columns from cache")
            return df
        except Exception as e:
            print(f"⚠️  Failed to load cache: {str(e)}")
            print("📥 Will download from S3...")
    
    # Download from S3
    print(f"📥 Downloading parquet files from S3...")
    print(f"   Bucket: s3://{s3_bucket}")
    print(f"   Folder: {s3_folder_path}")
    
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # List all files in the folder
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_folder_path
        )
        
        if 'Contents' not in response:
            raise ValueError(f"No files found in s3://{s3_bucket}/{s3_folder_path}")
        
        # Filter for parquet files only
        parquet_files = [
            obj['Key'] for obj in response['Contents']
            if obj['Key'].endswith('.parquet') and not obj['Key'].endswith('/')
        ]
        
        if not parquet_files:
            raise ValueError(f"No parquet files found in s3://{s3_bucket}/{s3_folder_path}")
        
        print(f"📁 Found {len(parquet_files)} parquet file(s)")
        
        # Download all parquet files
        dfs = []
        total_rows = 0
        
        for i, file_key in enumerate(parquet_files, 1):
            filename = file_key.split('/')[-1]
            print(f"   [{i}/{len(parquet_files)}] Downloading {filename}...", end=" ")
            
            try:
                # Download file to memory
                obj = s3_client.get_object(Bucket=s3_bucket, Key=file_key)
                parquet_data = obj['Body'].read()
                
                # Read parquet from bytes
                df_temp = pd.read_parquet(BytesIO(parquet_data))
                dfs.append(df_temp)
                total_rows += len(df_temp)
                print(f"✅ {len(df_temp):,} rows")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                continue
        
        if not dfs:
            raise ValueError("No parquet files were successfully downloaded")
        
        # Process dataframes - concatenate only if multiple files
        if len(dfs) == 1:
            print(f"\n✅ Single file: {len(dfs[0]):,} rows, {len(dfs[0].columns)} columns")
            df_combined = dfs[0]
        else:
            print(f"\n🔗 Concatenating {len(dfs)} dataframe(s)...")
            df_combined = pd.concat(dfs, axis=0, ignore_index=True)
            print(f"✅ Combined: {len(df_combined):,} rows, {len(df_combined.columns)} columns")
        
        # Save to local cache
        print(f"\n💾 Saving to local cache: {local_cache_path}")
        os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
        df_combined.to_parquet(local_cache_path, index=False)
        file_size_mb = os.path.getsize(local_cache_path) / (1024 * 1024)
        print(f"✅ Cache saved successfully ({file_size_mb:.2f} MB)")
        
        return df_combined
        
    except Exception as e:
        print(f"❌ Error downloading from S3: {str(e)}")
        raise


def clear_parquet_cache(cache_name):
    """
    Clear local parquet cache file
    
    Args:
        cache_name: Name of the cache file to delete (e.g., "ing_cpt_change.parquet")
        
    Example:
        clear_parquet_cache("ing_cpt_change.parquet")
    """
    cache_path = os.path.join(DATA_DIR, cache_name)
    if os.path.exists(cache_path):
        os.remove(cache_path)
        print(f"🗑️  Deleted cache: {cache_path}")
        return True
    else:
        print(f"⚠️  Cache not found: {cache_path}")
        return False


def list_parquet_caches():
    """
    List all cached parquet files in data directory
    
    Returns:
        List of tuples: (filename, size_mb, modified_time)
    """
    caches = []
    if not os.path.exists(DATA_DIR):
        return caches
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.parquet'):
            filepath = os.path.join(DATA_DIR, filename)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            caches.append((filename, size_mb, mtime))
    
    return sorted(caches, key=lambda x: x[2], reverse=True)