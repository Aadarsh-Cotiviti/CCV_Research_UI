"""
Payment Rate Comparison View (Section 3)

This module renders the UI for Section 3 - Payment Rate Comparison
"""

import streamlit as st
import pandas as pd
from services.payment_rate_service import analyze_payment_rate_comparison, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source


def render_cpt_code_reference(cpt_descriptions):
    """Render CPT Code Reference with all codes from payment tables"""
    if not cpt_descriptions or len(cpt_descriptions) == 0:
        return
    
    st.markdown("---")
    st.markdown("## 📖 CPT Codes Referenced")
    
    # Display codes with descriptions using format_text_with_source for proper color coding
    for cpt_code, desc_info in sorted(cpt_descriptions.items()):
        description = desc_info.get('description', 'N/A')
        source = desc_info.get('source', 'llm')
        
        # Format the entire line with source coloring
        formatted_line = f"**{cpt_code}**: {description}"
        colored_text = format_text_with_source(formatted_line, source)
        st.markdown(f"- {colored_text}", unsafe_allow_html=True)


def render_payment_table_apc(payment_data):
    """Render APC payment history table"""
    if not payment_data or payment_data.get("data_filtered") is None:
        st.warning("No APC payment history data available")
        return
    
    df = pd.DataFrame(payment_data["data_filtered"])
    if df.empty:
        st.warning("No APC payment records found")
        return
    
    # Clean APC Code column
    if 'APC' in df.columns and 'APC Code' not in df.columns:
        df.rename(columns={'APC': 'APC Code'}, inplace=True)
    if 'APC Code' in df.columns:
        df['APC Code'] = pd.to_numeric(df['APC Code'], errors='coerce').fillna(0).astype(int).astype(str)
    
    # Display columns
    display_columns = ['HCPCS Code', 'Year', 'SI', 'APC Code', 'Payment Rate']
    df_display = df[display_columns].copy()
    
    # Get exclusions info
    exclusions = payment_data.get("exclusions", {})
    excluded_count = len(exclusions)
    filtered_count = payment_data.get("record_count_filtered", len(df))
    
    # Display table
    if excluded_count > 0:
        st.markdown(f"### 📊 APC Payment History Table (Excluded codes removed)")
        st.info(f"ℹ️ Showing {filtered_count} records. {excluded_count} code(s) excluded from APC payment (see below).")
    else:
        st.markdown(f"### 📊 APC Payment History Table")
    
    def style_green(val):
        return 'color: #2e7d32'
    
    styled_df = df_display.style.applymap(style_green)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "HCPCS Code": st.column_config.TextColumn("CPT Code", width="small"),
            "Year": st.column_config.TextColumn("Year", width="small"),
            "SI": st.column_config.TextColumn("SI", width="small"),
            "APC Code": st.column_config.TextColumn("APC Code", width="small"),
            "Payment Rate": st.column_config.NumberColumn("Payment Rate", format="$%.2f"),
        }
    )
    
    st.caption("📅 Payment data represents January rates for each year (2024-2026)")
    
    # Display exclusions
    if exclusions and excluded_count > 0:
        st.markdown("#### ⚠️ CMS APC Excluded Codes")
        st.warning(f"**{excluded_count} code(s) excluded** - Not eligible for APC payment")
        
        exclusions_data = []
        for cpt, info in exclusions.items():
            exclusions_data.append({
                "CPT Code": cpt,
                "Status Indicator": info['status_indicator']
            })
        
        exclusions_df = pd.DataFrame(exclusions_data).sort_values('CPT Code')
        
        def style_red(val):
            return 'color: #d32f2f; font-weight: bold'
        
        styled_exclusions = exclusions_df.style.applymap(style_red, subset=['CPT Code', 'Status Indicator'])
        
        st.dataframe(
            styled_exclusions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CPT Code": st.column_config.TextColumn("CPT Code", width="small"),
                "Status Indicator": st.column_config.TextColumn("SI", width="small")
            }
        )


