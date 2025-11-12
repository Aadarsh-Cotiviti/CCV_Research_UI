import streamlit as st
from datetime import datetime, timedelta
from llm_wrapper import query_llm
import pandas as pd
from io import BytesIO
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def compute_audit_window():
    """Compute the audit window for claims (3 years back from today)"""
    current_date = datetime.now()
    start_date = current_date - timedelta(days=1095)  # 3 years = 1095 days
    return start_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")

def build_research_prompt(target_cpt, context_details):
    """Build comprehensive research prompt for APC analysis"""
    window_start, window_end = compute_audit_window()
    
    research_query = f"""
As a medical coding specialist focused on APC analysis, perform a thorough evaluation for CPT code: {target_cpt}

Audit Window: {window_start} through {window_end}

Context Information: {context_details or "Not specified"}

Complete the following analysis sections:

SECTION 1 - Code Description Analysis
- Review detailed descriptions for {target_cpt} and neighboring codes
- List neighboring codes in ASCENDING ORDER (from lowest to highest code number)
- Detect re-coding possibilities considering:
  • Procedural approach variations (open, percutaneous, laparoscopic)
  • Anatomical location differences
  • Intervention technique specifics
  • Potential bundling scenarios

SECTION 2 - Guideline Examination
- Extract instructional notes specific to {target_cpt}
- Summarize applicable chapter-level guidelines
- Note parenthetical references and code relationships

SECTION 3 - Payment Rate Comparison
- Evaluate APC assignments and payment rates for {target_cpt} and related codes
- Present the comparison in a TABLE format with the following columns:
  | CPT Code | APC Code | Payment Rate | Status | Notes |
- Categorize findings:
  • Matching rates → No audit opportunity
  • Differing rates → Investigate further
- Track rate consistency across quarters/years within audit window
- Flag potential underpayment or overpayment patterns
- Use markdown table format for clear presentation

SECTION 4 - Device Code Analysis
- Confirm if {target_cpt} involves medical devices
- List relevant HCPCS device codes
- Highlight common errors:
  • Procedure without device code
  • Device-procedure mismatch
  • Incorrect device type selection

SECTION 5 - NCCI Compliance Check
- Reference NCCI Edit Manual for {target_cpt}
- Examine PTP (Procedure-to-Procedure) edits
- Detect modifier abuse patterns:
  • Inappropriate modifier 59 usage
  • Modifier 25 misapplication
  • Other unbundling indicators

SECTION 6 - Reference Material Review
- Locate CPT Assistant guidance for {target_cpt}
- Find applicable HCPCS Coding Clinic articles
- Document special coding considerations

FINAL ASSESSMENT
- Consolidate findings and opportunities
- Assign priority level (Critical/Moderate/Low)
- Recommend validation steps

Structure output with clear headings and organized bullet points. Use markdown tables where specified.
"""
    return research_query

