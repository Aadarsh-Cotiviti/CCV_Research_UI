"""
Centralized database helpers for backend services.
All SQLite interactions live here to keep DB logic in one place.
"""

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

INTERACTIONS_DB_PATH = os.path.join(BASE_DIR, "interactions2.db")
NOTES_DB_PATH = os.path.join(DATA_DIR, "apc_notes.db")
CHAT_DB_PATH = os.path.join(DATA_DIR, "apc_chat.db")
RESEARCH_DB_PATH = os.path.join(DATA_DIR, "apc_research_sessions.db")
ACCURACY_FEEDBACK_DB_PATH = os.path.join(DATA_DIR, "apc_feedback.db")
USER_FEEDBACK_DB_PATH = os.path.join(BASE_DIR, "feedback.db")


def _ensure_parent(db_path: str) -> None:
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _connect(db_path: str) -> sqlite3.Connection:
    _ensure_parent(db_path)
    return sqlite3.connect(db_path)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================== Interactions (chat mode) ====================

def init_interactions_db() -> None:
    conn = _connect(INTERACTIONS_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            topic TEXT,
            persona TEXT,
            question TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def create_interaction_session(session_id: str, topic: str, persona: str = "Analysts") -> None:
    conn = _connect(INTERACTIONS_DB_PATH)
    conn.execute(
        """
        INSERT INTO interactions (session_id, topic, persona, question, response)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, topic, persona, "", ""),
    )
    conn.commit()
    conn.close()


def save_interaction(session_id: str, topic: str, persona: str, question: str, response: str) -> None:
    conn = _connect(INTERACTIONS_DB_PATH)
    conn.execute(
        """
        INSERT INTO interactions (session_id, topic, persona, question, response)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, topic, persona, question, response),
    )
    conn.commit()
    conn.close()


