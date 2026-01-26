"""
Device Code Analysis View (Section 4)

This module renders the UI for Section 4 - Device Code Analysis
Displays structured data from device_code_service.analyze_device_code_analysis()
"""

import streamlit as st
from services.device_code_service import analyze_device_code_analysis, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source


def format_structured_data(data):
    """
    Format structured data from device_code_service.analyze_device_code_analysis()
    into markdown for display
    
    Args:
        data: Dict with keys: device_codes_with_desc, internal_recoding_result, 
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
    
    # Device codes with descriptions section
    if data.get('device_codes_with_desc'):
        output.append('<h3 class="section-heading">🔍 Identified HCPCS Device Codes</h3>')
        output.append("")
        
        device_codes = data['device_codes_with_desc']
        output.append(f"**Found {len(device_codes)} device code(s) related to this procedure:**")
        output.append("")
        
        for code_info in sorted(device_codes, key=lambda x: x.get('hcpcs_code', '')):
            hcpcs_code = code_info.get('hcpcs_code', 'Unknown')
            description = code_info.get('description', 'Description not available')
            source = code_info.get('source', 'unknown')
            
            # Format with source coloring
            formatted_desc = format_text_with_source(description, source)
            output.append(f"**HCPCS {hcpcs_code}**: {formatted_desc}")
            output.append("")
        
        output.append("---")
        output.append("")
    
    # Knowledge base results (device codes with change tracking info)
    if data.get('internal_recoding_result'):
        output.append('<h3 class="section-heading">📚 Device Code Change Tracking</h3>')
        output.append("")
        output.append("**Device codes with recent changes (from internal knowledge base):**")
        output.append("")
        
        for item in sorted(data['internal_recoding_result'], key=lambda x: x.get('hcpcs_code', '')):
            change_type_map = {
                'C': '📝 Code Changed',
                'N': '✨ New Code',
                'R': '🔄 Reinstated',
                'D': '🗑️ Deleted'
            }
            change_type = change_type_map.get(item.get('change_type', ''), '📋 Changed')
            
            output.append(f'<h4 class="subsection-heading">HCPCS {item.get("hcpcs_code", "Unknown")} ({change_type})</h4>')
            output.append("")
            
            # Description with source coloring (internal_kb)
            desc_text = format_text_with_source(item.get('hcpcs_description', 'No description'), 'internal_kb')
            output.append(f"**Description:** {desc_text}")
            output.append("")
            
            # Change details with source coloring (internal_kb)
            change_text = format_text_with_source(item.get('change_description', 'No change details'), 'internal_kb')
            output.append(f"**Change Details:** {change_text}")
            output.append("")
            output.append("")  # Extra empty line after each device code
        
        output.append("---")
        output.append("")
    
    # Device codes with no changes since 2024
    if data.get('no_change_results'):
        output.append('<h3 class="section-heading">📋 Device Codes Without Recent Changes</h3>')
        output.append("")
        
        for item in sorted(data['no_change_results'], key=lambda x: x.get('hcpcs_code', '')):
            status = item.get('status', 'No changes to device code descriptions since 2024.')
            output.append(f"**HCPCS {item.get('hcpcs_code', 'Unknown')}:** {status}")
            output.append("")
        
        output.append("---")
        output.append("")
    
    # If no device codes found at all - check all result categories
    # Note: Empty lists [] evaluate to False, so we need to check explicitly
    has_any_results = bool(
        (data.get('device_codes_with_desc') and len(data.get('device_codes_with_desc', [])) > 0) or 
        (data.get('internal_recoding_result') and len(data.get('internal_recoding_result', [])) > 0) or 
        (data.get('no_change_results') and len(data.get('no_change_results', [])) > 0)
    )
    
    if not has_any_results:
        output.append('<h3 class="section-heading">ℹ️ No Device Codes Identified</h3>')
        output.append("")
        output.append("**Analysis Result:** This CPT procedure does not involve separately billable medical device codes (HCPCS).")
        output.append("")
        output.append("**Implication:** No device codes need to be reviewed or validated for this procedure. This is a normal result for procedures that:")
        output.append("- Do not require medical implants or devices")
        output.append("- Use only standard disposable supplies included in the procedure payment")
        output.append("- Are primarily therapeutic services (e.g., acupuncture, physical therapy)")
        output.append("")
    
    if not output or len(output) <= 1:  # Only CSS, no real content
        return "⚠️ No analysis results found"
    
    return "\n".join(output)


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Section 4 view with structured data from device_code_service
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use for analysis
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## SECTION 4 - Device Code Analysis")
    st.markdown("---")
    
    # Initialize session state for this section's results
    section_key = f"section_4_results_{cpt_code}"
    if section_key not in st.session_state:
        # Try to auto-load cache on first visit
        cached_data = load_cached_results(cpt_code)
        st.session_state[section_key] = cached_data  # Will be None if no cache exists
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        load_cache_btn = st.button("📦 Load Cache", key=f"load_cache_btn_sec4_{idx}", use_container_width=True)
    
    with col2:
        regenerate_btn = st.button("🔄 Re-generate Analysis", key=f"regenerate_btn_sec4_{idx}", use_container_width=True)
    
    # Handle Load Cache button
    if load_cache_btn:
        with st.spinner("Loading cached results..."):
            cached_data = load_cached_results(cpt_code)
            if cached_data:
                st.session_state[section_key] = cached_data
                # Force display to show the update
                st.success(f"✅ Successfully loaded cached results! Found {len(cached_data.get('device_codes_with_desc', []))} device codes.")
                st.rerun()
            else:
                st.warning("⚠️ No cached results found. Please run analysis first.")
    
    # Handle Re-generate button
    if regenerate_btn:
        with st.spinner("Running fresh device code analysis..."):
            try:
                # Run analysis without manually providing device_codes (let LLM identify them)
                fresh_data = analyze_device_code_analysis(cpt_code, device_codes=None, model=model, use_cache=False)
                st.session_state[section_key] = fresh_data
                st.success("✅ Analysis completed and saved!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
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
    

    # Accuracy feedback
    render_accuracy_feedback(
        section_id="section_4",
        section_num="4",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    # Chat interface
    render_chat_interface(
        section_id="section_4",
        section_title="Device Code Analysis",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
