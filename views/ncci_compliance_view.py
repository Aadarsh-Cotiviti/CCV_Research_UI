"""
NCCI Compliance Check View (Section 5)

This module renders the UI for Section 5 - NCCI Compliance Check
"""

import streamlit as st
import pandas as pd
from services.ncci_compliance_service import analyze_ncci_compliance, load_cached_results
from .utils import render_accuracy_feedback, render_chat_interface, render_source_legend, format_text_with_source, get_source_color


def render_ptp_tables(ptp_tables_by_cpt, target_cpt, ncci_manual_by_cpt=None, ncci_chunk_details_by_cpt=None):
    """
    Render PTP edit tables for multiple CPT codes (target + neighboring)
    Each CPT shows 2 tables side by side:
    - Modifier 0 (Not Allowed) | Modifier 1 (Allowed with Modifier)
    Plus NCCI manual analysis below the tables
    
    Args:
        ptp_tables_by_cpt: Dict with CPT codes as keys, each containing modifier_0 and modifier_1 data
        target_cpt: The target CPT code (to highlight)
        ncci_manual_by_cpt: Dict mapping CPT codes to their NCCI manual analysis
        ncci_chunk_details_by_cpt: Dict mapping CPT codes to their chunk details
    """
    if not ptp_tables_by_cpt:
        st.warning("No PTP edit table data available")
        return
    
    st.markdown("### 📊 PTP Edit Tables")
    st.caption("🟢 **Green text** indicates data from local knowledge base (PTP edit tables)")
    
    # Display target CPT first
    for cpt_code in sorted(ptp_tables_by_cpt.keys(), key=lambda x: (x != target_cpt, x)):
        ptp_tables = ptp_tables_by_cpt[cpt_code]
        
        # Check if this CPT has any data
        has_data = ptp_tables.get("has_data", False)
        
        # CPT code header
        if cpt_code == target_cpt:
            st.markdown(f"#### 🎯 CPT {cpt_code} (Target Code)")
        else:
            st.markdown(f"#### CPT {cpt_code} (Neighboring Code)")
        
        if not has_data:
            st.info(f"ℹ️  CPT code {cpt_code} does not appear in the NCCI PTP edit tables")
            st.markdown("---")
            st.markdown("---")
            continue
        
        # Create two columns for side-by-side display
        col_left, col_right = st.columns(2)
        
        # LEFT COLUMN: Modifier 0 (Not Allowed) - GREEN color
        with col_left:
            st.markdown("##### 🚫 Modifier 0 (Not Allowed)")
            st.caption(f"Cannot bill {cpt_code} with these codes")
            
            if ptp_tables.get("modifier_0") and ptp_tables["modifier_0"].get("data"):
                df_mod0 = pd.DataFrame(ptp_tables["modifier_0"]["data"])
                
                if not df_mod0.empty:
                    # Select display columns
                    display_columns = ['CPT_code_1', 'CPT_code_2', 'Effective_Date', 'PTP_Edit_Rationale']
                    display_columns = [col for col in display_columns if col in df_mod0.columns]
                    df_display = df_mod0[display_columns].copy()
                    
                    # Style with green color (local_kb source)
                    def style_green(val):
                        return 'color: #2e7d32'
                    
                    styled_df = df_display.style.map(style_green)
                    
                    st.dataframe(
                        styled_df,
                        width='stretch',
                        hide_index=True,
                        height=400,
                        column_config={
                            "CPT_code_1": st.column_config.TextColumn("Code 1", width="small"),
                            "CPT_code_2": st.column_config.TextColumn("Code 2", width="small"),
                            "Effective_Date": st.column_config.TextColumn("Effective", width="small"),
                            "PTP_Edit_Rationale": st.column_config.TextColumn("Rationale", width="medium"),
                        }
                    )
                    st.caption(f"📊 {len(df_mod0)} records")
                else:
                    st.info("No Modifier 0 edits")
            else:
                st.info("No Modifier 0 edits")
        
        # RIGHT COLUMN: Modifier 1 (Allowed) - GREEN color
        with col_right:
            st.markdown("##### ✅ Modifier 1 (Allowed)")
            st.caption(f"Can bill {cpt_code} with these codes (with modifier)")
            
            if ptp_tables.get("modifier_1") and ptp_tables["modifier_1"].get("data"):
                df_mod1 = pd.DataFrame(ptp_tables["modifier_1"]["data"])
                
                if not df_mod1.empty:
                    # Select display columns
                    display_columns = ['CPT_code_1', 'CPT_code_2', 'Effective_Date', 'PTP_Edit_Rationale']
                    display_columns = [col for col in display_columns if col in df_mod1.columns]
                    df_display = df_mod1[display_columns].copy()
                    
                    # Style with green color (local_kb source)
                    def style_green(val):
                        return 'color: #2e7d32'
                    
                    styled_df = df_display.style.map(style_green)
                    
                    st.dataframe(
                        styled_df,
                        width='stretch',
                        hide_index=True,
                        height=400,
                        column_config={
                            "CPT_code_1": st.column_config.TextColumn("Code 1", width="small"),
                            "CPT_code_2": st.column_config.TextColumn("Code 2", width="small"),
                            "Effective_Date": st.column_config.TextColumn("Effective", width="small"),
                            "PTP_Edit_Rationale": st.column_config.TextColumn("Rationale", width="medium"),
                        }
                    )
                    st.caption(f"📊 {len(df_mod1)} records")
                else:
                    st.info("No Modifier 1 edits")
            else:
                st.info("No Modifier 1 edits")
        
        # Add NCCI Manual Analysis below tables (for all CPT codes)
        if ncci_manual_by_cpt and cpt_code in ncci_manual_by_cpt:
            ncci_manual_content = ncci_manual_by_cpt[cpt_code]
            ncci_chunk_details = ncci_chunk_details_by_cpt.get(cpt_code, {}) if ncci_chunk_details_by_cpt else {}
            
            st.markdown("---")
            st.markdown("##### 📚 NCCI Manual Analysis")
            
            analysis_text = ncci_manual_content.get("analysis", "")
            source = ncci_manual_content.get("source", "unknown")
            
            if analysis_text:
                # Remove references section completely from LLM output
                # We'll build our own unified references section from chunk_details
                import re as ref_regex
                
                # Pattern to match References/Citations section and everything after it
                # This catches the title and all citation content (e.g., [1] `chunk_xxx`, etc.)
                references_pattern = r'(?:^|\n)(?:##\s*)?(?:References|Citations):?\s*\n.*'
                main_content = ref_regex.sub(references_pattern, '', analysis_text, flags=ref_regex.IGNORECASE | ref_regex.DOTALL).strip()
                
                # Extract chunk IDs from ncci_chunk_details (if available)
                # This ensures we always show available chunks regardless of LLM format
                chunk_matches = list(ncci_chunk_details.keys()) if ncci_chunk_details else []
                
                # Remove the first title line (e.g., "# 🎯 NCCI Compliance Analysis for CPT xxxxx")
                # and any Markdown formatting markers
                import re as regex
                
                # Remove all Markdown headers (##, ###, etc.) and bold markers (**)
                main_content = regex.sub(r'\*\*', '', main_content)
                main_content = regex.sub(r'^#{1,6}\s+', '', main_content, flags=regex.MULTILINE)
                
                lines = main_content.split('\n')
                if lines and 'NCCI Compliance Analysis' in lines[0]:
                    lines = lines[1:]  # Skip the first title line
                    main_content = '\n'.join(lines).strip()
                
                # Use format_text_with_source for proper color display with HTML escaping
                formatted_content = format_text_with_source(main_content, source)
                st.markdown(formatted_content, unsafe_allow_html=True)
                    
                # Add References section with expandable chunks
                if chunk_matches:
                    # Display unified "References:" title with proper color formatting
                    references_title = format_text_with_source("References:", source)
                    st.markdown(f'<div style="margin-top: 10px; margin-bottom: 5px;">{references_title}</div>', unsafe_allow_html=True)
                    
                    # Display each citation number with its expander
                    for chunk_id in chunk_matches:
                        chunk_info = ncci_chunk_details.get(chunk_id, {}) if ncci_chunk_details else {}
                        
                        # Get the original citation number from chunk_info
                        citation_num = chunk_info.get('citation_number', '?') if chunk_info else '?'
                        
                        # Expander with citation number in the label (📄 [1] View Source Details)
                        with st.expander(f"📄 [{citation_num}] View Source Details", expanded=False):
                            st.markdown(f"**Chunk ID**: {chunk_id}")
                            
                            if chunk_info:
                                st.markdown(f"**Section**: {chunk_info.get('section', 'N/A')}")
                                st.markdown(f"**Pages**: {chunk_info.get('pages', 'N/A')}")
                                
                                if chunk_info.get('topic_tags'):
                                    st.markdown(f"**Tags**: {', '.join(chunk_info['topic_tags'])}")
                                
                                st.markdown("**Full Text**:")
                                st.text_area(
                                    "Chunk Content",
                                    value=chunk_info.get('full_text', ''),
                                    height=300,
                                    key=f"chunk_text_{cpt_code}_{chunk_id}_{citation_num}",
                                    label_visibility="collapsed"
                                )
                            else:
                                st.warning(f"⚠️ Chunk details not found for {chunk_id}")
            else:
                st.info("No NCCI manual analysis available")
        
        # Bold separator between CPT code sections
        st.markdown("---")
        st.markdown("---")


