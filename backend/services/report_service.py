"""
Report Generation Service

This module handles PDF and Excel report generation.
Reports are saved to the output/ directory.
"""

import os
from datetime import datetime
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
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic_part = f"{topic.replace(' ', '_')}_" if topic else ""
    filename = f"apc_research_{topic_part}{cpt_code}_{timestamp}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    return filepath
