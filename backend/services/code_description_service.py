
# python -m services.code_description_service
"""
Code Description Analysis Service (Section 1)

This service analyzes CPT code descriptions and neighboring codes.
Designed as an independent agent capable of complete task execution.
"""

from pathlib import Path
import pandas as pd
import os, json, datetime
from llm_wrapper import query_llm
from pydantic import BaseModel, Field, ValidationError
from .utils import compute_audit_window
from services.common import get_or_generate_cpt_description

def retrieve_knowledge(cpt_code, cpt_change_df=Path('data/preprocessed_cpt_change_tracking.csv')):
    """
    Retrieve CPT code changes (new or changed codes) for the past 3 years from local knowledge base.
    
    Args:
        cpt_code: CPT code
        cpt_change_df: Path to preprocessed structured CPT change tracking CSV file
    Returns:
        Dict with knowledge base information, or None if not found
    """
    try:
        # Load preprocessed CPT change tracking data
        cpt_df = pd.read_csv(cpt_change_df, parse_dates=['EffectiveDt', 'EndDt'])
        
        # Convert cpt_code to int for comparison (CSV stores as int64)
        try:
            cpt_code_int = int(cpt_code)
        except (ValueError, TypeError):
            return None
        
        # Filter for the specific CPT code
        code_records = cpt_df[cpt_df['CPTCd'] == cpt_code_int]
        
        # If no records found, return None
        if len(code_records) == 0:
            return None
        
        # Get the first record (most recent)
        record = code_records.iloc[0]
        change_type = record['ChangeType']
        
        if change_type == 'C':
            cpt_old_desc = record['OldDesc']
            cpt_new_desc = record['NewDesc']
            effective_date = record['EffectiveDt']
            end_date = record['EndDt']
            cpt_change_description = f'''For the CPT code {cpt_code}, the description has changed from {effective_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. The old description was: {cpt_old_desc}, and the new description is: {cpt_new_desc}.'''
        else:
            cpt_new_desc = record['NewDesc']
            effective_date = record['EffectiveDt']
            end_date = record['EndDt']
            cpt_change_description = f'''The CPT code {cpt_code} is a new code effective from {effective_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. The description for this new code is: {cpt_new_desc}.'''

        knowledge = {
            "cpt_code": cpt_code,
            "cpt_description": cpt_new_desc,
            "change_type": change_type,
            "cpt_change_description": cpt_change_description,
            "resource": "internal_kb"
        }
        return knowledge
    except Exception as e:
        print(f"⚠️  Error retrieving knowledge for {cpt_code}: {str(e)}")
        return None


def get_neighboring_codes_prompt(target_cpt):
    """Generate prompt to identify neighboring CPT codes"""
    window_start, window_end = compute_audit_window()
    
    return f"""
As a certified medical coding specialist, identify the most relevant neighboring CPT codes for: {target_cpt}

Audit Window: {window_start} through {window_end}

Please provide a list of neighboring CPT codes that meet ALL the following criteria:
- Belong to the same official CPT chapter (section) and procedural/service category as {target_cpt}
- Have similar or closely related official CPT descriptions (procedure, technique, or clinical use)
- Are commonly used for the same or similar clinical scenarios, or may be confused, bundled, or cross-referenced with {target_cpt}
- Only include codes that are officially recognized in the current CPT code set (do not invent or infer codes)

Return ONLY a comma-separated list of CPT codes in STRICTLY ASCENDING ORDER, with no duplicates.
Example format: 97810, 97811, 97813, 97814

If there are fewer than 5 valid codes that meet the above criteria, return as many as exist.

Do not include any explanations, descriptions, or extra text—just the code numbers.
"""

def build_llm_completion_prompt_for_local_desc(local_desc_results):
    """Prompt LLM for Clinical Context and Potential Re-coding/Bundling"""
    window_start, window_end = compute_audit_window()
    prompt = (
        "You are a certified medical coding specialist. For each CPT code below, strictly return a JSON array, each element with keys 'cpt_code' and 'recoding_possibilities'.\n"
        "Example output:\n"
        "[\n  {\"cpt_code\": \"12345\", \"recoding_possibilities\": \"1. ...\\n2. ...\"},\n  ...\n]\n"
        "For each code, 'recoding_possibilities' should include:\n"
        "  1. Alternative CPT/HCPCS codes, with brief explanation of WHEN and WHY each should be used (focus on usage scenarios and clinical context, do NOT repeat code descriptions).\n"
        "  2. All common bundling/unbundling scenarios (including payer-specific or modifier-related), with official CPT or payer policy reference if possible.\n"
        "  3. Any common coding errors, misuse, or documentation pitfalls for this code.\n"
        f"\nAudit Window: {window_start} through {window_end}\n"
        "Codes: " + ', '.join([item['cpt_code'] for item in sorted(local_desc_results, key=lambda x: x['cpt_code'])]) + "\n"
        "Return ONLY valid JSON, no explanations, no markdown, no extra text."
    )
    return prompt

