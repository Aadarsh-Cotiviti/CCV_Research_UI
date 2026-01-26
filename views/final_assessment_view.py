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
    
    # 3. Payment History (from Section 3) - APC, ASC, and PNPP
    output.append("**💰 Payment Rate History:**")
    output.append("")
    
    has_payment_data = False
    
    # Check if payment_data is a dict (new format) or handle gracefully
    if not payment_data or not isinstance(payment_data, dict):
        output.append("  - No payment data available")
        output.append("")
        output.append("---")
        output.append("")
        return "\n".join(output)
    
    # Check APC payment data
    if payment_data.get('apc') and payment_data['apc'].get('has_data'):
        apc_data = payment_data['apc']['data']
        if apc_data and len(apc_data) > 0:
            df_apc = pd.DataFrame(apc_data)
            if 'HCPCS Code' in df_apc.columns:
                code_df = df_apc[df_apc['HCPCS Code'] == cpt_code]
                
                if len(code_df) > 0:
                    years = sorted(code_df['Year'].unique())
                    latest_year = years[-1] if years else 'N/A'
                    latest_row = code_df[code_df['Year'] == latest_year].iloc[0]
                    latest_rate = latest_row.get('Payment Rate', 'N/A')
                    latest_apc = latest_row.get('APC Code', 'N/A')  # Changed from 'APC' to 'APC Code'
                    if latest_apc != 'N/A':
                        try:
                            latest_apc = int(float(latest_apc))
                        except (ValueError, TypeError):
                            pass
                    output.append(f"  - **APC**: {len(years)} years of data available (Latest: {latest_year}, \${latest_rate}, APC {latest_apc})")
                    has_payment_data = True
    
    # Check ASC payment data
    if payment_data.get('asc') and payment_data['asc'].get('has_data'):
        asc_data = payment_data['asc']['data']
        if asc_data and len(asc_data) > 0:
            df_asc = pd.DataFrame(asc_data)
            if 'HCPCS Code' in df_asc.columns:
                code_df = df_asc[df_asc['HCPCS Code'] == cpt_code]
                
                if len(code_df) > 0:
                    years = sorted(code_df['Year'].unique())
                    latest_year = years[-1] if years else 'N/A'
                    latest_row = code_df[code_df['Year'] == latest_year].iloc[0]
                    latest_rate = latest_row.get('Payment Rate', 'N/A')
                    output.append(f"  - **ASC**: {len(years)} years of data available (Latest: {latest_year}, \${latest_rate})")
                    has_payment_data = True
    
    # Check PNPP payment data
    if payment_data.get('pnpp') and payment_data['pnpp'].get('has_data'):
        pnpp_data = payment_data['pnpp']['data']
        if pnpp_data and len(pnpp_data) > 0:
            df_pnpp = pd.DataFrame(pnpp_data)
            if 'HCPCS' in df_pnpp.columns:
                code_df = df_pnpp[df_pnpp['HCPCS'] == cpt_code]
                
                if len(code_df) > 0:
                    years = sorted(code_df['Year'].unique())
                    latest_year = years[-1] if years else 'N/A'
                    latest_row = code_df[code_df['Year'] == latest_year].iloc[0]
                    non_facility_rate = latest_row.get('Non-Facility Payment Rate', 'N/A')
                    facility_rate = latest_row.get('Facility Payment Rate', 'N/A')
                    # Format rates to 2 decimal places
                    if non_facility_rate != 'N/A':
                        try:
                            non_facility_rate = f"{float(non_facility_rate):.2f}"
                        except (ValueError, TypeError):
                            pass
                    if facility_rate != 'N/A':
                        try:
                            facility_rate = f"{float(facility_rate):.2f}"
                        except (ValueError, TypeError):
                            pass
                    output.append(f"  - **PNPP**: {len(years)} years of data available (Latest: {latest_year}, Non-Facility: \${non_facility_rate}, Facility: \${facility_rate})")
                    has_payment_data = True
    
    if not has_payment_data:
        output.append("  - No payment data available")
    
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
        generate_btn = st.button("🔄 Generate Assessment", key=f"generate_final_assessment_{idx}", type="primary")
    
    # Handle button click
    if generate_btn:
        with st.spinner("🔄 Consolidating results from all sections..."):
            try:
                # Generate final assessment
                assessment = generate_final_assessment(target_cpt=cpt_code, use_cache=False)
                
                if assessment:
                    # Store in session state for display
                    st.session_state[assessment_key] = assessment
                    st.success("✅ Final assessment generated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate final assessment. Please ensure all sections 1-6 have been completed.")
                    
            except Exception as e:
                st.error(f"❌ Error generating final assessment: {str(e)}")
    
    # Display results if available
    assessment_data = st.session_state.get(assessment_key)
    
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
                # Pass entire payment_history dict with apc, asc, pnpp keys
                
                formatted_section = format_cpt_code_section(
                    code, 
                    code_data, 
                    ncci_data, 
                    payment_history
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
