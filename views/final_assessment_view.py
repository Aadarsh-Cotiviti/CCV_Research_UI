"""
Final Assessment View

This module renders the UI for Final Assessment section
Consolidates key findings from Sections 1-6
"""

import streamlit as st
import pandas as pd
from services.final_assessment_service import generate_final_assessment
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source


def format_cpt_code_section(cpt_code, code_data, ncci_data, payment_data):
    """
    Format display for a single CPT code with all its associated data
    
    Args:
        cpt_code: CPT code string
        code_data: Dict with description and source
        ncci_data: Dict with NCCI results
        payment_data: List of payment records for this code
        
    Returns:
        Formatted markdown string
    """
    output = []
    
    # CPT Code Header
    output.append(f'<h4 style="color: #1f1f1f; margin-top: 1rem;">CPT {cpt_code}</h4>')
    output.append("")
    
    # 1. Description (from Section 1)
    if code_data:
        description = code_data.get('description', 'Description not available')
        source = code_data.get('source', 'unknown')
        formatted_desc = format_text_with_source(description, source)
        output.append(f"**📝 Description:** {formatted_desc}")
        output.append("")
    
    # 2. NCCI Results (from Section 5)
    if ncci_data and ncci_data.get('has_ncci_data'):
        output.append("**🔍 NCCI Compliance:**")
        output.append("")
        
        # PTP Modifier 0
        if ncci_data.get('ptp_modifier_0'):
            mod0 = ncci_data['ptp_modifier_0']
            count = mod0.get('record_count', 0)
            output.append(f"- **PTP Edits (Modifier 0):** {count} edits found")
            output.append("")
            
            # Show ALL edits
            if mod0.get('data') and len(mod0['data']) > 0:
                for edit in mod0['data']:
                    code2 = edit.get('CPT_code_2', 'N/A')
                    rationale = edit.get('PTP_Edit_Rationale', 'N/A')
                    output.append(f"  - {cpt_code} + {code2}: {rationale}")
            output.append("")
        
        # PTP Modifier 1
        if ncci_data.get('ptp_modifier_1'):
            mod1 = ncci_data['ptp_modifier_1']
            count = mod1.get('record_count', 0)
            output.append(f"- **PTP Edits (Modifier 1):** {count} edits found")
            output.append("")
            
            # Show ALL edits
            if mod1.get('data') and len(mod1['data']) > 0:
                for edit in mod1['data']:
                    code2 = edit.get('CPT_code_2', 'N/A')
                    rationale = edit.get('PTP_Edit_Rationale', 'N/A')
                    output.append(f"  - {cpt_code} + {code2}: {rationale}")
            output.append("")
        
        # NCCI Manual Summary
        if ncci_data.get('ncci_manual_summary'):
            output.append("- **NCCI Manual Findings:**")
            summary = ncci_data['ncci_manual_summary']
            output.append(f"  {summary}")
            output.append("")
    else:
        output.append("**🔍 NCCI Compliance:** No NCCI edits found")
        output.append("")
    
    # 3. Payment History (from Section 3)
    if payment_data and len(payment_data) > 0:
        output.append("**💰 Payment Rate History:**")
        output.append("")
        
        # Create payment table
        df = pd.DataFrame(payment_data)
        # Filter for this specific code
        code_df = df[df['HCPCS Code'] == cpt_code]
        
        if len(code_df) > 0:
            # Format as table
            payment_table = []
            for _, row in code_df.iterrows():
                year = row.get('Year', 'N/A')
                rate = row.get('Payment Rate', 'N/A')
                apc = row.get('APC', 'N/A')
                # Convert APC to int if it's a number
                if apc != 'N/A':
                    try:
                        apc = int(float(apc))
                    except (ValueError, TypeError):
                        pass
                payment_table.append(f"  - **{year}**: ${rate} (APC {apc})")
            
            output.extend(payment_table)
            output.append("")
        else:
            output.append("  - No payment history available for this code")
            output.append("")
    else:
        output.append("**💰 Payment Rate History:** No payment data available")
        output.append("")
    
    output.append("---")
    output.append("")
    
    return "\n".join(output)


