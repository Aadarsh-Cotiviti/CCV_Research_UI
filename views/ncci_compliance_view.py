"""
NCCI Compliance Check View (Section 5)

This module renders the UI for Section 5 - NCCI Compliance Check
"""

import streamlit as st
from .utils import render_accuracy_feedback, render_chat_interface


def render_section(cpt_code, model, session_id, idx=0):
    """Render Section 5 view"""
    st.markdown("## SECTION 5 - NCCI Compliance Check")
    st.markdown("---")
    
    st.info("⏳ This section has not been analyzed yet. Cache/regenerate functionality coming soon.")
    content_for_chat = ""
    
    st.markdown("---")
    
    render_accuracy_feedback(
        section_id="section_5",
        section_num="5",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    render_chat_interface(
        section_id="section_5",
        section_title="NCCI Compliance Check",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