def build_llm_analysis_prompt(codes_without_kb):
    """Build final analysis prompt for codes without local description"""

    window_start, window_end = compute_audit_window()
    codes_with_no_desc = []
    for code in sorted(codes_without_kb):
        desc_info = get_or_generate_cpt_description(code, use_llm_fallback=False)
        if not desc_info['description']:
            codes_with_no_desc.append(code)
    if not codes_with_no_desc:
        return None
    codes_str = ', '.join(codes_with_no_desc)
    prompt = f"""
You are a certified medical coding specialist. For each CPT code below, strictly return a JSON array, each element with keys 'cpt_code', 'description', and 'recoding_possibilities'.

Example output:
[
  {{
    "cpt_code": "12345",
    "description": "Official CPT code description",
    "recoding_possibilities": "1. Alternative codes...\\n2. Bundling scenarios...\\n3. Common errors..."
  }},
  ...
]

For each code:
- 'cpt_code': The CPT code number
- 'description': Official CPT code description (concise summary of the procedure)
- 'recoding_possibilities' should include:
  1. Alternative CPT/HCPCS codes, with brief explanation of WHEN and WHY each should be used (focus on usage scenarios and clinical context, do NOT repeat code descriptions).
  2. All common bundling/unbundling scenarios (including payer-specific or modifier-related), with official CPT or payer policy reference if possible.
  3. Any common coding errors, misuse, or documentation pitfalls for this code.

Audit Window: {window_start} through {window_end}

Codes: {codes_str}

Guidelines:
- Use only official CPT code descriptions and real clinical context (do not invent codes or scenarios).
- If a code is ambiguous or rarely used, state so explicitly.
- Output codes in STRICTLY ASCENDING ORDER.
- Return ONLY valid JSON, no explanations, no markdown, no extra text.
    """
    return prompt



def get_cpt_description(code):
    """
    DEPRECATED: Use get_or_generate_cpt_description from services.common instead
    
    Get CPT code description from S3 parquet files or local cache
    """
    desc_info = get_or_generate_cpt_description(code, use_llm_fallback=False)
    return desc_info['description']


def load_cached_results(target_cpt):
    """
    Load previously saved analysis results from cache
    
    Args:
        target_cpt: Target CPT code
        
    Returns:
        Dict with cached results, or None if not found/expired
    """
    output_dir = f"output/services_findings/{target_cpt}"
    file_name = "section_1_results.json"
    output_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(output_path):
        return None
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Extract the analysis results (excluding metadata)
        result = {
            "neighbouring_codes": cached_data.get("neighbouring_codes", []),
            "internal_recoding_result": cached_data.get("internal_recoding_result", []),
            "internal_llm_recoding_result": cached_data.get("internal_llm_recoding_result", []),
            "external_full_llm_result": cached_data.get("external_full_llm_result", "")
        }
        
        print(f"✅ Loaded cached results from {output_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error loading cached results: {str(e)}")
        return None