def render_cpt_codes_referenced(cpt_descriptions):
    """
    Render CPT codes referenced section with descriptions
    Color coding: Green for local_kb, Black for LLM
    
    Args:
        cpt_descriptions: Dict mapping CPT codes to their description info
    """
    if not cpt_descriptions:
        return
    
    st.markdown("### 📋 CPT Codes Referenced")
    st.caption("🟢 **Green text** indicates descriptions from local knowledge base | ⚫ **Black text** indicates LLM-generated descriptions")
    
    # Sort CPT codes numerically
    sorted_codes = sorted(cpt_descriptions.keys())
    
    for code in sorted_codes:
        desc_info = cpt_descriptions[code]
        description = desc_info.get("description", "No description available")
        source = desc_info.get("source", "unknown")
        
        # Use format_text_with_source to ensure proper color display
        formatted_description = format_text_with_source(description, source)
        st.markdown(f"**CPT {code}**: {formatted_description}", unsafe_allow_html=True)


def render_section(cpt_code, model, session_id, idx=0):
    """
    Render Section 5 view with NCCI compliance analysis
    
    Args:
        cpt_code: Target CPT code
        model: LLM model to use for analysis
        session_id: Current session ID
        idx: Tab index for unique keys
    """
    # Section title
    st.markdown("## SECTION 5 - NCCI Compliance Check")
    st.markdown("---")
    
    # Initialize session state for this section's results
    section_key = f"section_5_results_{cpt_code}"
    if section_key not in st.session_state:
        # Try to auto-load cache on first visit
        cached_data = load_cached_results(cpt_code)
        st.session_state[section_key] = cached_data  # Will be None if no cache exists
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        load_cache_btn = st.button("📦 Load Cache", key=f"load_cache_btn_s5_{idx}", use_container_width=True)
    
    with col2:
        regenerate_btn = st.button("🔄 Re-generate Analysis", key=f"regenerate_btn_s5_{idx}", use_container_width=True)
    
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
            fresh_data = analyze_ncci_compliance(cpt_code, model=model, use_cache=False)
            st.session_state[section_key] = fresh_data
            st.success("✅ Analysis completed and saved!")
            st.rerun()
    
    # Display results
    display_data = st.session_state[section_key]
    
    # Check if display_data has any results (ncci_manual_by_cpt or ptp_tables_by_cpt)
    has_results = display_data and (
        display_data.get("ncci_manual_by_cpt") or 
        display_data.get("ptp_tables_by_cpt") or
        display_data.get("analysis_content")  # Support old format
    )
    
    if has_results:
        # Show source legend
        render_source_legend()
        
        # Display neighboring codes info if available
        neighboring_codes = display_data.get("neighboring_codes", [])
        if neighboring_codes:
            st.info(f"📋 **Analyzing {cpt_code} and {len(neighboring_codes)} neighboring codes**: {', '.join(neighboring_codes)}")
        else:
            st.info(f"📋 **Analyzing CPT {cpt_code}** (no neighboring codes)")
        
        # Display PTP edit tables for all CPT codes
        ptp_tables_by_cpt = display_data.get("ptp_tables_by_cpt", {})
        
        # For backward compatibility with old cache format
        if not ptp_tables_by_cpt and "ptp_tables" in display_data:
            # Old format: single CPT's tables directly
            ptp_tables_by_cpt = {cpt_code: display_data["ptp_tables"]}
        
        # Get NCCI manual content and chunk details (now dictionaries by CPT code)
        ncci_manual_by_cpt = display_data.get("ncci_manual_by_cpt", {})
        ncci_chunk_details_by_cpt = display_data.get("ncci_chunk_details_by_cpt", {})
        
        # Handle backward compatibility for old format (single CPT)
        if ncci_manual_by_cpt and not isinstance(ncci_manual_by_cpt, dict):
            # Old format: single manual content for target CPT
            ncci_manual_by_cpt = {cpt_code: ncci_manual_by_cpt}
        if "ncci_chunk_details" in display_data and not isinstance(display_data["ncci_chunk_details"], dict):
            # Old format: single chunk details
            ncci_chunk_details_by_cpt = {cpt_code: display_data["ncci_chunk_details"]}
        
        render_ptp_tables(ptp_tables_by_cpt, cpt_code, ncci_manual_by_cpt, ncci_chunk_details_by_cpt)
        
        st.markdown("---")
        
        # Display LLM analysis ONLY if it exists in old format (backward compatibility)
        analysis_content = display_data.get("analysis_content", "")
        if analysis_content:
            st.markdown("### 🔍 Modifier Misuse Analysis")
            st.caption("⚠️ This is legacy analysis format - newer versions integrate analysis into NCCI Manual sections above")
            st.markdown(analysis_content)
            st.markdown("---")
        
        # Display CPT codes referenced
        cpt_descriptions = display_data.get("cpt_descriptions", {})
        render_cpt_codes_referenced(cpt_descriptions)
        
        # Collect content for chat (combine NCCI manual analyses if available)
        content_for_chat = analysis_content
        if ncci_manual_by_cpt:
            # Combine all NCCI manual analyses for chat context
            ncci_analyses = []
            for cpt, manual_data in ncci_manual_by_cpt.items():
                if manual_data.get("analysis"):
                    ncci_analyses.append(f"CPT {cpt}:\n{manual_data['analysis']}")
            if ncci_analyses:
                content_for_chat = "\n\n".join(ncci_analyses)
    else:
        st.warning("⚠️ No results available. Please load cache or run analysis.")
        content_for_chat = ""
    
    # Chat Interface
    st.markdown("---")
    
    # Accuracy feedback
    render_accuracy_feedback(
        section_id="section_5",
        section_num="5",
        session_id=session_id,
        cpt_code=cpt_code
    )
    
    st.subheader("💬 Ask Questions About This Section")
    
    # Chat interface
    render_chat_interface(
        section_id="section_5",
        section_title="NCCI Compliance Check",
        section_content=content_for_chat,
        session_id=session_id,
        cpt_code=cpt_code,
        model=model,
        idx=idx
    )
