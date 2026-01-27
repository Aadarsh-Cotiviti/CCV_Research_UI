"""
UI Utilities and Shared Components

This module contains reusable UI components and styling functions
used across all view modules.
"""

import streamlit as st
from datetime import datetime
from services import final_assessment_service
from services.utils import save_accuracy_feedback, save_chat_message, get_chat_history
from services.apc_orchestrator import chat_with_section


def get_source_color(source: str) -> str:
    """
    Get color code based on data source
    
    Args:
        source: Data source identifier ('internal_kb', 'local_kb', 'llm', etc.)
        
    Returns:
        Hex color code string
    """
    source_colors = {
        'internal_kb': '#2d7a4f',  # Green for internal knowledge base
        'local_kb': '#2d7a4f',     # Green for local knowledge base (same as internal_kb)
        'llm': '#1f1f1f',           # Black for LLM generated content
        'external': '#4a90e2',      # Blue for external sources (if needed)
        'hybrid': '#8b6914'         # Gold for hybrid sources (if needed)
    }
    return source_colors.get(source.lower(), '#1f1f1f')  # Default to black


def format_text_with_source(text: str, source: str, bold: bool = False) -> str:
    """
    Format text with color based on source
    
    Args:
        text: Text content to display
        source: Data source identifier
        bold: Whether to make text bold
        
    Returns:
        HTML formatted string with appropriate color
    """
    color = get_source_color(source)
    font_weight = 'bold' if bold else 'normal'
    # Use style tag to define a unique class with high specificity
    unique_id = f"src-{hash(text) % 10000}"
    
    # Escape HTML special characters but preserve line breaks
    import html
    escaped_text = html.escape(text)
    # Convert newlines to <br> tags for proper display
    escaped_text = escaped_text.replace('\n', '<br>')
    
    return f"""
    <style>
        #{unique_id}.source-colored-text {{
            color: {color} !important;
            font-weight: {font_weight};
            display: inline-block;
            white-space: pre-wrap;
        }}
    </style>
    <span id="{unique_id}" class="source-colored-text">{escaped_text}</span>
    """


def render_source_legend():
    """Render a legend showing color coding for different sources"""
    st.markdown("""
        <style>
            .source-legend-container {
                padding: 10px;
                background-color: #f7f7f8;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            .source-legend-item {
                display: inline-block;
                margin-left: 10px;
                font-weight: bold;
            }
            #legend-green.source-legend-item {
                color: #2d7a4f !important;
            }
            #legend-black.source-legend-item {
                color: #1f1f1f !important;
            }
        </style>
        <div class='source-legend-container'>
            <strong style='color: #1f1f1f !important;'>Source Legend:</strong>
            <div id='legend-green' class='source-legend-item'>● Internal KB</div>
            <div id='legend-black' class='source-legend-item'>● LLM Generated</div>
        </div>
    """, unsafe_allow_html=True)


def apply_custom_css():
    """Apply custom CSS styling for the entire application"""
    st.markdown("""
        <style>
            /* Tab styling - make text white */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                color: #ffffff !important;
                font-weight: 500 !important;
            }
            .stTabs [data-baseweb="tab"]:hover {
                color: #1f1f1f !important;
            }
            .stTabs [aria-selected="true"] {
                color: #1f1f1f !important;
                font-weight: 600 !important;
            }
            
            .stMarkdown p, .stMarkdown li, .stMarkdown td {
                font-size: 1.1rem !important;
                line-height: 1.6 !important;
            }
            .stMarkdown table {
                font-size: 1.05rem !important;
                margin: 15px 0 !important;
            }
            .stMarkdown th {
                background-color: #1f1f1f !important;
                color: white !important;
                padding: 10px !important;
                font-weight: bold !important;
            }
            .stMarkdown td {
                padding: 8px !important;
                border: 1px solid #555 !important;
            }
            .stMarkdown h1, .stMarkdown h2 {
                color: #1f1f1f !important;
                font-size: 1.8rem !important;
                font-weight: bold !important;
                margin-top: 10px !important;
                margin-bottom: 10px !important;
                padding-bottom: 8px !important;
                border-bottom: 2px solid #1f1f1f !important;
            }
            .stMarkdown h3 {
                color: #e0e0e0 !important;
                font-size: 1.4rem !important;
                font-weight: bold !important;
                margin-top: 12px !important;
                margin-bottom: 8px !important;
            }
            .stMarkdown strong {
                color: #1f1f1f !important;
                font-weight: bold !important;
            }
            .stMarkdown ul, .stMarkdown ol {
                margin-left: 20px !important;
                margin-bottom: 15px !important;
            }
            .stMarkdown li {
                margin-bottom: 8px !important;
            }
        </style>
    """, unsafe_allow_html=True)


