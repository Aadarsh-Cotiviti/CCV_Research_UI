"""
APC Research Orchestrator

This module orchestrates the complete APC research workflow.

=== RECOMMENDED APPROACH (Agentic) ===
Each section runs independently with its own knowledge retrieval and analysis:
- conduct_section_research(section_num, target_cpt, ...) - Run a single section
- conduct_all_sections_research(target_cpt, ...) - Run all or selected sections

Each service (section) handles:
- Knowledge base retrieval (e.g., retrieve_knowledge() in code_description_service)
- LLM analysis with service-specific prompts
- Result formatting and storage

=== LEGACY APPROACH (Deprecated) ===
Single LLM call for all sections (will be removed in future versions):
- build_comprehensive_research_prompt() - [DEPRECATED]
- conduct_comprehensive_research() - [DEPRECATED]

Use the agentic approach for new development.
"""

import re
from llm_wrapper import query_llm
from .utils import compute_audit_window, replace_cpt_descriptions_in_text
from . import (
    code_description_service,
    guideline_examination_service,
    payment_rate_service,
    device_code_service,
    ncci_compliance_service,
    reference_material_service
)


# Registry of all section services
SECTION_SERVICES = {
    1: code_description_service,
    2: guideline_examination_service,
    3: payment_rate_service,
    4: device_code_service,
    5: ncci_compliance_service,
    6: reference_material_service
}


def build_comprehensive_research_prompt(target_cpt, context_details):
    """
    [DEPRECATED - Legacy Method] 
    Build comprehensive research prompt combining all sections in a single LLM call.
    
    This function is deprecated and will be removed in future versions.
    Use conduct_all_sections_research() instead for the new agentic approach where
    each section runs independently with its own knowledge retrieval.
    
    Args:
        target_cpt: Target CPT code
        context_details: Additional context
        
    Returns:
        Complete prompt string
    """
    window_start, window_end = compute_audit_window()
    
    research_query = f"""
As a medical coding specialist focused on APC analysis, perform a thorough evaluation for CPT code: {target_cpt}

Audit Window: {window_start} through {window_end}

Context Information: {context_details or "Not specified"}

Complete the following analysis sections. IMPORTANT: Use the exact XML-style delimiters shown below to structure your response:

<SECTION_1>
<TITLE>Code Description Analysis</TITLE>
<CONTENT>
- Review detailed descriptions for {target_cpt} and neighboring codes
- List neighboring codes in ASCENDING ORDER (from lowest to highest code number)
- Detect re-coding possibilities considering:
  • Procedural approach variations (open, percutaneous, laparoscopic)
  • Anatomical location differences
  • Intervention technique specifics
  • Potential bundling scenarios
</CONTENT>
</SECTION_1>

<SECTION_2>
<TITLE>Guideline Examination</TITLE>
<CONTENT>
- Extract instructional notes specific to {target_cpt}
- Summarize applicable chapter-level guidelines
- Note parenthetical references and code relationships
</CONTENT>
</SECTION_2>

<SECTION_3>
<TITLE>Payment Rate Comparison</TITLE>
<CONTENT>
- Evaluate APC assignments and payment rates for {target_cpt} and related codes
- Present the comparison in a TABLE format with the following columns:
  | CPT Code | APC Code | Payment Rate | Status | Notes |
- Categorize findings:
  • Matching rates → No audit opportunity
  • Differing rates → Investigate further
- Track rate consistency across quarters/years within audit window
- Flag potential underpayment or overpayment patterns
- Use markdown table format for clear presentation
</CONTENT>
</SECTION_3>

<SECTION_4>
<TITLE>Device Code Analysis</TITLE>
<CONTENT>
- Confirm if {target_cpt} involves medical devices
- List relevant HCPCS device codes
- Highlight common errors:
  • Procedure without device code
  • Device-procedure mismatch
  • Incorrect device type selection
</CONTENT>
</SECTION_4>

<SECTION_5>
<TITLE>NCCI Compliance Check</TITLE>
<CONTENT>
- Reference NCCI Edit Manual for {target_cpt}
- Examine PTP (Procedure-to-Procedure) edits
- Detect modifier abuse patterns:
  • Inappropriate modifier 59 usage
  • Modifier 25 misapplication
  • Other unbundling indicators
</CONTENT>
</SECTION_5>

<SECTION_6>
<TITLE>Reference Material Review</TITLE>
<CONTENT>
- Locate CPT Assistant guidance for {target_cpt}
- Find applicable HCPCS Coding Clinic articles
- Document special coding considerations
</CONTENT>
</SECTION_6>

<FINAL_ASSESSMENT>
<CONTENT>
- Consolidate findings and opportunities
- Assign priority level (Critical/Moderate/Low)
- Recommend validation steps
</CONTENT>
</FINAL_ASSESSMENT>

CRITICAL: Your response MUST use these exact XML-style tags (<SECTION_1>, <SECTION_2>, etc.) to delimit each section. Place your actual analysis content inside the <CONTENT> tags for each section. Use markdown formatting within the content sections, including tables where specified.
"""
    return research_query


