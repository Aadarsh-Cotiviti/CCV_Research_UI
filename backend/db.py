# Create a new session by inserting a dummy system message
def create_session(session_id, topic, persona="Analysts"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO interactions (session_id, topic, persona, question, response)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, topic, persona, "", ""))
    conn.commit()
    conn.close()
import sqlite3

DB_PATH = "interactions2.db"
from services.db_access import (
    create_interaction_session,
    delete_interaction_session,
    get_interaction_history,
    get_interaction_sessions,
    init_interactions_db,
    rename_interaction_session,
    save_interaction,
)

# Legacy exports for existing imports
init_db = init_interactions_db
create_session = create_interaction_session
get_sessions = get_interaction_sessions
get_session_history = get_interaction_history
rename_session = rename_interaction_session
delete_session = delete_interaction_session
# def save_interaction(session_id, topic, persona, question, response):
