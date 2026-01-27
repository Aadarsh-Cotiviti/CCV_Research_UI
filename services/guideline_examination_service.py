"""
Guideline Examination Service (Section 2)

This service handles examination of coding guidelines and instructional notes.
Designed as an independent agent for agentic workflow.
"""

import os
import json
import datetime
import re
from llm_wrapper import query_llm
from .utils import compute_audit_window
from services.common import get_or_generate_cpt_description


def build_guideline_examination_prompt(target_cpt):
    """
    Build prompt for comprehensive guideline examination
    
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

1. **Summary**: Key coding requirements, major restrictions, critical compliance points

2. **Instructional Notes**: 
   - "Do not report with" restrictions (list specific CPT codes)
   - "Use with" requirements (list specific CPT codes)
   - Bundling rules and code relationships

3. **Chapter Guidelines**: CPT chapter rules, section-specific requirements, category reporting instructions

4. **Coding Rules**: Frequency limits, bilateral/unilateral rules, age/diagnosis restrictions, modifier requirements

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
    file_name = "section_2_results.json"
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


def analyze_guideline_examination(target_cpt, model="gpt-4.1-mini", use_cache=True):
    """
    Perform comprehensive guideline examination for the target CPT code
    
    Args:
        target_cpt: Target CPT code to analyze
        model: LLM model to use
        use_cache: If True, check for and use cached results (default: True)
        
    Returns:
        Dict with analysis results
    """
    print(f"\n🔍 Starting guideline examination for CPT code: {target_cpt}")
    
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
        print("\nGenerating guideline examination analysis...")
        prompt = build_guideline_examination_prompt(target_cpt)
        
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
        file_name = "section_2_results.json"
        output_path = os.path.join(output_dir, file_name)
        
        result_obj = {
            "service": "section 2 - guideline examination",
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
            "section_id": "section_2",
            "section_title": "Guideline Examination"
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 2,
        "section_id": "section_2",
        "title": "Guideline Examination",
        "description": "Extract and summarize coding guidelines and instructional notes",
        "agent_function": "analyze_guideline_examination"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the guideline examination workflow"""
    test_cpt = "97810"
    
    print(f"📋 CPT Code: {test_cpt}\n")
    
    result = analyze_guideline_examination(test_cpt, model="gpt-4.1-mini", use_cache=False)
    
    if result and "analysis_content" in result:
        print("\n" + "="*80)
        print("GUIDELINE EXAMINATION RESULTS:")
        print("="*80)
        print(result["analysis_content"])