def conduct_comprehensive_research(target_cpt, context_details, model="gpt-4.1-mini"):
    """
    [DEPRECATED - Legacy Method]
    Conduct comprehensive APC research using single LLM call for all sections.
    
    This function is deprecated and will be removed in future versions.
    Use conduct_all_sections_research() or conduct_section_research() instead
    for the new agentic approach where each section:
    - Runs independently
    - Has its own knowledge base retrieval
    - Performs specialized analysis
    
    Migration example:
        # Old way (deprecated):
        result = conduct_comprehensive_research(cpt, context, model)
        sections, final = parse_structured_research(result)
        
        # New way (recommended):
        results = conduct_all_sections_research(cpt, context, model)
        for section_key, section_data in results['sections'].items():
            if section_data['status'] == 'success':
                # Use section_data['data']
    
    Args:
        target_cpt: Target CPT code
        context_details: Additional context
        model: LLM model to use
        
    Returns:
        Complete analysis result string (with XML-style section delimiters)
    """
    prompt = build_comprehensive_research_prompt(target_cpt, context_details)
    
    messages = [
        {"role": "system", "content": "You are an expert medical coding analyst specializing in APC research."},
        {"role": "user", "content": prompt}
    ]
    
    analysis_result = query_llm(messages, model=model)
    return analysis_result


def conduct_section_research(section_num, target_cpt, context_details="", model="gpt-4.1-mini", use_cache=True):
    """
    Conduct research for a single section (for agentic workflow)
    Each service now handles its own complete analysis workflow including:
    - Knowledge base retrieval
    - LLM analysis
    - Result formatting and storage
    
    Args:
        section_num: Section number (1-6)
        target_cpt: Target CPT code
        context_details: Additional context
        model: LLM model to use
        use_cache: If True, use cached results when available (default: True)
        
    Returns:
        Section analysis result (format varies by service)
    """
    if section_num not in SECTION_SERVICES:
        raise ValueError(f"Invalid section number: {section_num}")
    
    service = SECTION_SERVICES[section_num]
    
    # Section 1 (Code Description) has its own complete analysis function
    if section_num == 1:
        # Call the dedicated analysis function with cache support
        result = service.analyze_code_descriptions(target_cpt, model=model, use_cache=use_cache)
        return result
    
    # For sections 2-6, use the prompt-based approach (can be upgraded later)
    else:
        prompt = service.build_section_prompt(target_cpt, context_details)
        
        messages = [
            {"role": "system", "content": "You are an expert medical coding analyst specializing in APC research."},
            {"role": "user", "content": prompt}
        ]
        
        result = query_llm(messages, model=model)
        return result


