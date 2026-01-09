"""
NCCI Compliance Check Service (Section 5)

This service handles NCCI edits and modifier compliance analysis.
Designed as an independent agent for agentic workflow.
"""

from .utils import compute_audit_window


def build_section_prompt(target_cpt, context_details=""):
    """
    Build prompt for NCCI Compliance Check section
    
    Args:
        target_cpt: Target CPT code to analyze
        context_details: Additional context information
        
    Returns:
        Formatted prompt string
    """
    window_start, window_end = compute_audit_window()
    
    prompt = f"""
As a medical coding specialist focused on APC analysis, perform NCCI Compliance Check for CPT code: {target_cpt}

Audit Window: {window_start} through {window_end}
Context: {context_details or "Not specified"}

<SECTION_5>
<TITLE>NCCI Compliance Check</TITLE>
<CONTENT>
- Reference NCCI Edit Manual for {target_cpt}
- Examine PTP (Procedure-to-Procedure) edits
- Detect modifier abuse patterns:
  • Inappropriate modifier 59 usage
  • Modifier 25 misapplication
  • Other unbundling indicators
- Identify compliance risks
</CONTENT>
</SECTION_5>

CRITICAL: Use the exact XML-style tags shown above. Place your analysis inside the <CONTENT> tags.
Use markdown formatting within the content sections.
"""
    return prompt


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 5,
        "section_id": "section_5",
        "title": "NCCI Compliance Check",
        "description": "Check NCCI edits and modifier compliance"
    }
