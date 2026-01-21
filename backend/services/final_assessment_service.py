"""
Final Assessment Service

This module generates comprehensive final assessment by consolidating
key findings from Sections 1-6:
- Section 1: CPT code descriptions (target + neighbors)
- Section 3: Payment rate history
- Section 4: Device code descriptions
- Section 5: NCCI manual and PTP table results

All data is extracted from internal_kb sources.
"""

import os
import json
import datetime
from pathlib import Path
from datetime import datetime as dt
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .utils import compute_audit_window

# Output directory for generated reports
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def load_section_results(target_cpt, section_num):
    """
    Load saved results from a specific section
    
    Args:
        target_cpt: Target CPT code
        section_num: Section number (1-6)
        
    Returns:
        Dict with section results, or None if not found
    """
    output_dir = f"output/services_findings/{target_cpt}"
    file_name = f"section_{section_num}_results.json"
    file_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"⚠️  Section {section_num} results not found: {file_path}")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Loaded Section {section_num} results from {file_path}")
        return data
    except Exception as e:
        print(f"⚠️  Error loading Section {section_num} results: {str(e)}")
        return None


def extract_cpt_descriptions(section1_data):
    """
    Extract CPT code descriptions from Section 1
    
    Args:
        section1_data: Section 1 results dict
        
    Returns:
        Dict mapping CPT codes to their descriptions with source
    """
    cpt_descriptions = {}
    
    if not section1_data:
        return cpt_descriptions
    
    # Extract from neighbouring_codes (includes target + neighbors)
    neighbouring_codes = section1_data.get('neighbouring_codes', [])
    for code_info in neighbouring_codes:
        cpt_code = code_info.get('cpt_code')
        description = code_info.get('description', 'Description not available')
        source = code_info.get('source', 'unknown')
        
        if cpt_code:
            cpt_descriptions[cpt_code] = {
                'description': description,
                'source': source
            }
    
    print(f"📋 Extracted {len(cpt_descriptions)} CPT descriptions from Section 1")
    return cpt_descriptions


def extract_ncci_results(section5_data):
    """
    Extract NCCI manual and PTP table results from Section 5
    
    Args:
        section5_data: Section 5 results dict
        
    Returns:
        Dict with NCCI findings for each CPT code
    """
    ncci_results = {}
    
    if not section5_data:
        return ncci_results
    
    target_cpt = section5_data.get('cpt_code')
    neighboring_codes = section5_data.get('neighboring_codes', [])
    all_codes = [target_cpt] + neighboring_codes if target_cpt else neighboring_codes
    
    # Extract PTP table results
    ptp_tables = section5_data.get('ptp_tables_by_cpt', {})
    
    # Extract NCCI manual results from analysis_content
    analysis_content = section5_data.get('analysis_content', '')
    
    for cpt_code in all_codes:
        result = {
            'cpt_code': cpt_code,
            'ptp_modifier_0': None,
            'ptp_modifier_1': None,
            'ncci_manual_summary': '',
            'has_ncci_data': False
        }
        
        # Get PTP table data for this code
        if cpt_code in ptp_tables:
            ptp_data = ptp_tables[cpt_code]
            
            if ptp_data.get('modifier_0'):
                mod0 = ptp_data['modifier_0']
                result['ptp_modifier_0'] = {
                    'record_count': mod0.get('record_count', 0),
                    'data': mod0.get('data', [])
                }
                result['has_ncci_data'] = True
            
            if ptp_data.get('modifier_1'):
                mod1 = ptp_data['modifier_1']
                result['ptp_modifier_1'] = {
                    'record_count': mod1.get('record_count', 0),
                    'data': mod1.get('data', [])
                }
                result['has_ncci_data'] = True
        
        # Extract relevant NCCI manual content for this code from analysis_content
        # The analysis_content contains text analysis of NCCI guidelines
        if cpt_code in analysis_content:
            # Find sections mentioning this code
            lines = analysis_content.split('\n')
            relevant_lines = [line for line in lines if cpt_code in line]
            if relevant_lines:
                result['ncci_manual_summary'] = '\n'.join(relevant_lines[:5])  # First 5 relevant lines
                result['has_ncci_data'] = True
        
        ncci_results[cpt_code] = result
    
    print(f"📋 Extracted NCCI results for {len(ncci_results)} codes from Section 5")
    return ncci_results


def extract_device_descriptions(section4_data):
    """
    Extract device code descriptions from Section 4
    
    Args:
        section4_data: Section 4 results dict
        
    Returns:
        List of device codes with descriptions
    """
    device_codes = []
    
    if not section4_data:
        return device_codes
    
    # Extract from device_codes_with_desc
    device_codes_with_desc = section4_data.get('device_codes_with_desc', [])
    
    for device_info in device_codes_with_desc:
        hcpcs_code = device_info.get('hcpcs_code')
        description = device_info.get('description', 'Description not available')
        source = device_info.get('source', 'unknown')
        
        device_codes.append({
            'hcpcs_code': hcpcs_code,
            'description': description.strip(),
            'source': source
        })
    
    print(f"📋 Extracted {len(device_codes)} device code descriptions from Section 4")
    return device_codes


def extract_payment_history(section3_data):
    """
    Extract payment rate comparison history from Section 3
    
    Args:
        section3_data: Section 3 results dict
        
    Returns:
        Dict with payment history data
    """
    payment_history = {
        'data': [],
        'has_data': False
    }
    
    if not section3_data:
        return payment_history
    
    # Extract target_cpt_payment_history
    target_payment = section3_data.get('target_cpt_payment_history', {})
    
    if target_payment and 'data' in target_payment:
        payment_history['data'] = target_payment['data']
        payment_history['has_data'] = len(target_payment['data']) > 0
    
    print(f"📋 Extracted payment history with {len(payment_history['data'])} records from Section 3")
    return payment_history