def conduct_all_sections_research(target_cpt, context_details="", model="gpt-4.1-mini", sections_to_run=None, use_cache=True):
    """
    Conduct research for all sections individually (agentic approach)
    Each service independently handles knowledge retrieval and analysis
    
    Args:
        target_cpt: Target CPT code
        context_details: Additional context
        model: LLM model to use
        sections_to_run: List of section numbers to run (default: all 1-6)
        use_cache: If True, use cached results when available (default: True)
        
    Returns:
        Dict with results for each section
    """
    if sections_to_run is None:
        sections_to_run = [1, 2, 3, 4, 5, 6]
    
    print(f"\n🔬 Starting comprehensive APC research for CPT: {target_cpt}")
    print(f"📋 Running sections: {sections_to_run}")
    print(f"💾 Cache enabled: {use_cache}")
    
    results = {}
    
    for section_num in sections_to_run:
        try:
            print(f"\n{'='*60}")
            print(f"🔍 Section {section_num}: {SECTION_SERVICES[section_num].get_section_metadata()['title']}")
            print(f"{'='*60}")
            
            section_result = conduct_section_research(
                section_num=section_num,
                target_cpt=target_cpt,
                context_details=context_details,
                model=model,
                use_cache=use_cache
            )
            
            results[f"section_{section_num}"] = {
                "section_num": section_num,
                "status": "success",
                "data": section_result
            }
            
            print(f"✅ Section {section_num} completed successfully")
            
        except Exception as e:
            print(f"❌ Section {section_num} failed: {str(e)}")
            results[f"section_{section_num}"] = {
                "section_num": section_num,
                "status": "error",
                "error": str(e)
            }
    
    print(f"\n{'='*60}")
    print(f"✅ All sections completed!")
    print(f"{'='*60}\n")
    
    return {
        "target_cpt": target_cpt,
        "context_details": context_details,
        "model": model,
        "sections": results
    }


def parse_structured_research(llm_response):
    """
    Parse LLM response with XML-style section delimiters
    Returns a list of sections with guaranteed 6 sections + final assessment
    
    Args:
        llm_response: Raw LLM response with XML tags
        
    Returns:
        Tuple of (sections_list, final_assessment_content)
    """
    sections = []
    
    # Parse each section (1-6)
    for i in range(1, 7):
        section_pattern = rf'<SECTION_{i}>(.*?)</SECTION_{i}>'
        match = re.search(section_pattern, llm_response, re.DOTALL)
        
        if match:
            section_content = match.group(1)
            
            # Extract title
            title_match = re.search(r'<TITLE>(.*?)</TITLE>', section_content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else f"Section {i}"
            
            # Extract content
            content_match = re.search(r'<CONTENT>(.*?)</CONTENT>', section_content, re.DOTALL)
            content = content_match.group(1).strip() if content_match else ""
            
            # For Section 1 and Section 3, replace CPT descriptions with xlsx descriptions
            if i in [1, 3]:
                content = replace_cpt_descriptions_in_text(content)
            
            sections.append({
                'num': str(i),
                'name': title,
                'title': f"SECTION {i} - {title}",
                'content': content
            })
        else:
            # If section not found, create placeholder
            sections.append({
                'num': str(i),
                'name': f"Section {i}",
                'title': f"SECTION {i} - Not Available",
                'content': "⚠️ This section was not generated in the response."
            })
    
    # Parse Final Assessment
    final_pattern = r'<FINAL_ASSESSMENT>(.*?)</FINAL_ASSESSMENT>'
    final_match = re.search(final_pattern, llm_response, re.DOTALL)
    
    if final_match:
        final_content_block = final_match.group(1)
        content_match = re.search(r'<CONTENT>(.*?)</CONTENT>', final_content_block, re.DOTALL)
        final_content = content_match.group(1).strip() if content_match else final_content_block.strip()
    else:
        final_content = "⚠️ Final assessment not available."
    
    return sections, final_content


def chat_with_section(section_content, cpt_code, user_question, chat_history=None, model="gpt-5"):
    """
    Chat with LLM about a specific section
    
    Args:
        section_content: The content of the current section/tab
        cpt_code: The CPT code being researched
        user_question: The user's question
        chat_history: Previous chat messages in this section
        model: The LLM model to use
    
    Returns:
        AI response string
    """
    context = f"""
You are assisting with APC (Ambulatory Payment Classification) research for CPT code: {cpt_code}

Here is the research content for this section:
---
{section_content}
---

The user has a follow-up question about this content. Please answer based on the research above and your medical coding expertise.
"""
    
    messages = [{"role": "system", "content": context}]
    
    # Add previous chat history if available
    if chat_history:
        for chat in chat_history:
            messages.append({"role": "user", "content": chat["user"]})
            messages.append({"role": "assistant", "content": chat["ai"]})
    
    # Add current question
    messages.append({"role": "user", "content": user_question})
    
    try:
        response = query_llm(messages, model=model)
        return response
    except Exception as e:
        return f"Error: {str(e)}"