def get_interaction_sessions(limit: int = 50) -> List[Tuple[str, str]]:
    conn = _connect(INTERACTIONS_DB_PATH)
    cursor = conn.execute(
        """
        SELECT DISTINCT session_id, topic FROM interactions
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )
    sessions = cursor.fetchall()
    conn.close()
    return sessions


def get_interaction_history(session_id: str) -> List[Tuple[str, str]]:
    conn = _connect(INTERACTIONS_DB_PATH)
    cursor = conn.execute(
        """
        SELECT question, response FROM interactions
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def rename_interaction_session(session_id: str, new_topic: str) -> None:
    conn = _connect(INTERACTIONS_DB_PATH)
    conn.execute(
        """
        UPDATE interactions SET topic = ? WHERE session_id = ?
        """,
        (new_topic, session_id),
    )
    conn.commit()
    conn.close()


def delete_interaction_session(session_id: str) -> None:
    conn = _connect(INTERACTIONS_DB_PATH)
    conn.execute("DELETE FROM interactions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ==================== Notes ====================

def init_notes_db() -> None:
    conn = _connect(NOTES_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            cpt_code TEXT,
            notes_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_notes(session_id: str, cpt_code: str, notes_text: str) -> None:
    conn = _connect(NOTES_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute(
        """
        SELECT id FROM notes WHERE session_id = ? AND cpt_code = ?
        """,
        (session_id, cpt_code),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE notes SET notes_text = ?, updated_at = ?
            WHERE session_id = ? AND cpt_code = ?
            """,
            (notes_text, timestamp, session_id, cpt_code),
        )
    else:
        cursor.execute(
            """
            INSERT INTO notes (session_id, cpt_code, notes_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, cpt_code, notes_text, timestamp, timestamp),
        )
    conn.commit()
    conn.close()


def get_notes(session_id: str, cpt_code: str) -> str:
    conn = _connect(NOTES_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT notes_text FROM notes WHERE session_id = ? AND cpt_code = ?
        """,
        (session_id, cpt_code),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""


# ==================== Chat History ====================

def init_chat_db() -> None:
    conn = _connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cpt_code TEXT NOT NULL,
            section_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_chat_message(
    session_id: str, cpt_code: str, section_id: str, user_message: str, ai_response: str
) -> None:
    conn = _connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute(
        """
        INSERT INTO chat_history (session_id, cpt_code, section_id, user_message, ai_response, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, cpt_code, section_id, user_message, ai_response, timestamp),
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id: str, cpt_code: str, section_id: str) -> List[Dict[str, Any]]:
    conn = _connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT m.role, m.content, m.created_at
        FROM messages m
        JOIN chats c ON c.id = m.chat_id
        JOIN sections s ON s.chat_id = c.id
        WHERE s.session_id = ?
          AND s.id = ?
          AND m.role != 'system'
        ORDER BY m.created_at ASC
        """,
        (session_id, section_id),
    )
    results = cursor.fetchall()
    conn.close()

    # Map Next.js roles into legacy shape (user/assistant pairs)
    mapped: List[Dict[str, Any]] = []
    pending: Optional[Dict[str, Any]] = None

    for role, content, ts in results:
        timestamp = str(ts)
        if role == "user":
            if pending and "ai" not in pending:
                mapped.append(pending)
            pending = {"user": content, "timestamp": timestamp}
        elif role == "assistant":
            if pending and "user" in pending and "ai" not in pending:
                pending["ai"] = content
                mapped.append(pending)
                pending = None
            else:
                mapped.append({"user": "", "ai": content, "timestamp": timestamp})

    if pending:
        mapped.append(pending)

    return mapped


# ==================== Research Sessions ====================

def init_research_sessions_db() -> None:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()


def save_research_session(
    session_id: str, topic: str, cpt_code: str, model_used: str, analysis_result: str
) -> None:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute("SELECT id FROM research_sessions WHERE session_id = ?", (session_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE research_sessions
            SET topic = ?, cpt_code = ?, model_used = ?, analysis_result = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (topic, cpt_code, model_used, analysis_result, timestamp, session_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO research_sessions
            (session_id, topic, cpt_code, model_used, analysis_result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, topic, cpt_code, model_used, analysis_result, timestamp, timestamp),
        )
    conn.commit()
    conn.close()


def get_all_research_sessions() -> List[Tuple[str, str, str, str, str]]:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, topic, cpt_code, created_at, updated_at
        FROM research_sessions
        ORDER BY updated_at DESC
        """
    )
    sessions = cursor.fetchall()
    conn.close()
    return sessions


def get_research_session(session_id: str) -> Optional[Dict[str, str]]:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, topic, cpt_code, model_used, analysis_result, created_at, updated_at
        FROM research_sessions
        WHERE session_id = ?
        """,
        (session_id,),
    )
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
            "updated_at": session[6],
        }
    return None


def delete_research_session(session_id: str) -> None:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM research_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    conn = _connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    conn = _connect(NOTES_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    conn = _connect(ACCURACY_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accuracy_feedback WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def update_research_topic(session_id: str, new_topic: str) -> None:
    conn = _connect(RESEARCH_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute(
        """
        UPDATE research_sessions
        SET topic = ?, updated_at = ?
        WHERE session_id = ?
        """,
        (new_topic, timestamp, session_id),
    )
    conn.commit()
    conn.close()


# ==================== Accuracy Feedback ====================

def init_accuracy_feedback_db() -> None:
    conn = _connect(ACCURACY_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accuracy_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cpt_code TEXT NOT NULL,
            section_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_accuracy_feedback(
    session_id: str, cpt_code: str, section_id: str, rating: str, reason: Optional[str] = None
) -> None:
    conn = _connect(ACCURACY_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute(
        """
        SELECT id FROM accuracy_feedback
        WHERE session_id = ? AND cpt_code = ? AND section_id = ?
        """,
        (session_id, cpt_code, section_id),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE accuracy_feedback
            SET rating = ?, reason = ?, created_at = ?
            WHERE session_id = ? AND cpt_code = ? AND section_id = ?
            """,
            (rating, reason, timestamp, session_id, cpt_code, section_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO accuracy_feedback
            (session_id, cpt_code, section_id, rating, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, cpt_code, section_id, rating, reason, timestamp),
        )
    conn.commit()
    conn.close()


def get_accuracy_feedback(session_id: str, cpt_code: str, section_id: str) -> Optional[Dict[str, str]]:
    conn = _connect(ACCURACY_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT rating, reason FROM accuracy_feedback
        WHERE session_id = ? AND cpt_code = ? AND section_id = ?
        """,
        (session_id, cpt_code, section_id),
    )
    result = cursor.fetchone()
    conn.close()
    return {"rating": result[0], "reason": result[1]} if result else None


# ==================== User Feedback (UI/content form) ====================

def init_user_feedback_db() -> None:
    conn = _connect(USER_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model_used TEXT,
            research_type TEXT,
            topic TEXT,
            ui_rating INTEGER,
            content_rating INTEGER,
            section1_accuracy TEXT,
            section2_accuracy TEXT,
            section3_accuracy TEXT,
            section4_accuracy TEXT,
            section5_accuracy TEXT,
            section6_accuracy TEXT,
            feedback_text TEXT,
            submitted_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_user_feedback(
    model_used: Optional[str],
    research_type: Optional[str],
    topic: Optional[str],
    ui_rating: int,
    content_rating: int,
    section_ratings: Dict[str, str],
    feedback_text: str,
) -> None:
    conn = _connect(USER_FEEDBACK_DB_PATH)
    cursor = conn.cursor()
    timestamp = _timestamp()
    cursor.execute(
        """
        INSERT INTO feedback (
            timestamp, model_used, research_type, topic, ui_rating,
            content_rating, section1_accuracy, section2_accuracy,
            section3_accuracy, section4_accuracy, section5_accuracy, section6_accuracy,
            feedback_text, submitted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            model_used,
            research_type,
            topic,
            ui_rating,
            content_rating,
            section_ratings.get("section1", "Not Rated"),
            section_ratings.get("section2", "Not Rated"),
            section_ratings.get("section3", "Not Rated"),
            section_ratings.get("section4", "Not Rated"),
            section_ratings.get("section5", "Not Rated"),
            section_ratings.get("section6", "Not Rated"),
            feedback_text,
            timestamp,
        ),
    )
    conn.commit()
    conn.close()


# ==================== Initialization helper ====================

def init_all_databases() -> None:
    init_notes_db()
    init_chat_db()
    init_research_sessions_db()
    init_accuracy_feedback_db()
    init_interactions_db()
    init_user_feedback_db()