def render_accuracy_feedback(section_id, section_num, session_id, cpt_code):
    """
    Render accuracy feedback UI component
    
    Args:
        section_id: Section identifier (e.g., "section_1")
        section_num: Section number for display
        session_id: Current session ID
        cpt_code: CPT code being analyzed
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Accuracy buttons in one line
    col_label, col_yes, col_maybe, col_no = st.columns([0.6, 0.4, 0.5, 0.4])
    
    with col_label:
        st.markdown("<p style='color: #ffffff; font-size: 0.95rem; margin-top: 0.5rem; margin-bottom: 0; white-space: nowrap; font-weight: 500;'>Accurate?</p>", unsafe_allow_html=True)
    
    accuracy_key = f"{section_id}_accuracy"
    
    # Initialize feedback state key
    feedback_state_key = f"show_feedback_{section_id}"
    if feedback_state_key not in st.session_state:
        st.session_state[feedback_state_key] = False
    
    # Initialize section accuracy tracking
    if "section_accuracy" not in st.session_state:
        st.session_state.section_accuracy = {}
    
    with col_yes:
        if st.button("✅ Yes", key=f"{accuracy_key}_yes", use_container_width=True):
            st.session_state.section_accuracy[section_num] = "✅ Yes"
            st.session_state[feedback_state_key] = False
            save_accuracy_feedback(session_id, cpt_code, section_id, "✅ Yes", None)
            st.rerun()
            
    with col_maybe:
        if st.button("⚠️ Maybe", key=f"{accuracy_key}_maybe", use_container_width=True):
            st.session_state.section_accuracy[section_num] = "⚠️ Maybe"
            st.session_state[feedback_state_key] = True
            
    with col_no:
        if st.button("❌ No", key=f"{accuracy_key}_no", use_container_width=True):
            st.session_state.section_accuracy[section_num] = "❌ No"
            st.session_state[feedback_state_key] = True
    
    # Show reason input if Maybe or No was selected
    if st.session_state.get(feedback_state_key, False):
        current_rating = st.session_state.section_accuracy.get(section_num, '')
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #ffffff; font-size: 0.9rem; margin-bottom: 0.5rem;'>Please explain why you selected {current_rating}:</p>", unsafe_allow_html=True)
        reason_input = st.text_input(
            "Reason",
            key=f"reason_{section_id}",
            placeholder="Enter your reason here...",
            label_visibility="collapsed"
        )
        
        col_save, col_cancel = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save Feedback", key=f"save_feedback_{section_id}", use_container_width=True):
                if reason_input.strip():
                    save_accuracy_feedback(session_id, cpt_code, section_id, current_rating, reason_input)
                    st.session_state[feedback_state_key] = False
                    st.success("✅ Feedback saved!")
                    st.rerun()
                else:
                    st.warning("Please provide a reason.")
        
        with col_cancel:
            if st.button("✖️ Cancel", key=f"cancel_feedback_{section_id}", use_container_width=True):
                st.session_state[feedback_state_key] = False
                st.rerun()


def render_chat_interface(section_id, section_title, section_content, session_id, cpt_code, model, idx=0):
    """
    Render chat interface UI component
    
    Args:
        section_id: Section identifier
        section_title: Section title
        section_content: Section content for context
        session_id: Current session ID
        cpt_code: CPT code being analyzed
        model: Model to use for chat
        idx: Unique identifier for form keys
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize chat history for this section if not exists
    if "section_chat_history" not in st.session_state:
        st.session_state.section_chat_history = {}
        
    if section_id not in st.session_state.section_chat_history:
        # Load from database
        db_history = get_chat_history(session_id, cpt_code, section_id)
        st.session_state.section_chat_history[section_id] = db_history
    
    # Display chat history
    chat_history = st.session_state.section_chat_history.get(section_id, [])
    if chat_history:
        for i, chat in enumerate(chat_history):
            # User message bubble (black, aligned right)
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; margin: 0.5rem 0;'>
                <div style='background-color: #1f1f1f; color: white; padding: 1rem; border-radius: 1rem; max-width: 80%; text-align: left; white-space: pre-wrap;'>
            """, unsafe_allow_html=True)
            st.markdown(chat['user'])
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # AI response (no bubble, just regular markdown)
            st.markdown(chat['ai'])
            st.markdown("---")  # Separator between Q&A pairs
    
    # Chat input
    with st.form(key=f"chat_form_{section_id}_{idx}", clear_on_submit=True):
        user_question = st.text_area(
            "Your question:",
            placeholder="Ask anything about this section...",
            height=80,
            key=f"chat_input_{section_id}_{idx}"
        )
        submit_button = st.form_submit_button("Send 📤", use_container_width=True)
        
        if submit_button and user_question.strip():
            with st.spinner("🤔 Thinking..."):
                # Get AI response
                ai_response = chat_with_section(
                    section_content=section_title + "\n" + section_content,
                    cpt_code=cpt_code,
                    user_question=user_question,
                    chat_history=chat_history,
                    model=model
                )
                
                # Save to database
                save_chat_message(session_id, cpt_code, section_id, user_question, ai_response)
                
                # Update session state
                new_chat = {
                    "user": user_question,
                    "ai": ai_response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if section_id not in st.session_state.section_chat_history:
                    st.session_state.section_chat_history[section_id] = []
                st.session_state.section_chat_history[section_id].append(new_chat)
                
                # Rerun to display new message
                st.rerun()


def render_export_buttons(analysis_result, cpt_code, idx=0):
    """
    Render export buttons UI component
    
    Args:
        analysis_result: Complete analysis text
        cpt_code: CPT code
        idx: Unique identifier for button keys
    """
    st.markdown("---")
    st.subheader("💾 Export Options")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Excel download
        excel_file = final_assessment_service.create_excel_output(analysis_result, cpt_code)
        st.download_button(
            label="📊 Download as Excel",
            data=excel_file,
            file_name=f"apc_research_{cpt_code}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_download_{idx}"
        )
    
    with col_b:
        # PDF download
        pdf_file = final_assessment_service.create_pdf_output(analysis_result, cpt_code)
        st.download_button(
            label="📑 Download as PDF",
            data=pdf_file,
            file_name=f"apc_research_{cpt_code}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            key=f"pdf_download_{idx}"
        )
