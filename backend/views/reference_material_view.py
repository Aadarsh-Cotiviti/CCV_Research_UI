"""
Reference Material Review View (Section 6)

This module renders the UI for Section 6 - Reference Material Review
"""

import streamlit as st
from services.reference_material_service import analyze_reference_material_review, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source


def format_reference_material_data(data):
    """
    Format reference material data into markdown for display
    
    Args:
        data: Dict with keys: analysis_content, cpt_descriptions
        
    Returns:
        Formatted markdown string
    """
    output = []
    
    # Add the analysis content first
    analysis_content = data.get("analysis_content", "")
    if analysis_content:
        output.append(analysis_content)
        output.append("")
        output.append("---")
        output.append("")
    
    # Display CPT code descriptions at the bottom as references
    cpt_descriptions = data.get("cpt_descriptions", {})
    if cpt_descriptions:
        output.append("### 📋 CPT Codes Referenced")
        output.append("")
        
        for cpt_code in sorted(cpt_descriptions.keys()):
            desc_info = cpt_descriptions[cpt_code]
            description = desc_info.get('description', 'No description available')
            source = desc_info.get('source', 'llm')
            
            # Format with source coloring
            formatted_desc = format_text_with_source(description, source)
            output.append(f"**CPT {cpt_code}**: {formatted_desc}")
            output.append("")
    
    return "\n".join(output)


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Section 6 view with reference material review analysis
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use for analysis
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## SECTION 6 - Reference Material Review")
    st.markdown("---")
    
    # Initialize session state for this section's results
    section_key = f"section_6_results_{cpt_code}"
    if section_key not in st.session_state:
        # Try to auto-load cache on first visit
        cached_data = load_cached_results(cpt_code)
        st.session_state[section_key] = cached_data  # Will be None if no cache exists
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        load_cache_btn = st.button("📦 Load Cache", key=f"load_cache_btn_s6_{idx}", use_container_width=True)
    
    with col2:
        regenerate_btn = st.button("🔄 Re-generate Analysis", key=f"regenerate_btn_s6_{idx}", use_container_width=True)
    
    # Handle Load Cache button
    if load_cache_btn:
        with st.spinner("Loading cached results..."):
            cached_data = load_cached_results(cpt_code)
            if cached_data:
                st.session_state[section_key] = cached_data
                st.success("✅ Successfully loaded cached results!")
                st.rerun()
            else:
                st.warning("⚠️ No cached results found. Please run analysis first.")
    
    # Handle Re-generate button
    if regenerate_btn:
        with st.spinner("Running fresh analysis..."):
            fresh_data = analyze_reference_material_review(cpt_code, model=model, use_cache=False)
            st.session_state[section_key] = fresh_data
            st.success("✅ Analysis completed and saved!")
            st.rerun()
    
    # Display results
    display_data = st.session_state[section_key]
    
    if display_data and display_data.get("analysis_content"):
        # Show source legend
        render_source_legend()
        
        # Important notice
        st.info("**Note:** Reference materials including CPT Assistant and coding guidance are proprietary resources. All content in this section is LLM-generated and should be verified against official sources.")
        
        # Format and display all content together
        formatted_content = format_reference_material_data(display_data)
        st.markdown(formatted_content, unsafe_allow_html=True)
        content_for_chat = formatted_content
    else:
        st.warning("⚠️ No results available. Please load cache or run analysis.")
        content_for_chat = ""
    
    # Chat Interface
    st.markdown("---")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="section_6",
        section_num="6",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    # Chat interface
    render_chat_interface(
        section_id="section_6",
        section_title="Reference Material Review",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