def analyze_code_descriptions(target_cpt, model="gpt-4.1-mini", use_cache=True):
    """
    Two-stage analysis:
    1. Check cache for existing results (if use_cache=True)
    2. Use LLM to identify neighboring CPT codes
    3. Check knowledge base for all codes (target + neighbors)
    4. Use LLM for codes not in knowledge base
    
    Args:
        target_cpt: Target CPT code to analyze
        model: LLM model to use
        use_cache: If True, check for and use cached results (default: True)
        
    Returns:
        Dict with analysis results and metadata
    """
    print(f"\n🔍 Starting analysis for CPT code: {target_cpt}")
    
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
        # Step 1: Get neighboring codes from LLM
        print("\nStep 1: Identifying neighboring CPT codes...")
        neighboring_prompt = get_neighboring_codes_prompt(target_cpt)
        messages = [
            {"role": "system", "content": "You are an expert medical coding analyst."},
            {"role": "user", "content": neighboring_prompt}
        ]
        neighboring_codes_result = query_llm(messages, model=model)
        try:
            neighbouring_codes = [code.strip() for code in neighboring_codes_result.strip().split(',') if code.strip()]
            print(f"✅ Found neighboring codes: {', '.join(neighbouring_codes)}")
        except Exception as e:
            print(f"⚠️  Could not parse neighboring codes, using only target code: {str(e)}")
            neighbouring_codes = []
        
        # Remove target_cpt from neighbouring_codes if it's included, then create all_codes
        neighbouring_codes = [code for code in neighbouring_codes if code != target_cpt]
        all_codes = [target_cpt] + neighbouring_codes
        
        print(f"📋 Target CPT: {target_cpt}")
        print(f"📋 Neighboring CPT codes: {', '.join(neighbouring_codes) if neighbouring_codes else 'None'}")

        # Step 2: Check knowledge base for all codes
        print("\nStep 2: Checking internal knowledge base...")
        kb_results = []
        codes_without_kb = []
        
        # Get descriptions for target CPT and all neighboring codes (local first, then LLM if needed)
        neighbouring_codes_with_desc = []
        print("\nStep 1.5: Getting descriptions for target and neighboring codes...")
        
        # Get target CPT description
        target_desc_info = get_or_generate_cpt_description(target_cpt, model=model, use_llm_fallback=True)
        neighbouring_codes_with_desc.append(target_desc_info)
        print(f"  {target_cpt} (target): {target_desc_info['description'][:80]}... [source: {target_desc_info['source']}]")
        
        # Get neighboring codes descriptions
        for code in neighbouring_codes:
            desc_info = get_or_generate_cpt_description(code, model=model, use_llm_fallback=True)
            neighbouring_codes_with_desc.append(desc_info)
            print(f"  {code}: {desc_info['description'][:80]}... [source: {desc_info['source']}]")
        
        # Sort by CPT code to maintain ascending order
        neighbouring_codes_with_desc = sorted(neighbouring_codes_with_desc, key=lambda x: x['cpt_code'])
        
        for code in all_codes:
            knowledge = retrieve_knowledge(code)
            if knowledge:
                kb_results.append(knowledge)
                print(f"✅ Found in KB: {code}")
            else:
                codes_without_kb.append(code)
                print(f"❌ Not in KB: {code}")

        print(f"\n📊 Knowledge base results: {len(kb_results)} codes found")
        print(f"📊 Codes without changes since 2024: {len(codes_without_kb)}")

        # Step 3: For codes not in the change tracking KB, return standardized message
        no_change_results = []
        if codes_without_kb:
            no_change_message = "No changes to CPT code descriptions since 2024."
            for code in codes_without_kb:
                desc = get_or_generate_cpt_description(code, model=model, use_llm_fallback=False)
                no_change_results.append({
                    "cpt_code": code,
                    "description": desc["description"] if desc and desc["description"] else "Description not available",
                    "description_source": desc["source"] if desc else "unknown",
                    "status": no_change_message
                })
                print(f"  {code}: {no_change_message}")
        
        # Kept for backwards compatibility (empty lists)
        internal_llm_recoding_results = []
        external_full_llm_result = []

        # Save findings to JSON file
        output_dir = f"output/services_findings/{target_cpt}"
        os.makedirs(output_dir, exist_ok=True)
        dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = "section_1_results.json"
        output_path = os.path.join(output_dir, file_name)
        result_obj = {
            "service": "section 1 - code description analysis",
            "update_time": dt_str,
            "neighbouring_codes": neighbouring_codes_with_desc,
            "internal_recoding_result": kb_results,
            "no_change_results": no_change_results
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, ensure_ascii=False, indent=2)
        print(f"[Saved findings to {output_path}]")

        return {
            "neighbouring_codes": neighbouring_codes_with_desc,
            "internal_recoding_result": kb_results,
            "no_change_results": no_change_results,
            "internal_llm_recoding_result": [],
            "external_full_llm_result": []
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "content": None,
            "error": str(e),
            "section_id": "section_1",
            "section_title": "Code Description Analysis"
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 1,
        "section_id": "section_1",
        "title": "Code Description Analysis",
        "description": "Analyze CPT code descriptions, identify neighboring codes and their potential recoding/bundling scenarios.",
        "agent_function": "analyze_code_descriptions"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the complete agent workflow for Section 1"""
    test_cpt = "97810"
    
    print(f"📋 CPT Code: {test_cpt}\n")
    
    # Step 1: Test knowledge retrieval
    knowledge = retrieve_knowledge(test_cpt)

    # Step 2: Test complete agent workflow
    result = analyze_code_descriptions(test_cpt, model="gpt-4.1-mini")
        

    
   