def format_device_codes_section(device_codes):
    """
    Format device codes section
    
    Args:
        device_codes: List of device code dicts
        
    Returns:
        Formatted markdown string
    """
    if not device_codes or len(device_codes) == 0:
        return "**No device codes found**\n"
    
    output = []
    output.append(f"**Found {len(device_codes)} related device codes:**")
    output.append("")
    
    for device in device_codes:
        hcpcs = device.get('hcpcs_code', 'N/A')
        description = device.get('description', 'Description not available')
        source = device.get('source', 'unknown')
        
        formatted_desc = format_text_with_source(description, source)
        output.append(f"**{hcpcs}**: {formatted_desc}")
        output.append("")
    
    return "\n".join(output)


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Final Assessment view with consolidated data
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## 📊 FINAL ASSESSMENT")
    st.markdown("---")
    
    # Source legend
    render_source_legend()
    
    # Auto-load on first visit
    assessment_key = f'final_assessment_data_{idx}'
    if assessment_key not in st.session_state:
        # Try to load cached assessment
        cached_assessment = generate_final_assessment(target_cpt=cpt_code, use_cache=True)
        st.session_state[assessment_key] = cached_assessment
    
    # Generate button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Consolidated Summary")
        st.markdown("This section consolidates key findings from all previous sections (1-6)")
    
    with col2:
        if st.button("🔄 Generate Assessment", key=f"generate_final_assessment_{idx}", type="primary"):
            st.session_state[f'final_assessment_trigger_{idx}'] = True
    
    # Check if we should run the analysis
    should_run = st.session_state.get(f'final_assessment_trigger_{idx}', False)
    
    if should_run:
        # Clear trigger
        st.session_state[f'final_assessment_trigger_{idx}'] = False
        
        with st.spinner("🔄 Consolidating results from all sections..."):
            try:
                # Generate final assessment
                assessment = generate_final_assessment(target_cpt=cpt_code, use_cache=True)
                
                if assessment:
                    st.success("✅ Final assessment generated successfully!")
                    
                    # Store in session state for display
                    st.session_state[f'final_assessment_data_{idx}'] = assessment
                else:
                    st.error("❌ Failed to generate final assessment. Please ensure all sections 1-6 have been completed.")
                    return
                    
            except Exception as e:
                st.error(f"❌ Error generating final assessment: {str(e)}")
                return
    
    # Display results if available
    assessment_data = st.session_state.get(f'final_assessment_data_{idx}')
    
    if assessment_data:
        # Extract data
        cpt_descriptions = assessment_data.get('cpt_descriptions', {})
        ncci_results = assessment_data.get('ncci_results', {})
        device_codes = assessment_data.get('device_codes', [])
        payment_history = assessment_data.get('payment_history', {})
        
        # Display timestamp
        update_time = assessment_data.get('update_time', 'Unknown')
        st.caption(f"📅 Generated: {update_time}")
        
        st.markdown("---")
        
        # Display CPT Codes Analysis (no tabs)
        st.markdown("### 📋 Target CPT and Neighboring Codes")
        st.markdown("")
        
        if cpt_descriptions:
            # Get all CPT codes sorted
            all_cpt_codes = sorted(cpt_descriptions.keys())
            
            # Display each CPT code with its associated data
            for code in all_cpt_codes:
                code_data = cpt_descriptions.get(code)
                ncci_data = ncci_results.get(code)
                payment_data = payment_history.get('data', [])
                
                formatted_section = format_cpt_code_section(
                    code, 
                    code_data, 
                    ncci_data, 
                    payment_data
                )
                
                st.markdown(formatted_section, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No CPT code data available. Please run Section 1 first.")
        
        st.markdown("---")
        st.markdown("---")  # Extra separator before device codes
        
        # Display Device Codes at the bottom
        st.markdown("### 🔧 Related Device Codes")
        st.markdown("")
        
        if device_codes:
            formatted_devices = format_device_codes_section(device_codes)
            st.markdown(formatted_devices, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No device code data available. Please run Section 4 first.")
        
        st.markdown("---")
        
        # Export options
        st.markdown("### 📥 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export to Excel", key=f"export_excel_{idx}"):
                st.info("📊 Excel export functionality coming soon")
        
        with col2:
            if st.button("📄 Export to PDF", key=f"export_pdf_{idx}"):
                st.info("📄 PDF export functionality coming soon")
    
    else:
        st.info("⏳ Click 'Generate Assessment' to consolidate findings from all sections")
    
    # Chat Interface
    st.markdown("---")
    st.subheader("💬 Ask Questions About The Final Assessment")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="final_assessment",
        section_num="final",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    # Get formatted content for chat context
    section_content = ""
    if assessment_data:
        section_content = str(assessment_data)  # Simple string representation for now
    
    # Chat interface
    render_chat_interface(
        section_id="final_assessment",
        section_title="FINAL ASSESSMENT",
        section_content=section_content,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
