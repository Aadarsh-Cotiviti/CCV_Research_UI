"""
Payment Rate Comparison View (Section 3)

This module renders the UI for Section 3 - Payment Rate Comparison
"""

import streamlit as st
import pandas as pd
from services.payment_rate_service import analyze_payment_rate_comparison, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend


def render_payment_table(payment_history_dict):
    """
    Render payment history table as interactive dataframe
    
    Args:
        payment_history_dict: Dict with payment data and metadata
    """
    if not payment_history_dict or "data" not in payment_history_dict:
        st.warning("No payment history data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(payment_history_dict["data"])
    
    if df.empty:
        st.warning("No payment records found")
        return
    
    # Rename old column name for backward compatibility
    if 'APC' in df.columns and 'APC Code' not in df.columns:
        df.rename(columns={'APC': 'APC Code'}, inplace=True)
    
    # Clean APC Code column - remove decimals (e.g., "5072.0" -> "5072")
    if 'APC Code' in df.columns:
        df['APC Code'] = pd.to_numeric(df['APC Code'], errors='coerce').fillna(0).astype(int).astype(str)
    
    # Select and reorder columns, excluding Month, Addendum and Period
    display_columns = ['HCPCS Code', 'Year', 'SI', 'APC Code', 'Payment Rate']
    df_display = df[display_columns].copy()
    
    st.markdown(f"### 📊 Payment History Table")
    
    # Apply green styling to the entire dataframe
    def style_green(val):
        return 'color: #2e7d32'
    
    styled_df = df_display.style.applymap(style_green)
    
    # Display styled table
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
    
    # Add note about data source
    st.caption("📅 Payment data represents January rates for each year (2023, 2024, 2025) for all CPT codes analyzed.")


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
        
        # Display payment history table
        render_payment_table(payment_history)
        
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
