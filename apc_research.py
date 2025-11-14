import streamlit as st
from datetime import datetime, timedelta
from llm_wrapper import query_llm
import pandas as pd
from io import BytesIO
import json
import sqlite3
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def init_notes_db():
    """Initialize notes database"""
    db_path = os.path.join(os.path.dirname(__file__), "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            cpt_code TEXT,
            notes_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def save_notes(session_id, cpt_code, notes_text):
    """Save or update notes for a session/CPT code"""
    db_path = os.path.join(os.path.dirname(__file__), "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if notes already exist for this session/CPT
    cursor.execute("""
        SELECT id FROM notes WHERE session_id = ? AND cpt_code = ?
    """, (session_id, cpt_code))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing notes
        cursor.execute("""
            UPDATE notes SET notes_text = ?, updated_at = ?
            WHERE session_id = ? AND cpt_code = ?
        """, (notes_text, timestamp, session_id, cpt_code))
    else:
        # Insert new notes
        cursor.execute("""
            INSERT INTO notes (session_id, cpt_code, notes_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, cpt_code, notes_text, timestamp, timestamp))
    
    conn.commit()
    conn.close()

def get_notes(session_id, cpt_code):
    """Retrieve notes for a session/CPT code"""
    db_path = os.path.join(os.path.dirname(__file__), "apc_notes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT notes_text FROM notes WHERE session_id = ? AND cpt_code = ?
    """, (session_id, cpt_code))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else ""

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
            /* Sidebar notes text area styling */
            .stSidebar .stTextArea textarea {
                background-color: #2c2c2c !important;
                color: #ffffff !important;
                border: 1px solid #555 !important;
                border-radius: 6px !important;
                font-size: 0.9rem !important;
                line-height: 1.5 !important;
            }
            .stSidebar .stTextArea label {
                color: #ffffff !important;
            }
            
            /* Reduce spacing for info boxes */
            .stAlert {
                margin-top: 0.25rem !important;
                margin-bottom: 0.25rem !important;
                padding: 0.5rem 1rem !important;
            }
            
            /* Reduce spacing around horizontal lines */
            hr {
                margin-top: 0.25rem !important;
                margin-bottom: 0.25rem !important;
            }
            
            /* Reduce spacing around subheaders */
            h3 {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }
            
            .stForm label {
                color: #ffffff !important;
            }
            /* Form submit buttons - MOST SPECIFIC FIRST */
            .stForm button[type="submit"],
            form button[type="submit"],
            div[data-testid="stForm"] button,
            .stForm .stFormSubmitButton > button {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }
            .stForm button[type="submit"]:hover,
            form button[type="submit"]:hover,
            div[data-testid="stForm"] button:hover,
            .stForm .stFormSubmitButton > button:hover {
                background-color: #f0f0f0 !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
            }
            /* Force text color inside form buttons */
            .stForm button[type="submit"] *,
            form button[type="submit"] *,
            div[data-testid="stForm"] button *,
            .stForm .stFormSubmitButton > button * {
                color: #000000 !important;
            }
            /* ALL BUTTONS - White background with black text using multiple selectors */
            .stButton > button,
            button[data-testid="baseButton-primary"],
            button[data-testid="baseButton-secondary"],
            div[data-testid="stButton"] > button,
            button[kind="primary"],
            button[kind="secondary"] {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
                transition: background-color 0.3s !important;
            }
            /* Button text and children */
            .stButton > button *,
            button[data-testid="baseButton-primary"] *,
            button[data-testid="baseButton-secondary"] *,
            div[data-testid="stButton"] > button * {
                color: #000000 !important;
            }
            /* Hover states */
            .stButton > button:hover,
            button[data-testid="baseButton-primary"]:hover,
            button[data-testid="baseButton-secondary"]:hover,
            div[data-testid="stButton"] > button:hover,
            button[kind="primary"]:hover,
            button[kind="secondary"]:hover {
                background-color: #f0f0f0 !important;
                border: 2px solid #000000 !important;
                color: #000000 !important;
            }
            /* Active/Focus states */
            .stButton > button:active,
            .stButton > button:focus,
            button[data-testid="baseButton-primary"]:active,
            button[data-testid="baseButton-secondary"]:active {
                background-color: #e0e0e0 !important;
                border: 2px solid #000000 !important;
                color: #000000 !important;
                box-shadow: none !important;
            }
            /* Download buttons */
            .stDownloadButton > button,
            div[data-testid="stDownloadButton"] > button {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }
            .stDownloadButton > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {
                background-color: #f0f0f0 !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize notes database
    init_notes_db()
    
    # Initialize session state for workflow
    if "apc_step" not in st.session_state:
        st.session_state.apc_step = 1
    if "generated_cpts" not in st.session_state:
        st.session_state.generated_cpts = []
    if "selected_cpt" not in st.session_state:
        st.session_state.selected_cpt = None
    if "topic_description" not in st.session_state:
        st.session_state.topic_description = ""
    if "show_notes" not in st.session_state:
        st.session_state.show_notes = False
    
    # Sidebar: Notes Section
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📝 Research Notes")
        
        if st.button("✏️ Open Notes", use_container_width=True):
            st.session_state.show_notes = not st.session_state.show_notes
        
        if st.session_state.show_notes:
            # Get current CPT code if available
            current_cpt = st.session_state.selected_cpt if st.session_state.selected_cpt else "general"
            session_id = st.session_state.get("session_id", "default")
            
            # Load existing notes
            existing_notes = get_notes(session_id, current_cpt)
            
            st.markdown(f"**Notes for:** {current_cpt}")
            
            notes_text = st.text_area(
                "Your Notes",
                value=existing_notes,
                height=300,
                placeholder="Add your research notes here...",
                help="These notes will be saved for this CPT code",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Notes", use_container_width=True):
                    save_notes(session_id, current_cpt, notes_text)
                    st.success("✅ Notes saved!")
            with col2:
                if st.button("❌ Close", use_container_width=True):
                    st.session_state.show_notes = False
                    st.rerun()
    
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
                if st.button(cpt_info['code'], key=f"cpt_btn_{idx}", use_container_width=True):
                    st.session_state.selected_cpt = cpt_info['code']
                    st.session_state.apc_step = 2
                    st.rerun()
            with col2:
                st.markdown(f"<div style='padding: 10px 20px; color: #e0e0e0; font-size: 1rem;'>{cpt_info['description']}</div>", unsafe_allow_html=True)
        
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
        # Add CSS to reduce spacing before Research Results
        st.markdown("""
            <style>
                hr { margin: 0.5rem 0 !important; }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📊 Research Results")
        
        analysis_data = st.session_state.apc_analysis
        
        # Metadata with custom styling
        st.markdown("""
            <style>
                /* Metric values and labels - force white */
                div[data-testid="stMetricValue"],
                div[data-testid="stMetricValue"] *,
                [data-testid="stMetricValue"],
                [data-testid="stMetricValue"] * {
                    color: #ffffff !important;
                    font-weight: bold !important;
                }
                div[data-testid="stMetricLabel"],
                div[data-testid="stMetricLabel"] *,
                [data-testid="stMetricLabel"],
                [data-testid="stMetricLabel"] * {
                    color: #ffffff !important;
                    font-weight: bold !important;
                }
                /* Alternative metric selectors */
                .stMetric > div > div {
                    color: #ffffff !important;
                }
                .stMetric label {
                    color: #ffffff !important;
                    font-weight: bold !important;
                }
                .stMetric [data-testid="metric-container"] {
                    color: #ffffff !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("CPT Code", analysis_data["cpt_code"])
        col2.metric("Model Used", analysis_data["model"])
        col3.metric("Generated", analysis_data["timestamp"])
        
        # Reduce spacing before Analysis Report heading
        st.markdown("<style>.stMarkdown h3:first-of-type { margin-top: 0.5rem !important; }</style>", unsafe_allow_html=True)
        
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
                    margin-top: 10px !important;
                    margin-bottom: 10px !important;
                    padding-bottom: 8px !important;
                    border-bottom: 2px solid #10a37f !important;
                }
                .stMarkdown h3 {
                    color: #e0e0e0 !important;
                    font-size: 1.4rem !important;
                    font-weight: bold !important;
                    margin-top: 12px !important;
                    margin-bottom: 8px !important;
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
        
        # Initialize section accuracy tracking in session state
        if "section_accuracy" not in st.session_state:
            st.session_state.section_accuracy = {}
        
        # Process and format the result to make sections stand out
        formatted_result = analysis_data["result"]
        
        # Split content by sections
        import re
        section_pattern = r'(SECTION \d+ - [^\n]+)'
        sections = re.split(section_pattern, formatted_result)
        
        # First part before any section
        if sections[0].strip():
            st.markdown(sections[0])
        
        # Process each section with accuracy toggle
        for i in range(1, len(sections), 2):
            if i < len(sections):
                section_title = sections[i]
                section_content = sections[i+1] if i+1 < len(sections) else ""
                
                # Extract section number
                section_match = re.match(r'SECTION (\d+)', section_title)
                section_num = section_match.group(1) if section_match else str((i+1)//2)
                
                # Create columns for section title and accuracy toggle
                col_title, col_toggle = st.columns([3, 2])
                
                with col_title:
                    st.markdown(f"## {section_title}")
                
                with col_toggle:
                    # Display "Accurate?" label and inline buttons
                    st.markdown("<p style='color: #b0b0b0; font-size: 0.85rem; margin-bottom: 0.25rem; margin-top: 1rem;'>Accurate?</p>", unsafe_allow_html=True)
                    
                    accuracy_key = f"section_{section_num}_accuracy"
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        if st.button("✅ Yes", key=f"{accuracy_key}_yes", use_container_width=True):
                            st.session_state.section_accuracy[section_num] = "✅ Yes"
                    with btn_col2:
                        if st.button("⚠️ Maybe", key=f"{accuracy_key}_maybe", use_container_width=True):
                            st.session_state.section_accuracy[section_num] = "⚠️ Maybe"
                    with btn_col3:
                        if st.button("❌ No", key=f"{accuracy_key}_no", use_container_width=True):
                            st.session_state.section_accuracy[section_num] = "❌ No"
                
                # Display section content
                # Convert markdown formatting for better display
                formatted_content = re.sub(r'^(FINAL ASSESSMENT)', r'## \1', section_content, flags=re.MULTILINE)
                st.markdown(formatted_content)
        
        # Handle FINAL ASSESSMENT if present
        final_assessment_match = re.search(r'(FINAL ASSESSMENT[^\n]*)(.*)', formatted_result, re.DOTALL)
        if final_assessment_match and 'SECTION' not in final_assessment_match.group(0).split('\n')[0]:
            st.markdown(f"## {final_assessment_match.group(1)}")
            st.markdown(final_assessment_match.group(2))
        
        # Display section accuracy summary if any sections were rated
        if st.session_state.section_accuracy:
            st.markdown("---")
            st.subheader("📊 Section Accuracy Summary")
            
            summary_cols = st.columns(6)
            for idx, (section_num, rating) in enumerate(st.session_state.section_accuracy.items()):
                with summary_cols[idx % 6]:
                    st.metric(f"Section {section_num}", rating)
        
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