def generate_cpt_codes_from_topic(topic, model="gpt-4.1-mini"):
    """Generate relevant CPT codes from a medical procedure topic"""
    prompt = f"""
You are a medical coding expert. Given the following medical procedure or condition topic, provide the top 5 most relevant CPT codes.

Topic: {topic}

For each CPT code, provide:
1. The CPT code number
2. A brief description (one line)

Format your response EXACTLY as follows (one code per line):
CODE: [5-digit code] | DESCRIPTION: [brief description]

Example format:
CODE: 99213 | DESCRIPTION: Office visit, established patient, moderate complexity
CODE: 99214 | DESCRIPTION: Office visit, established patient, high complexity

Provide exactly 5 CPT codes. If the topic is too vague or unclear, provide the most commonly associated codes.
"""
    
    messages = [
        {"role": "system", "content": "You are an expert medical coding specialist with deep knowledge of CPT codes."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = query_llm(messages, model=model)
        return response
    except Exception as e:
        return f"Error generating CPT codes: {str(e)}"

def parse_cpt_codes(llm_response):
    """Parse LLM response to extract CPT codes and descriptions"""
    codes = []
    lines = llm_response.strip().split('\n')
    
    for line in lines:
        if 'CODE:' in line and 'DESCRIPTION:' in line:
            try:
                parts = line.split('|')
                code_part = parts[0].split('CODE:')[1].strip()
                desc_part = parts[1].split('DESCRIPTION:')[1].strip()
                codes.append({"code": code_part, "description": desc_part})
            except:
                continue
    
    return codes

def create_excel_output(analysis_content, cpt_value):
    """Create Excel workbook from research analysis"""
    output_buffer = BytesIO()
    
    window_start, window_end = compute_audit_window()
    
    # Prepare data structure
    summary_data = {
        "Field": ["Report Date", "CPT Code", "Audit Window Start", "Audit Window End"],
        "Value": [datetime.now().strftime("%Y-%m-%d %H:%M"), cpt_value, window_start, window_end]
    }
    
    sections_data = {
        "Section": [
            "Code Description Analysis",
            "Guideline Examination", 
            "Payment Rate Comparison",
            "Device Code Analysis",
            "NCCI Compliance Check",
            "Reference Material Review"
        ],
        "Status": ["Completed"] * 6
    }
    
    # Create Excel file
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        pd.DataFrame(sections_data).to_excel(writer, sheet_name='Sections', index=False)
        
        # Split analysis into manageable chunks for Excel cells
        analysis_lines = analysis_content.split('\n')
        chunks = [analysis_lines[i:i+50] for i in range(0, len(analysis_lines), 50)]
        
        for idx, chunk in enumerate(chunks):
            chunk_df = pd.DataFrame({"Content": chunk})
            chunk_df.to_excel(writer, sheet_name=f'Analysis_Part{idx+1}', index=False)
    
    output_buffer.seek(0)
    return output_buffer

def create_pdf_output(analysis_content, cpt_value):
    """Create PDF report from research analysis"""
    output_buffer = BytesIO()
    
    window_start, window_end = compute_audit_window()
    
    # Create PDF document
    doc = SimpleDocTemplate(output_buffer, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=0.75*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#10a37f',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#343541',
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph("🏥 APC Target Code Research Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata section
    story.append(Paragraph("<b>Report Details</b>", heading_style))
    metadata_text = f"""
    <b>CPT Code:</b> {cpt_value}<br/>
    <b>Report Date:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}<br/>
    <b>Audit Window:</b> {window_start} to {window_end}<br/>
    """
    story.append(Paragraph(metadata_text, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Analysis content
    story.append(Paragraph("<b>Analysis Report</b>", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Process analysis content - split by lines and format
    lines = analysis_content.split('\n')
    for line in lines:
        if line.strip():
            # Check if line is a section header
            if line.strip().startswith('SECTION') or line.strip().startswith('FINAL'):
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(f"<b>{line.strip()}</b>", heading_style))
            else:
                # Regular content line
                # Escape special characters for XML
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(safe_line, normal_style))
        else:
            story.append(Spacer(1, 0.05*inch))
    
    # Build PDF
    doc.build(story)
    
    output_buffer.seek(0)
    return output_buffer

def render_apc_interface():
    """Main interface for APC Research"""
    st.title("🏥 APC Target Code Research")
    st.markdown("---")
    
    # Display audit window
    window_start, window_end = compute_audit_window()
    st.info(f"📅 Current Audit Window: {window_start} to {window_end}")
    
    # Add custom CSS for buttons and labels
    st.markdown("""
        <style>
            .stForm button[type="submit"] {
                background-color: #000000 !important;
                color: white !important;
            }
            .stForm button[type="submit"]:hover {
                background-color: #333333 !important;
                color: white !important;
            }
            .stForm label {
                color: #ffffff !important;
            }
            .cpt-code-button {
                background-color: #10a37f !important;
                color: white !important;
                padding: 10px 15px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                text-align: left;
            }
            .cpt-code-button:hover {
                background-color: #0d8566 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for workflow
    if "apc_step" not in st.session_state:
        st.session_state.apc_step = 1
    if "generated_cpts" not in st.session_state:
        st.session_state.generated_cpts = []
    if "selected_cpt" not in st.session_state:
        st.session_state.selected_cpt = None
    if "topic_description" not in st.session_state:
        st.session_state.topic_description = ""
    
    # STEP 1: Topic Input and CPT Code Generation
    if st.session_state.apc_step == 1:
        st.subheader("📋 Step 1: Enter Topic and Generate CPT Codes")
        
        with st.form("topic_form"):
            topic_input = st.text_input(
                "Medical Procedure or Condition Topic",
                placeholder="e.g., Bronchial Biopsy, Knee Replacement, Cardiac Catheterization",
                help="Enter a medical procedure or condition to find relevant CPT codes"
            )
            
            model_for_generation = st.selectbox(
                "Model for CPT Generation",
                ["gpt-4.1", "gpt-4.1-mini", "gpt-5", "gpt-5-mini"],
                index=1,
                help="Select the AI model for generating CPT codes"
            )
            
            generate_btn = st.form_submit_button("🔍 Generate CPT Codes", use_container_width=True)
        
        if generate_btn and topic_input:
            with st.spinner("Generating relevant CPT codes..."):
                llm_response = generate_cpt_codes_from_topic(topic_input, model=model_for_generation)
                parsed_codes = parse_cpt_codes(llm_response)
                
                if parsed_codes:
                    st.session_state.generated_cpts = parsed_codes
                    st.session_state.topic_description = topic_input
                    st.session_state.apc_step = 1.5  # Show CPT selection
                    st.rerun()
                else:
                    st.error("⚠️ No relevant CPT codes found. Please try a different topic or be more specific.")
        
        elif generate_btn and not topic_input:
            st.error("⚠️ Please enter a medical topic to generate CPT codes.")
    
    # STEP 1.5: Display Generated CPT Codes for Selection
    if st.session_state.apc_step == 1.5:
        st.subheader("📋 Step 1: Select a CPT Code")
        st.info(f"Topic: **{st.session_state.topic_description}**")
        
        st.markdown("### Generated CPT Codes")
        st.markdown("Click on a CPT code to proceed with research:")
        
        for idx, cpt_info in enumerate(st.session_state.generated_cpts):
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"**{cpt_info['code']}**", key=f"cpt_btn_{idx}", use_container_width=True):
                    st.session_state.selected_cpt = cpt_info['code']
                    st.session_state.apc_step = 2
                    st.rerun()
            with col2:
                st.markdown(f"<div style='padding: 10px; color: #e0e0e0;'>{cpt_info['description']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("← Back to Topic Input"):
            st.session_state.apc_step = 1
            st.session_state.generated_cpts = []
            st.rerun()
    
    # STEP 2: Research Parameters and Analysis
    if st.session_state.apc_step == 2:
        st.subheader("📋 Step 2: Conduct APC Research")
        
        # Display selected CPT and topic
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"**Selected CPT Code:** {st.session_state.selected_cpt}")
        with col_info2:
            st.info(f"**Topic:** {st.session_state.topic_description}")
        
        with st.form("apc_research_form"):
            # Auto-fill context with topic
            default_context = f"Related to {st.session_state.topic_description}"
            
            additional_context = st.text_area(
                "Additional Context",
                value=default_context,
                placeholder="Provide any specific details: surrounding codes, known issues, claim examples, etc.",
                height=100,
                help="Context has been pre-filled with your topic. You can modify or add more details."
            )
            
            selected_model = st.selectbox(
                "Analysis Model",
                ["gpt-4.1", "gpt-4.1-mini", "gpt-5", "gpt-5-mini"],
                help="Select the AI model for comprehensive analysis"
            )
            
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                back_btn = st.form_submit_button("← Back")
            with col_btn2:
                submit_btn = st.form_submit_button("🔍 Start Research", use_container_width=True)
        
        if back_btn:
            st.session_state.apc_step = 1.5
            st.rerun()
        
        if submit_btn:
            with st.spinner("Conducting comprehensive APC research..."):
                # Build prompt and query LLM
                research_prompt = build_research_prompt(st.session_state.selected_cpt, additional_context)
                
                messages = [
                    {"role": "system", "content": "You are an expert medical coding analyst specializing in APC research."},
                    {"role": "user", "content": research_prompt}
                ]
                
                analysis_result = query_llm(messages, model=selected_model)
                
                # Store in session state
                st.session_state.apc_analysis = {
                    "cpt_code": st.session_state.selected_cpt,
                    "context": additional_context,
                    "model": selected_model,
                    "result": analysis_result,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "topic": st.session_state.topic_description
                }
                st.session_state.apc_step = 3
                st.rerun()
    
    # STEP 3: Display Results
    if st.session_state.apc_step == 3 and "apc_analysis" in st.session_state:
        st.markdown("---")
        st.subheader("📊 Research Results")
        
        analysis_data = st.session_state.apc_analysis
        
        # Metadata with custom styling
        st.markdown("""
            <style>
                div[data-testid="stMetricValue"] {
                    color: #e0e0e0 !important;
                }
                div[data-testid="stMetricLabel"] {
                    color: #e0e0e0 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("CPT Code", analysis_data["cpt_code"])
        col2.metric("Model Used", analysis_data["model"])
        col3.metric("Generated", analysis_data["timestamp"])
        
        # Analysis content with larger font - render as markdown to preserve tables
        st.markdown("### Analysis Report")
        
        # Add custom CSS for larger markdown content
        st.markdown("""
            <style>
                .stMarkdown p, .stMarkdown li, .stMarkdown td {
                    font-size: 1.1rem !important;
                    line-height: 1.6 !important;
                }
                .stMarkdown table {
                    font-size: 1.05rem !important;
                    margin: 15px 0 !important;
                }
                .stMarkdown th {
                    background-color: #10a37f !important;
                    color: white !important;
                    padding: 10px !important;
                    font-weight: bold !important;
                }
                .stMarkdown td {
                    padding: 8px !important;
                    border: 1px solid #555 !important;
                }
                .stMarkdown h1, .stMarkdown h2 {
                    color: #10a37f !important;
                    font-size: 1.8rem !important;
                    font-weight: bold !important;
                    margin-top: 25px !important;
                    margin-bottom: 15px !important;
                    padding-bottom: 8px !important;
                    border-bottom: 2px solid #10a37f !important;
                }
                .stMarkdown h3 {
                    color: #e0e0e0 !important;
                    font-size: 1.4rem !important;
                    font-weight: bold !important;
                    margin-top: 20px !important;
                    margin-bottom: 12px !important;
                }
                .stMarkdown strong {
                    color: #10a37f !important;
                    font-weight: bold !important;
                }
                .stMarkdown ul, .stMarkdown ol {
                    margin-left: 20px !important;
                    margin-bottom: 15px !important;
                }
                .stMarkdown li {
                    margin-bottom: 8px !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Process and format the result to make sections stand out
        formatted_result = analysis_data["result"]
        
        # Replace SECTION headers with H2 markdown for better styling
        import re
        formatted_result = re.sub(r'^(SECTION \d+ - [^\n]+)', r'## \1', formatted_result, flags=re.MULTILINE)
        formatted_result = re.sub(r'^(FINAL ASSESSMENT)', r'## \1', formatted_result, flags=re.MULTILINE)
        
        # Render the analysis result as markdown (preserves tables)
        st.markdown(formatted_result)
        
        # Download options
        st.markdown("---")
        st.subheader("💾 Export Options")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Excel download
            excel_file = create_excel_output(analysis_data["result"], analysis_data["cpt_code"])
            st.download_button(
                label="📊 Download as Excel",
                data=excel_file,
                file_name=f"apc_research_{analysis_data['cpt_code']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col_b:
            # PDF download
            pdf_file = create_pdf_output(analysis_data["result"], analysis_data["cpt_code"])
            st.download_button(
                label="📑 Download as PDF",
                data=pdf_file,
                file_name=f"apc_research_{analysis_data['cpt_code']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        
        # Option to start new research
        st.markdown("---")
        if st.button("🔄 Start New Research"):
            # Reset workflow
            st.session_state.apc_step = 1
            st.session_state.generated_cpts = []
            st.session_state.selected_cpt = None
            st.session_state.topic_description = ""
            if "apc_analysis" in st.session_state:
                del st.session_state.apc_analysis
            st.rerun()
