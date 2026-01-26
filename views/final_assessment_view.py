"""
Final Assessment View

This module renders the UI for Final Assessment section
"""

import streamlit as st
from .utils import render_accuracy_feedback, render_chat_interface


def render_section(cpt_code, session_id):
    """
    Render Final Assessment view
    
    Args:
        cpt_code: Target CPT code
        session_id: Current session ID
    """
    # Title
    st.markdown("## FINAL ASSESSMENT")
    st.markdown("---")
    
    st.info("⏳ Final assessment will be generated after all sections are completed.")
    
    # Chat Interface
    st.markdown("---")
    st.subheader("💬 Ask Questions About The Full Research")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="final_assessment",
        section_num="final",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    # Chat interface (with full research context)
    render_chat_interface(
        section_id="final_assessment",
        section_title="FINAL ASSESSMENT",
        section_content="",  # Empty for now until sections are complete
        session_id=session_id,
        cpt_code=cpt_code,
        model="gpt-4.1-mini",
        idx=999  # Unique index for final assessment
    )

