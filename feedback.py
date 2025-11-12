import streamlit as st
from datetime import datetime
import sqlite3
import os

def init_feedback_db():
    """Initialize feedback database"""
    db_path = os.path.join(os.path.dirname(__file__), "feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model_used TEXT,
            research_type TEXT,
            topic TEXT,
            ui_rating INTEGER,
            content_rating INTEGER,
            feedback_text TEXT,
            submitted_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def save_feedback(model_used, research_type, topic, ui_rating, content_rating, feedback_text):
    """Save feedback to database"""
    db_path = os.path.join(os.path.dirname(__file__), "feedback.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO feedback (timestamp, model_used, research_type, topic, ui_rating, content_rating, feedback_text, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, model_used, research_type, topic, ui_rating, content_rating, feedback_text, timestamp))
    
    conn.commit()
    conn.close()

def render_feedback_page():
    """Render the feedback form page"""
    st.title("📝 User Feedback")
    st.markdown("---")
    
    st.markdown("""
        We value your feedback! Please take a moment to share your experience with the application.
        All fields are optional, but the more details you provide, the better we can improve.
    """)
    
    st.markdown("---")
    
    # Custom CSS for feedback page
    st.markdown("""
        <style>
            /* Form labels white */
            .stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
                color: #ffffff !important;
                font-weight: bold !important;
            }
            /* Hide radio button circles, make entire label clickable */
            .stRadio div[role="radiogroup"] {
                gap: 15px;
                display: flex;
                flex-direction: row !important;
            }
            .stRadio div[role="radiogroup"] label {
                background-color: #2c2c2c;
                border: 2px solid #555;
                border-radius: 12px;
                padding: 20px 15px;
                cursor: pointer;
                transition: all 0.3s;
                flex: 1;
                text-align: center;
                min-height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: #ffffff !important;
            }
            .stRadio div[role="radiogroup"] label:hover {
                border-color: #ffffff;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(255, 255, 255, 0.1);
            }
            .stRadio div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
                display: none !important;
            }
            /* Selected state */
            .stRadio div[role="radiogroup"] label:has(input:checked) {
                border-width: 3px;
                background-color: #1e1e1e;
            }
            /* Bad rating - Red */
            .stRadio div[role="radiogroup"] label:nth-child(2):hover,
            .stRadio div[role="radiogroup"] label:nth-child(2):has(input:checked) {
                border-color: #ff4444 !important;
                background-color: rgba(255, 68, 68, 0.1) !important;
            }
            /* Medium rating - Yellow */
            .stRadio div[role="radiogroup"] label:nth-child(3):hover,
            .stRadio div[role="radiogroup"] label:nth-child(3):has(input:checked) {
                border-color: #ffaa00 !important;
                background-color: rgba(255, 170, 0, 0.1) !important;
            }
            /* Good rating - Green */
            .stRadio div[role="radiogroup"] label:nth-child(4):hover,
            .stRadio div[role="radiogroup"] label:nth-child(4):has(input:checked) {
                border-color: #00cc44 !important;
                background-color: rgba(0, 204, 68, 0.1) !important;
            }
            /* Submit button styling */
            .stForm button[type="submit"] {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }
            .stForm button[type="submit"]:hover {
                background-color: #f0f0f0 !important;
                color: #000000 !important;
            }
            /* Regular buttons styling */
            .stButton > button {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }
            .stButton > button:hover {
                background-color: #f0f0f0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("feedback_form"):
        st.subheader("📋 Session Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_used = st.selectbox(
                "Model Used (Optional)",
                ["", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-5", "gpt-5-mini", "gpt-5-nano", "MedGEMMA-27b"],
                help="Select the AI model you used for your research"
            )
        
        with col2:
            research_type = st.selectbox(
                "Research Type (Optional)",
                ["", "APC Research", "Chat Research"],
                help="Select the type of research you performed"
            )
        
        topic = st.text_input(
            "Topic/CPT Code (Optional)",
            placeholder="e.g., Bronchial Biopsy, CPT 31628",
            help="Enter the topic or CPT code you researched"
        )
        
        st.markdown("---")
        st.subheader("⭐ Rate Your Experience")
        
        st.markdown("**UI Rating**")
        st.markdown("<p style='color: #b0b0b0; font-size: 0.9rem; margin-bottom: 15px;'>How would you rate the user interface and overall design?</p>", unsafe_allow_html=True)
        ui_rating = st.radio(
            "UI Rating",
            options=["Not Rated", "😞 Bad - Poor experience", "😐 Medium - Neutral experience", "😊 Good - Great experience"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("**Content Quality Rating**")
        st.markdown("<p style='color: #b0b0b0; font-size: 0.9rem; margin-bottom: 15px;'>How would you rate the quality and accuracy of the generated content?</p>", unsafe_allow_html=True)
        content_rating = st.radio(
            "Content Quality Rating",
            options=["Not Rated", "😞 Bad - Inaccurate content", "😐 Medium - Acceptable content", "😊 Good - Excellent content"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Convert radio selections to numeric values
        rating_map = {
            "Not Rated": 0, 
            "😞 Bad - Poor experience": 1, 
            "😐 Medium - Neutral experience": 2, 
            "😊 Good - Great experience": 3,
            "😞 Bad - Inaccurate content": 1,
            "😐 Medium - Acceptable content": 2,
            "😊 Good - Excellent content": 3
        }
        ui_rating_value = rating_map[ui_rating]
        content_rating_value = rating_map[content_rating]
        
        st.markdown("---")
        st.subheader("💬 Additional Comments")
        
        feedback_text = st.text_area(
            "Your Feedback (Optional)",
            placeholder="Please share your thoughts, suggestions, or any issues you encountered...",
            height=150,
            help="Any additional feedback to help us improve the application"
        )
        
        st.markdown("---")
        
        col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
        
        with col_submit2:
            submit_btn = st.form_submit_button("📤 Submit Feedback", use_container_width=True)
        
        if submit_btn:
            # Check if at least one field is filled
            if any([model_used, research_type, topic, ui_rating_value > 0, content_rating_value > 0, feedback_text]):
                # Save feedback
                save_feedback(
                    model_used if model_used else "Not specified",
                    research_type if research_type else "Not specified",
                    topic if topic else "Not specified",
                    ui_rating_value,
                    content_rating_value,
                    feedback_text if feedback_text else "No additional comments"
                )
                
                st.success("✅ Thank you for your feedback! Your input has been recorded.")
                st.balloons()
                
                # Show summary
                st.markdown("---")
                st.subheader("📊 Feedback Summary")
                
                summary_col1, summary_col2 = st.columns(2)
                with summary_col1:
                    if model_used:
                        st.info(f"**Model:** {model_used}")
                    if research_type:
                        st.info(f"**Type:** {research_type}")
                    if topic:
                        st.info(f"**Topic:** {topic}")
                
                with summary_col2:
                    if ui_rating_value > 0:
                        rating_text = {1: "😞 Bad", 2: "😐 Medium", 3: "😊 Good"}
                        st.metric("UI Rating", rating_text.get(ui_rating_value, "Not rated"))
                    if content_rating_value > 0:
                        rating_text = {1: "😞 Bad", 2: "😐 Medium", 3: "😊 Good"}
                        st.metric("Content Rating", rating_text.get(content_rating_value, "Not rated"))
                
                if feedback_text:
                    st.text_area("Your Comments", feedback_text, disabled=True)
            else:
                st.warning("⚠️ Please provide at least some feedback before submitting.")
    
    st.markdown("---")
    st.info("💡 Use the navigation in the sidebar to return to Chat Research or APC Research.")

if __name__ == "__main__":
    init_feedback_db()
    render_feedback_page()
