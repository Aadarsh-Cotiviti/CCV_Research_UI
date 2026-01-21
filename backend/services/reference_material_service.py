"""
Reference Material Review Service (Section 6)

This service handles review of coding references and guidance materials.
Designed as an independent agent for agentic workflow.
"""

import os
import json
import datetime
import re
from llm_wrapper import query_llm
from .utils import compute_audit_window
from services.common import get_or_generate_cpt_description


def build_reference_material_prompt(target_cpt):
    """
    Build prompt for additional reference material review
    
    Args:
        target_cpt: Target CPT code to analyze
        
    Returns:
        Formatted prompt string for LLM
    """
    window_start, window_end = compute_audit_window()
    
    prompt = f"""
Analyze CPT {target_cpt} coding guidelines (Audit Window: {window_start} - {window_end}).

Focus on code relationships, restrictions, and usage rules. Do NOT give the description of any CPT code.

Provide structured analysis:

**Summary**: Key coding requirements, major restrictions, critical compliance points

- Locate CPT Assistant guidance for {target_cpt}
- Find applicable HCPCS Coding Clinic articles
- Document special coding considerations
- Identify relevant policy updates
- Note professional society guidelines

Format: Section headers with bullet points. Always include CPT code numbers (e.g., CPT 12345).
Do not include introductory/concluding remarks or code descriptions. Start directly with section 1.
"""
    return prompt


def extract_cpt_codes_from_text(text):
    """
    Extract all CPT codes mentioned in the analysis text
    
    Args:
        text: Analysis text containing CPT code references
        
    Returns:
        List of unique CPT codes found in the text
    """
    # Pattern to match CPT codes (5 digits, often preceded by "CPT")
    pattern = r'\b(?:CPT\s+)?(\d{5})\b'
    matches = re.findall(pattern, text)
    
    # Return unique codes, sorted
    unique_codes = sorted(set(matches))
    return unique_codes


def get_cpt_descriptions_for_analysis(analysis_text, target_cpt, model="gpt-4.1-mini"):
    """
    Extract CPT codes from analysis and get their descriptions
    
    Args:
        analysis_text: LLM analysis text
        target_cpt: Target CPT code
        model: LLM model for fallback descriptions
        
    Returns:
        Dict mapping CPT codes to their description info
    """
    # Extract all CPT codes mentioned in the analysis
    cpt_codes = extract_cpt_codes_from_text(analysis_text)
    
    # Always include target CPT
    if target_cpt not in cpt_codes:
        cpt_codes.insert(0, target_cpt)
    
    # Get descriptions for all codes
    code_descriptions = {}
    print(f"\n📋 Extracting descriptions for {len(cpt_codes)} CPT codes...")
    
    for code in cpt_codes:
        desc_info = get_or_generate_cpt_description(code, model=model, use_llm_fallback=True)
        code_descriptions[code] = desc_info
        print(f"  {code}: {desc_info['description'][:60]}... [source: {desc_info['source']}]")
    
    return code_descriptions


def load_cached_results(target_cpt):
    """
    Load previously saved analysis results from cache
    
    Args:
        target_cpt: Target CPT code
        
    Returns:
        Dict with cached results, or None if not found
    """
    output_dir = f"output/services_findings/{target_cpt}"
    file_name = "section_6_results.json"
    output_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(output_path):
        return None
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Extract the analysis results
        result = {
            "analysis_content": cached_data.get("analysis_content", ""),
            "cpt_descriptions": cached_data.get("cpt_descriptions", {}),
            "source": cached_data.get("source", "llm")
        }
        
        print(f"✅ Loaded cached results from {output_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error loading cached results: {str(e)}")
        return None


def analyze_reference_material_review(target_cpt, model="gpt-4.1-mini", use_cache=True):
    """
    Perform comprehensive additional reference material review for the target CPT code
    
    Args:
        target_cpt: Target CPT code to analyze
        model: LLM model to use
        use_cache: If True, check for and use cached results (default: True)
        
    Returns:
        Dict with analysis results
    """
    print(f"\n🔍 Starting additional reference material review for CPT code: {target_cpt}")
    
    # Check cache first if enabled
    if use_cache:
        print("\n📦 Checking cache for existing results...")
        cached_results = load_cached_results(target_cpt)
        if cached_results is not None:
            print("✅ Using cached results (set use_cache=False to force re-analysis)")
            return cached_results
        else:
            print("❌ No cached results found, running fresh analysis...")
    
    try:
        # Build prompt and query LLM
        print("\nGenerating additional reference material review analysis...")
        prompt = build_reference_material_prompt(target_cpt)
        
        messages = [
            {"role": "system", "content": "You are an expert medical coding specialist with deep knowledge of CPT guidelines and coding regulations."},
            {"role": "user", "content": prompt}
        ]
        
        analysis_result = query_llm(messages, model=model)
        print(f"✅ Analysis completed")
        
        # Extract CPT codes and get their descriptions
        cpt_descriptions = get_cpt_descriptions_for_analysis(analysis_result, target_cpt, model)
        
        # Save findings to JSON file
        output_dir = f"output/services_findings/{target_cpt}"
        os.makedirs(output_dir, exist_ok=True)
        dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = "section_6_results.json"
        output_path = os.path.join(output_dir, file_name)
        
        result_obj = {
            "service": "section 6 - reference material review",
            "update_time": dt_str,
            "cpt_code": target_cpt,
            "analysis_content": analysis_result,
            "cpt_descriptions": cpt_descriptions,
            "source": "llm"
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, ensure_ascii=False, indent=2)
        print(f"[Saved findings to {output_path}]")
        
        return {
            "analysis_content": analysis_result,
            "cpt_descriptions": cpt_descriptions,
            "source": "llm"
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "content": None,
            "error": str(e),
            "section_id": "section_6",
            "section_title": "Reference Material Review"
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 6,
        "section_id": "section_6",
        "title": "Reference Material Review",
        "description": "Extract and summarize coding guidelines and instructional notes",
        "agent_function": "analyze_reference_material_review"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the reference material review workflow"""
    test_cpt = "97810"
    
    print(f"📋 CPT Code: {test_cpt}\n")
    
    result = analyze_reference_material_review(test_cpt, model="gpt-4.1-mini", use_cache=False)








from .utils import compute_audit_window


def build_section_prompt(target_cpt, context_details=""):
    """
    Build prompt for Reference Material Review section
    
    Args:
        target_cpt: Target CPT code to analyze
        context_details: Additional context information
        
    Returns:
        Formatted prompt string
    """
    window_start, window_end = compute_audit_window()
    
    prompt = f"""
As a medical coding specialist focused on APC analysis, perform Reference Material Review for CPT code: {target_cpt}

Audit Window: {window_start} through {window_end}
Context: {context_details or "Not specified"}

<SECTION_6>
<TITLE>Reference Material Review</TITLE>
<CONTENT>
- Locate CPT Assistant guidance for {target_cpt}
- Find applicable HCPCS Coding Clinic articles
- Document special coding considerations
- Identify relevant policy updates
- Note professional society guidelines
</CONTENT>
</SECTION_6>

CRITICAL: Use the exact XML-style tags shown above. Place your analysis inside the <CONTENT> tags.
Use markdown formatting within the content sections.
"""
    return prompt


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 6,
        "section_id": "section_6",
        "title": "Reference Material Review",
        "description": "Review coding references and guidance materials"
    }
