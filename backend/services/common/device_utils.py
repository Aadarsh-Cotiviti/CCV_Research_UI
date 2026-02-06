"""
Common Device/HCPCS Code Utilities

Shared functions for HCPCS device code description retrieval and generation.
"""

import pandas as pd
import os
from pathlib import Path
from llm_wrapper import query_llm
from ..storage import fileStorage

# CSV cache file path
HCPCS_CSV_PATH = fileStorage.get_path("data","hcpcs_codes_all.csv")


def _preprocess_hcpcs_data():
    """
    Load HCPCS data from S3 parquet file and save as CSV
    
    This function should be called once to download and preprocess the data.
    Subsequent calls will use the cached CSV file.
    """
    from services.utils import load_s3_parquet_files
    
    print("📥 Downloading HCPCS data from S3...")
    
    # S3 path
    s3_path = "AI-Research/data/ml_globalhccnlymedicalcodeslibrary/HCPCODE/"
    
    try:
        # Load parquet file
        df = load_s3_parquet_files(
            s3_folder_path=s3_path,
            local_cache_name="hcpcs_codes_raw.parquet"
        )
        
        print(f"✅ Loaded {len(df)} records from S3")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Select and rename required columns
        # Note: S3 columns use PascalCase (e.g., HCPCSCode, not hcpcscode)
        required_columns = {
            'HCPCSCode': 'hcpcs_code',
            'HCPCSLongDescription': 'hcpcs_desc',
            'HCPCSActionEffectiveDates': 'hcpcs_effectivedt',
            'HCPCSTerminationDate': 'hcpcs_terminationdt'
        }
        
        # Check if all required columns exist
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
            print(f"   Available columns: {list(df.columns)}")
            return False
        
        # Select and rename columns
        df_selected = df[list(required_columns.keys())].copy()
        df_selected = df_selected.rename(columns=required_columns)
        
        # Convert effective date to datetime if not already
        df_selected['hcpcs_effectivedt'] = pd.to_datetime(
            df_selected['hcpcs_effectivedt'], 
            errors='coerce'
        )
        
        # No year filtering - use all available HCPCS data
        # (HCPCS codes are generally current unless explicitly terminated)
        # Filter out rows with invalid dates
        df_filtered = df_selected[df_selected['hcpcs_effectivedt'].notna()].copy()
        
        print(f"🔍 Total records with valid dates: {len(df_filtered)}")
        
        # Save to CSV
        fileStorage.write_csv(HCPCS_CSV_PATH, df_filtered, index=False, encoding='utf-8')
        # df_filtered.to_csv(HCPCS_CSV_PATH, index=False, encoding='utf-8')
        
        print(f"💾 Saved to: {HCPCS_CSV_PATH}")
        print(f"   File size: {os.path.getsize(HCPCS_CSV_PATH) / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error preprocessing HCPCS data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_device_description_from_local(code):
    """
    Get HCPCS device code description from local CSV file
    
    Args:
        code: HCPCS code (string)
        
    Returns:
        Description string if found, None otherwise
    """
    try:
        # Check if CSV exists, if not preprocess data
        if not os.path.exists(HCPCS_CSV_PATH):
            print(f"📂 HCPCS CSV not found, preprocessing data from S3...")
            success = _preprocess_hcpcs_data()
            if not success:
                print(f"⚠️  Failed to preprocess HCPCS data")
                return None
        
        # Load CSV
        df = pd.read_csv(HCPCS_CSV_PATH)
        
        # Check required columns
        if 'hcpcs_code' not in df.columns or 'hcpcs_desc' not in df.columns:
            print(f"⚠️  Expected columns 'hcpcs_code' and 'hcpcs_desc' not found. Available: {df.columns.tolist()}")
            return None
        
        # Convert code to string for comparison
        code_str = str(code).strip().upper()
        df['hcpcs_code'] = df['hcpcs_code'].astype(str).str.strip().str.upper()
        
        # Find matching code
        code_df = df[df['hcpcs_code'] == code_str]
        
        if not code_df.empty:
            # Return first match description
            return code_df.iloc[0]['hcpcs_desc']
        
        return None
        
    except Exception as e:
        print(f"⚠️  Could not load HCPCS description for {code}: {str(e)}")
        return None


def generate_device_description_with_llm(code, model="gpt-4.1-mini"):
    """
    Generate HCPCS device code description using LLM when not found in local database
    
    Args:
        code: HCPCS code (string)
        model: LLM model to use
        
    Returns:
        Generated description string
    """
    prompt = f"""
As a certified medical coding specialist, provide the official HCPCS code description for: {code}

Return ONLY the description text itself, without any prefix or code number.

Example:
For HCPCS A4657, return: "Syringe, with or without needle, each"

NOT: "HCPCS A4657: Syringe..."

Guidelines:
- Use only official HCPCS code descriptions
- Be concise and accurate
- Return ONLY the description text
- If the code is not recognized or invalid, state "Code not found in HCPCS database"
- Do not include any additional explanations or formatting
"""
    
    try:
        messages = [
            {"role": "system", "content": "You are an expert medical coding specialist with knowledge of HCPCS codes."},
            {"role": "user", "content": prompt}
        ]
        description = query_llm(messages, model=model)
        return description.strip()
    except Exception as e:
        print(f"⚠️  Error generating description for {code}: {str(e)}")
        return "Description unavailable"


def get_or_generate_device_description(code, model="gpt-4.1-mini", use_llm_fallback=True):
    """
    Get HCPCS device code description - first from local database, then from LLM if not found
    
    This is the main function that should be used throughout the application
    for retrieving HCPCS device code descriptions.
    
    Args:
        code: HCPCS code (string)
        model: LLM model to use for generation (default: gpt-4.1-mini)
        use_llm_fallback: Whether to use LLM if local description not found (default: True)
        
    Returns:
        Dictionary with:
            - hcpcs_code: The HCPCS code
            - description: The description text
            - source: 'internal_kb' or 'llm' or 'not_found'
    """
    # Try local database first
    local_desc = get_device_description_from_local(code)
    
    if local_desc:
        return {
            "hcpcs_code": code,
            "description": local_desc,
            "source": "internal_kb"
        }
    
    # If not found and LLM fallback is enabled, generate with LLM
    if use_llm_fallback:
        print(f"📝 Generating description for {code} using LLM...")
        llm_desc = generate_device_description_with_llm(code, model=model)
        return {
            "hcpcs_code": code,
            "description": llm_desc,
            "source": "llm"
        }
    
    # If no fallback, return None
    return {
        "hcpcs_code": code,
        "description": None,
        "source": "not_found"
    }