def render_payment_table_asc(payment_data):
    """Render ASC payment history table"""
    if not payment_data or payment_data.get("data_filtered") is None:
        st.warning("No ASC payment history data available")
        return
    
    df = pd.DataFrame(payment_data["data_filtered"])
    if df.empty:
        st.warning("No ASC payment records found")
        return
    
    # Check available columns
    available_cols = df.columns.tolist()
    
    # Build display columns based on what's available
    display_columns = []
    if 'HCPCS Code' in available_cols:
        display_columns.append('HCPCS Code')
    if 'Year' in available_cols:
        display_columns.append('Year')
    if 'Payment Indicator' in available_cols:
        display_columns.append('Payment Indicator')
    if 'Payment Rate' in available_cols:
        display_columns.append('Payment Rate')
    
    if not display_columns:
        st.error(f"Required columns not found. Available columns: {available_cols}")
        return
    
    df_display = df[display_columns].copy()
    
    # Get exclusions info
    exclusions = payment_data.get("exclusions", {})
    excluded_count = len(exclusions)
    filtered_count = payment_data.get("record_count_filtered", len(df))
    
    # Display table
    if excluded_count > 0:
        st.markdown(f"### 📊 ASC Payment History Table (Excluded codes removed)")
        st.info(f"ℹ️ Showing {filtered_count} records. {excluded_count} code(s) excluded from ASC payment (see below).")
    else:
        st.markdown(f"### 📊 ASC Payment History Table")
    
    def style_green(val):
        return 'color: #2e7d32'
    
    styled_df = df_display.style.applymap(style_green)
    
    # Build column config dynamically
    column_config = {}
    if 'HCPCS Code' in display_columns:
        column_config['HCPCS Code'] = st.column_config.TextColumn("CPT Code", width="small")
    if 'Year' in display_columns:
        column_config['Year'] = st.column_config.TextColumn("Year", width="small")
    if 'Payment Indicator' in display_columns:
        column_config['Payment Indicator'] = st.column_config.TextColumn("Payment Indicator", width="small")
    if 'Payment Rate' in display_columns:
        column_config['Payment Rate'] = st.column_config.NumberColumn("Payment Rate", format="$%.2f")
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
    st.caption("📅 Payment data represents January rates for each year (2024-2026)")
    
    # Display exclusions
    if exclusions and excluded_count > 0:
        st.markdown("#### ⚠️ CMS ASC Excluded Codes")
        st.warning(f"**{excluded_count} code(s) excluded** - Not eligible for ASC payment")
        
        exclusions_data = []
        for cpt, info in exclusions.items():
            exclusions_data.append({
                "CPT Code": cpt,
                "Payment Indicator": info['status_indicator']
            })
        
        exclusions_df = pd.DataFrame(exclusions_data).sort_values('CPT Code')
        
        def style_red(val):
            return 'color: #d32f2f; font-weight: bold'
        
        styled_exclusions = exclusions_df.style.applymap(style_red, subset=['CPT Code', 'Payment Indicator'])
        
        st.dataframe(
            styled_exclusions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CPT Code": st.column_config.TextColumn("CPT Code", width="small"),
                "Payment Indicator": st.column_config.TextColumn("Payment Indicator", width="small")
            }
        )