def generate_final_assessment(target_cpt, use_cache=True):
    """
    Generate comprehensive final assessment by consolidating results from Sections 1-6
    
    Args:
        target_cpt: Target CPT code
        use_cache: Whether to use cached results (default True)
        
    Returns:
        Dict with consolidated assessment data
    """
    print(f"\n{'='*80}")
    print(f"🎯 Generating Final Assessment for CPT {target_cpt}")
    print(f"{'='*80}\n")
    
    # Check for existing cache
    if use_cache:
        cached = load_cached_final_assessment(target_cpt)
        if cached:
            print("✅ Using cached final assessment")
            return cached
    
    # Load results from each section
    print("📂 Loading section results...")
    section1 = load_section_results(target_cpt, 1)  # Code descriptions
    section3 = load_section_results(target_cpt, 3)  # Payment rates
    section4 = load_section_results(target_cpt, 4)  # Device codes
    section5 = load_section_results(target_cpt, 5)  # NCCI compliance
    
    # Extract relevant data from each section
    print("\n🔍 Extracting and consolidating data...")
    
    cpt_descriptions = extract_cpt_descriptions(section1)
    ncci_results = extract_ncci_results(section5)
    device_codes = extract_device_descriptions(section4)
    payment_history = extract_payment_history(section3)
    
    # Build comprehensive assessment
    assessment = {
        'target_cpt': target_cpt,
        'cpt_descriptions': cpt_descriptions,
        'ncci_results': ncci_results,
        'device_codes': device_codes,
        'payment_history': payment_history,
        'update_time': dt.now().strftime("%Y%m%d_%H%M%S"),
        'source': 'internal_kb'
    }
    
    # Save to cache
    save_final_assessment(target_cpt, assessment)
    
    print(f"\n✅ Final Assessment generated successfully")
    print(f"   - CPT Descriptions: {len(cpt_descriptions)} codes")
    print(f"   - NCCI Results: {len(ncci_results)} codes")
    print(f"   - Device Codes: {len(device_codes)} devices")
    print(f"   - Payment Records: {len(payment_history['data'])} records")
    
    return assessment


def load_cached_final_assessment(target_cpt):
    """
    Load cached final assessment results
    
    Args:
        target_cpt: Target CPT code
        
    Returns:
        Dict with cached results, or None if not found
    """
    output_dir = f"output/services_findings/{target_cpt}"
    file_name = "final_assessment.json"
    file_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        print(f"✅ Loaded cached final assessment from {file_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        return cached_data
        
    except Exception as e:
        print(f"⚠️  Error loading cached final assessment: {str(e)}")
        return None


def save_final_assessment(target_cpt, assessment_data):
    """
    Save final assessment to cache
    
    Args:
        target_cpt: Target CPT code
        assessment_data: Assessment data dict to save
    """
    output_dir = f"output/services_findings/{target_cpt}"
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = "final_assessment.json"
    file_path = os.path.join(output_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(assessment_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved final assessment to {file_path}")
        
    except Exception as e:
        print(f"⚠️  Error saving final assessment: {str(e)}")


# Legacy report generation functions (kept for backward compatibility)

def create_excel_output(analysis_content, cpt_value):
    """
    Create Excel workbook from research analysis
    
    Args:
        analysis_content: Complete analysis text
        cpt_value: CPT code
        
    Returns:
        BytesIO buffer with Excel file
    """
    output_buffer = BytesIO()
    
    window_start, window_end = compute_audit_window()
    
    # Prepare data structure
    summary_data = {
        "Field": ["Report Date", "CPT Code", "Audit Window Start", "Audit Window End"],
        "Value": [dt.now().strftime("%Y-%m-%d %H:%M"), cpt_value, window_start, window_end]
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
    """
    Create PDF report from research analysis
    
    Args:
        analysis_content: Complete analysis text
        cpt_value: CPT code
        
    Returns:
        BytesIO buffer with PDF file
    """
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
    <b>Report Date:</b> {dt.now().strftime("%Y-%m-%d %H:%M")}<br/>
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
                # Regular content line - escape special characters for XML
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(safe_line, normal_style))
        else:
            story.append(Spacer(1, 0.05*inch))
    
    # Build PDF
    doc.build(story)
    
    output_buffer.seek(0)
    return output_buffer


def save_excel_to_file(excel_buffer, cpt_code, topic=None):
    """
    Save Excel buffer to file in output directory
    
    Args:
        excel_buffer: BytesIO buffer with Excel content
        cpt_code: CPT code for filename
        topic: Optional topic name for filename
        
    Returns:
        Full path to saved file
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
    topic_part = f"{topic.replace(' ', '_')}_" if topic else ""
    filename = f"apc_research_{topic_part}{cpt_code}_{timestamp}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(excel_buffer.getvalue())
    
    return filepath


def save_pdf_to_file(pdf_buffer, cpt_code, topic=None):
    """
    Save PDF buffer to file in output directory
    
    Args:
        pdf_buffer: BytesIO buffer with PDF content
        cpt_code: CPT code for filename
        topic: Optional topic name for filename
        
    Returns:
        Full path to saved file
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
    topic_part = f"{topic.replace(' ', '_')}_" if topic else ""
    filename = f"apc_research_{topic_part}{cpt_code}_{timestamp}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    return filepath
