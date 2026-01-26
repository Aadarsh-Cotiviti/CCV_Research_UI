"""
Code Description Analysis View (Section 1)

This module renders the UI for Section 1 - Code Description Analysis
Displays structured data from code_description_service.analyze_code_descriptions()
"""

import streamlit as st
from services.code_description_service import analyze_code_descriptions, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source


def format_structured_data(data):
    """
    Format structured data from code_description_service.analyze_code_descriptions()
    into markdown for display
    
    Args:
        data: Dict with keys: neighbouring_codes, internal_recoding_result, 
              internal_llm_recoding_result, external_full_llm_result
              
    Returns:
        Formatted markdown string
    """
    output = []
    
    # Add custom CSS for black headings
    output.append("""
    <style>
        .section-heading {
            color: #1f1f1f !important;
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .subsection-heading {
            color: #1f1f1f !important;
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 0.75rem;
            margin-bottom: 0.5rem;
        }
    </style>
    """)
    
    # Neighboring codes section
    if data.get('neighbouring_codes'):
        output.append('<h3 class="section-heading">🔍 Neighboring CPT Codes with Target CPT Code</h3>')
        output.append("")
        
        neighbouring_codes = data['neighbouring_codes']
        # Check if it's the new format (list of dicts) or old format (list of strings)
        if neighbouring_codes and isinstance(neighbouring_codes[0], dict):
            # New format with descriptions
            output.append(f"**Identified {len(neighbouring_codes)} related codes (in ascending order):**")
            output.append("")
            
            for code_info in sorted(neighbouring_codes, key=lambda x: x['cpt_code']):
                cpt_code = code_info['cpt_code']
                description = code_info.get('description', 'Description not available')
                source = code_info.get('source', 'unknown')
                
                # Format with source coloring
                formatted_desc = format_text_with_source(description, source)
                output.append(f"**CPT {cpt_code}**: {formatted_desc}")
                output.append("")
        else:
            # Old format (just code numbers)
            codes = sorted(neighbouring_codes)
            output.append(f"**Identified {len(codes)} related codes (in ascending order):**")
            output.append("")
            output.append(f"**{', '.join(codes)}**")
            output.append("")
        
        output.append("---")
        output.append("")
    
    # Knowledge base results (codes with change tracking info)
    if data.get('internal_recoding_result'):
        output.append('<h3 class="section-heading">📚 CPT Code Change Tracking</h3>')
        output.append("")
        output.append("**Codes with recent changes (from internal knowledge base):**")
        output.append("")
        
        for item in sorted(data['internal_recoding_result'], key=lambda x: x['cpt_code']):
            change_type = "📝 Code Changed" if item['change_type'] == 'C' else "✨ New Code"
            output.append(f'<h4 class="subsection-heading">CPT {item["cpt_code"]} ({change_type})</h4>')
            output.append("")
            
            # Description with source coloring (internal_kb)
            desc_text = format_text_with_source(item['cpt_description'], 'internal_kb')
            output.append(f"**Description:** {desc_text}")
            output.append("")
            
            # Change details with source coloring (internal_kb)
            change_text = format_text_with_source(item['cpt_change_description'], 'internal_kb')
            output.append(f"**Change Details:** {change_text}")
            output.append("")
            output.append("")  # Extra empty line after each CPT code
        
        output.append("---")
        output.append("")
    
    # Codes with no changes since 2024
    if data.get('no_change_results'):
        output.append('<h3 class="section-heading">📋 Codes Without Recent Changes</h3>')
        output.append("")
        
        for item in sorted(data['no_change_results'], key=lambda x: x['cpt_code']):
            status = item.get('status', 'No changes to CPT code descriptions since 2024.')
            output.append(f"**CPT {item['cpt_code']}:** {status}")
            output.append("")
        
        output.append("---")
        output.append("")
    
    if not output:
        return "⚠️ No analysis results found"
    
    return "\n".join(output)


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Section 1 view with structured data from code_description_service
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use for analysis
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## SECTION 1 - Code Description Analysis")
    st.markdown("---")
    
    # Initialize session state for this section's results
    section_key = f"section_1_results_{cpt_code}"
    if section_key not in st.session_state:
        # Try to auto-load cache on first visit
        cached_data = load_cached_results(cpt_code)
        st.session_state[section_key] = cached_data  # Will be None if no cache exists
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        load_cache_btn = st.button("📦 Load Cache", key=f"load_cache_btn_{idx}", use_container_width=True)
    
    with col2:
        regenerate_btn = st.button("🔄 Re-generate Analysis", key=f"regenerate_btn_{idx}", use_container_width=True)
    
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
            fresh_data = analyze_code_descriptions(cpt_code, model=model, use_cache=False)
            st.session_state[section_key] = fresh_data
            st.success("✅ Analysis completed and saved!")
            st.rerun()
    
    # Display results
    display_data = st.session_state[section_key]
    
    if display_data:
        # Show source legend
        render_source_legend()
        
        formatted_content = format_structured_data(display_data)
        st.markdown(formatted_content, unsafe_allow_html=True)
        content_for_chat = formatted_content
    else:
        st.warning("⚠️ No results available. Please load cache or run analysis.")
        content_for_chat = ""
    
    # Chat Interface
    st.markdown("---")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="section_1",
        section_num="1",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    # Chat interface
    render_chat_interface(
        section_id="section_1",
        section_title="Code Description Analysis",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