def render_payment_table_pnpp(payment_data):
    """Render PNPP payment history table"""
    if not payment_data or payment_data.get("data_filtered") is None:
        st.warning("No PNPP payment history data available")
        return
    
    df = pd.DataFrame(payment_data["data_filtered"])
    if df.empty:
        st.warning("No PNPP payment records found")
        return
    
    # Check which columns are available and handle different column names
    available_cols = df.columns.tolist()
    
    # Build display columns based on what's available
    display_columns = []
    col_mapping = {}
    
    # HCPCS column (could be 'HCPCS' or 'HCPCS Code')
    if 'HCPCS' in available_cols:
        display_columns.append('HCPCS')
        col_mapping['CPT Code'] = 'HCPCS'
    elif 'HCPCS Code' in available_cols:
        display_columns.append('HCPCS Code')
        col_mapping['CPT Code'] = 'HCPCS Code'
    
    # Add other required columns if they exist
    if 'Year' in available_cols:
        display_columns.append('Year')
    if 'STATUS CODE' in available_cols:
        display_columns.append('STATUS CODE')
    if 'Non-Facility Payment Rate' in available_cols:
        display_columns.append('Non-Facility Payment Rate')
    if 'Facility Payment Rate' in available_cols:
        display_columns.append('Facility Payment Rate')
    
    if not display_columns:
        st.error(f"Required columns not found. Available columns: {available_cols}")
        return
    
    df_display = df[display_columns].copy()
    
    # Get exclusions info
    exclusions = payment_data.get("exclusions", {})
    excluded_count = len(exclusions)
    filtered_count = payment_data.get("record_count_filtered", len(df))
    
    # Display table
    if excluded_count > 0:
        st.markdown(f"### 📊 PNPP Payment History Table (Excluded codes removed)")
        st.info(f"ℹ️ Showing {filtered_count} records. {excluded_count} code(s) excluded from PNPP payment (see below).")
    else:
        st.markdown(f"### 📊 PNPP Payment History Table")
    
    def style_green(val):
        return 'color: #2e7d32'
    
    styled_df = df_display.style.applymap(style_green)
    
    # Build column config dynamically
    column_config = {}
    if 'HCPCS' in display_columns:
        column_config['HCPCS'] = st.column_config.TextColumn("CPT Code", width="small")
    elif 'HCPCS Code' in display_columns:
        column_config['HCPCS Code'] = st.column_config.TextColumn("CPT Code", width="small")
    
    if 'Year' in display_columns:
        column_config['Year'] = st.column_config.TextColumn("Year", width="small")
    if 'STATUS CODE' in display_columns:
        column_config['STATUS CODE'] = st.column_config.TextColumn("Status Code", width="small")
    if 'Non-Facility Payment Rate' in display_columns:
        column_config['Non-Facility Payment Rate'] = st.column_config.NumberColumn("Non-Facility Rate", format="$%.2f")
    if 'Facility Payment Rate' in display_columns:
        column_config['Facility Payment Rate'] = st.column_config.NumberColumn("Facility Rate", format="$%.2f")
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
    st.caption("📅 Payment data represents January rates for each year (2024-2026)")
    
    # Display exclusions
    if exclusions and excluded_count > 0:
        st.markdown("#### ⚠️ CMS PNPP Excluded Codes")
        st.warning(f"**{excluded_count} code(s) excluded** - Not eligible for PNPP payment")
        
        exclusions_data = []
        for cpt, info in exclusions.items():
            exclusions_data.append({
                "CPT Code": cpt,
                "Status Code": info['status_indicator']
            })
        
        exclusions_df = pd.DataFrame(exclusions_data).sort_values('CPT Code')
        
        def style_red(val):
            return 'color: #d32f2f; font-weight: bold'
        
        styled_exclusions = exclusions_df.style.applymap(style_red, subset=['CPT Code', 'Status Code'])
        
        st.dataframe(
            styled_exclusions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CPT Code": st.column_config.TextColumn("CPT Code", width="small"),
                "Status Code": st.column_config.TextColumn("Status Code", width="small")
            }
        )


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Section 3 view with payment rate comparison analysis
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use for analysis
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## SECTION 3 - Payment Rate Comparison")
    st.markdown("---")
    
    # Initialize session state for this section's results
    section_key = f"section_3_results_{cpt_code}"
    if section_key not in st.session_state:
        # Try to auto-load cache on first visit
        cached_data = load_cached_results(cpt_code)
        st.session_state[section_key] = cached_data  # Will be None if no cache exists
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        load_cache_btn = st.button("📦 Load Cache", key=f"load_cache_btn_s3_{idx}", use_container_width=True)
    
    with col2:
        regenerate_btn = st.button("🔄 Re-generate Analysis", key=f"regenerate_btn_s3_{idx}", use_container_width=True)
    
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
            fresh_data = analyze_payment_rate_comparison(cpt_code, model=model, use_cache=False)
            st.session_state[section_key] = fresh_data
            st.success("✅ Analysis completed and saved!")
            st.rerun()
    
    # Display results
    display_data = st.session_state[section_key]
    
    if display_data and display_data.get("analysis_content"):
        # Show source legend
        render_source_legend()
        
        # Display neighboring codes info if available
        payment_history = display_data.get("target_cpt_payment_history", {})
        neighboring_codes = payment_history.get("neighboring_codes", [])
        cpt_codes_analyzed = payment_history.get("cpt_codes_analyzed", [cpt_code])
        
        if neighboring_codes:
            st.info(f"📋 **Analyzing {len(cpt_codes_analyzed)} CPT codes**: Target code **{cpt_code}** + {len(neighboring_codes)} neighboring codes ({', '.join(neighboring_codes)})")
        
        # Display all three payment history tables
        st.markdown("---")
        st.markdown("## Payment History Tables")
        
        # APC Table
        if "apc" in payment_history:
            render_payment_table_apc(payment_history["apc"])
            st.markdown("---")
        
        # ASC Table  
        if "asc" in payment_history:
            render_payment_table_asc(payment_history["asc"])
            st.markdown("---")
        
        # PNPP Table
        if "pnpp" in payment_history:
            render_payment_table_pnpp(payment_history["pnpp"])
        
        # Display CPT Code Reference
        cpt_descriptions = display_data.get("cpt_descriptions", {})
        if cpt_descriptions:
            render_cpt_code_reference(cpt_descriptions)
        
        st.markdown("---")
        
        # Display LLM analysis
        st.markdown("### 🔍 Analysis")
        analysis_content = display_data.get("analysis_content", "")
        st.markdown(analysis_content)
        
        content_for_chat = analysis_content
    else:
        st.warning("⚠️ No results available. Please load cache or run analysis.")
        content_for_chat = ""
    
    # Chat Interface
    st.markdown("---")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="section_3",
        section_num="3",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    # Chat interface
    render_chat_interface(
        section_id="section_3",
        section_title="Payment Rate Comparison",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
