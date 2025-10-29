import sqlite3

DB_PATH = "interactions2.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            topic TEXT,
            persona TEXT,
            question TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_interaction(session_id, topic, persona, question, response):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO interactions (session_id, topic, persona, question, response)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, topic, persona, question, response))
    conn.commit()
    conn.close()

def get_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT DISTINCT session_id, topic FROM interactions ORDER BY timestamp DESC LIMIT 50
    """)
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_session_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT question, response FROM interactions WHERE session_id = ? ORDER BY timestamp ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    messages = [{"role": "system", "content": "You are an APC research assistant."}]
    for q, r in rows:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": r})
    return messages

def rename_session(session_id, new_topic):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE interactions SET topic = ? WHERE session_id = ?
    """, (new_topic, session_id))
    conn.commit()
    conn.close()
