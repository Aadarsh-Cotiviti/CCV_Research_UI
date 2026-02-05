"""
Device Code Analysis Service (Section 4)

This service handles medical device code (HCPCS) analysis and validation.
Designed as an independent agent for agentic workflow.
"""

import pandas as pd
import os
import json
import datetime
from pathlib import Path
from llm_wrapper import query_llm
from pydantic import BaseModel, ValidationError, TypeAdapter
from .utils import compute_audit_window
from services.common.device_utils import get_or_generate_device_description


def retrieve_knowledge(hcpcs_code, device_change_df=Path('data/preprocessed_device_code_change_tracking.csv')):
    """
    Retrieve HCPCS device code changes (new or changed codes) from local knowledge base.
    
    Args:
        hcpcs_code: HCPCS code
        device_change_df: Path to preprocessed device code change tracking CSV file
        
    Returns:
        Dict with knowledge base information, or None if not found
    """
    try:
        # Load preprocessed device code change tracking data
        df = pd.read_csv(device_change_df, parse_dates=['EffectiveDt', 'EndDt'])
        
        # Filter for the specific HCPCS code
        code_records = df[df['hcpcscode'] == hcpcs_code]
        
        # If no records found, return None
        if len(code_records) == 0:
            return None
        
        # Get the first record (most recent)
        record = code_records.iloc[0]
        change_type = record['ChangeType']
        
        # Validate that required description fields are not empty
        # If empty, return None to trigger LLM fallback
        if change_type == 'C':
            old_desc = record['OldDesc']
            new_desc = record['NewDesc']
            
            # For Changed codes, both OldDesc and NewDesc should be present
            if pd.isna(old_desc) or pd.isna(new_desc) or str(old_desc).strip() == '' or str(new_desc).strip() == '':
                print(f"⚠️  HCPCS {hcpcs_code} (ChangeType=C): Missing OldDesc or NewDesc, falling back to LLM")
                return None
            
            effective_date = record['EffectiveDt']
            end_date = record['EndDt']
            change_description = f'''For the HCPCS code {hcpcs_code}, the description has changed from {effective_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. The old description was: {old_desc}, and the new description is: {new_desc}.'''
            hcpcs_description = new_desc
            
        elif change_type == 'N':
            new_desc = record['NewDesc']
            
            # For New codes, NewDesc should be present
            if pd.isna(new_desc) or str(new_desc).strip() == '':
                print(f"⚠️  HCPCS {hcpcs_code} (ChangeType=N): Missing NewDesc, falling back to LLM")
                return None
            
            effective_date = record['EffectiveDt']
            end_date = record['EndDt']
            change_description = f'''The HCPCS code {hcpcs_code} is a new code effective from {effective_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. The description for this new code is: {new_desc}.'''
            hcpcs_description = new_desc
            
        elif change_type == 'R':
            old_desc = record['OldDesc']
            
            # For Reinstated codes, OldDesc should be present
            if pd.isna(old_desc) or str(old_desc).strip() == '':
                print(f"⚠️  HCPCS {hcpcs_code} (ChangeType=R): Missing OldDesc, falling back to LLM")
                return None
            
            effective_date = record['EffectiveDt']
            change_description = f'''The HCPCS code {hcpcs_code} was reinstated from {effective_date.strftime('%Y-%m-%d')}. The description is: {old_desc}.'''
            hcpcs_description = old_desc
            
        else:  # 'D' - Deleted
            old_desc = record['OldDesc']
            
            # For Deleted codes, OldDesc should be present
            if pd.isna(old_desc) or str(old_desc).strip() == '':
                print(f"⚠️  HCPCS {hcpcs_code} (ChangeType=D): Missing OldDesc, falling back to LLM")
                return None
            
            effective_date = record['EffectiveDt']
            change_description = f'''The HCPCS code {hcpcs_code} was deleted/discontinued from {effective_date.strftime('%Y-%m-%d')}. The previous description was: {old_desc}.'''
            hcpcs_description = old_desc

        knowledge = {
            "hcpcs_code": hcpcs_code,
            "hcpcs_description": hcpcs_description,
            "change_type": change_type,
            "change_description": change_description,
            "resource": "internal_kb"
        }
        return knowledge
    except Exception as e:
        print(f"⚠️  Error retrieving knowledge for {hcpcs_code}: {str(e)}")
        return None


def build_llm_completion_prompt_for_local_desc(local_desc_results):
    """Prompt LLM for Clinical Context and Potential Re-coding/Bundling for codes with local descriptions"""
    window_start, window_end = compute_audit_window()
    prompt = (
        "You are a certified medical coding specialist. For each HCPCS device code below, strictly return a JSON array, each element with keys 'hcpcs_code' and 'recoding_possibilities'.\n"
        "Example output:\n"
        "[\n  {\"hcpcs_code\": \"A4657\", \"recoding_possibilities\": \"1. ...\\n2. ...\"},\n  ...\n]\n"
        "For each code, 'recoding_possibilities' should include:\n"
        "  1. Alternative HCPCS/CPT codes, with brief explanation of WHEN and WHY each should be used (focus on usage scenarios and clinical context, do NOT repeat code descriptions).\n"
        "  2. All common bundling/unbundling scenarios with procedure codes (including payer-specific or modifier-related), with official policy reference if possible.\n"
        "  3. Any common coding errors, misuse, or documentation pitfalls for this device code.\n"
        f"\nAudit Window: {window_start} through {window_end}\n"
        "Codes: " + ', '.join([item['hcpcs_code'] for item in sorted(local_desc_results, key=lambda x: x['hcpcs_code'])]) + "\n"
        "Return ONLY valid JSON, no explanations, no markdown, no extra text."
    )
    return prompt


def get_related_device_codes_prompt(target_cpt):
    """Generate prompt to identify HCPCS device codes related to target CPT code"""
    window_start, window_end = compute_audit_window()
    
    return f"""
As a certified medical coding specialist, identify the TOP 5-10 MOST RELEVANT HCPCS device codes commonly associated with CPT code: {target_cpt}

Audit Window: {window_start} through {window_end}

List the most commonly used HCPCS device codes (A, C, E, J, L, Q, or V series) that are:
- Medical devices, equipment, implants, or supplies used with or during the procedure {target_cpt}
- May be separately billable alongside {target_cpt}
- Commonly paired or used together with this procedure

Focus on the MOST FREQUENT and CLINICALLY RELEVANT codes. Limit your response to a maximum of 10 codes.

Include codes that represent:
- Implantable devices (C-codes): pacemakers, stents, grafts, electrodes, etc.
- Durable medical equipment (E-codes): wheelchairs, walkers, oxygen equipment, etc.
- Prosthetics/Orthotics (L-codes): artificial limbs, braces, custom devices, etc.
- Medical/surgical supplies (A-codes): catheters, syringes, dressings, etc.
- Drugs/injections (J-codes): medications administered during the procedure
- Vision/hearing services (V-codes): glasses, hearing aids, etc.
- Dental procedures (D-codes): if applicable

Return ONLY a comma-separated list of HCPCS codes in STRICTLY ASCENDING ORDER, with no duplicates.
Maximum 10 codes. Prioritize the most commonly billed codes.

Example format: A4657, C1713, E0114

If CPT {target_cpt} does NOT typically involve any separately billable devices, supplies, or equipment, return: NONE

Do not include explanations or extra text—just the codes or "NONE".
"""



def build_llm_analysis_prompt(codes_without_kb):
    """Build final analysis prompt for codes without local description"""
    window_start, window_end = compute_audit_window()
    codes_with_no_desc = []
    
    for code in sorted(codes_without_kb):
        desc_info = get_or_generate_device_description(code, use_llm_fallback=False)
        if not desc_info['description']:
            codes_with_no_desc.append(code)
    
    if not codes_with_no_desc:
        return None
    
    codes_str = ', '.join(codes_with_no_desc)
    prompt = f"""
You are a certified medical coding specialist. For each HCPCS device code below, strictly return a JSON array, each element with keys 'hcpcs_code', 'description', and 'recoding_possibilities'.

Example output:
[
  {{
    "hcpcs_code": "A4657",
    "description": "Official HCPCS code description",
    "recoding_possibilities": "1. Alternative codes...\\n2. Bundling scenarios...\\n3. Common errors..."
  }},
  ...
]

For each code:
- 'hcpcs_code': The HCPCS code
- 'description': Official HCPCS code description (concise summary of the device/supply)
- 'recoding_possibilities' should include:
  1. Alternative HCPCS/CPT codes, with brief explanation of WHEN and WHY each should be used (focus on usage scenarios and clinical context, do NOT repeat code descriptions).
  2. All common bundling/unbundling scenarios with procedure codes (including payer-specific or modifier-related), with official policy reference if possible.
  3. Any common coding errors, misuse, or documentation pitfalls for this device code.

Audit Window: {window_start} through {window_end}

Codes: {codes_str}

Guidelines:
- Use only official HCPCS code descriptions and real clinical context (do not invent codes or scenarios).
- If a code is ambiguous or rarely used, state so explicitly.
- Output codes in STRICTLY ASCENDING ORDER.
- Return ONLY valid JSON, no explanations, no markdown, no extra text.
    """
    return prompt


def load_cached_results(target_cpt):
    """
    Load previously saved analysis results from cache
    
    Args:
        target_cpt: Target CPT code
        
    Returns:
        Dict with cached results, or None if not found
    """
    output_dir = f"output/services_findings/{target_cpt}"
    file_name = "section_4_results.json"
    output_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(output_path):
        return None
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Extract the analysis results (excluding metadata)
        result = {
            "device_codes_with_desc": cached_data.get("device_codes_with_desc", []),
            "internal_recoding_result": cached_data.get("internal_recoding_result", []),
            "internal_llm_recoding_result": cached_data.get("internal_llm_recoding_result", []),
            "external_full_llm_result": cached_data.get("external_full_llm_result", [])
        }
        
        print(f"✅ Loaded cached results from {output_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error loading cached results: {str(e)}")
        return None


def analyze_device_code_analysis(target_cpt, device_codes=None, model="gpt-4.1-mini", use_cache=True):
    """
    Analyze HCPCS device codes related to target CPT code
    
    Workflow:
    1. Check cache for existing results (if use_cache=True)
    2. If device_codes not provided, use LLM to identify relevant device codes
    3. Check knowledge base for device code changes
    4. Use LLM for codes not in knowledge base
    
    Args:
        target_cpt: Target CPT code to analyze
        device_codes: List of HCPCS device codes to analyze (optional - if not provided, LLM will identify them)
        model: LLM model to use
        use_cache: If True, check for and use cached results (default: True)
        
    Returns:
        Dict with analysis results and metadata
    """
    print(f"\n🔍 Starting Device Code Analysis for CPT code: {target_cpt}")
    
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
        # Step 1: Identify device codes if not provided
        if device_codes is None or len(device_codes) == 0:
            print("\nStep 1: Identifying related device codes using LLM...")
            device_codes_prompt = get_related_device_codes_prompt(target_cpt)
            messages = [
                {"role": "system", "content": "You are an expert medical coding analyst."},
                {"role": "user", "content": device_codes_prompt}
            ]
            device_codes_result = query_llm(messages, model=model)
            
            # Parse result
            if device_codes_result.strip().upper() == "NONE":
                print(f"✅ LLM determined that CPT {target_cpt} does not involve separately billable device codes")
                device_codes = []
            else:
                try:
                    device_codes = [code.strip() for code in device_codes_result.strip().split(',') if code.strip()]
                    print(f"✅ LLM identified device codes: {', '.join(device_codes)}")
                except Exception as e:
                    print(f"⚠️  Could not parse device codes from LLM, using empty list: {str(e)}")
                    device_codes = []
        else:
            print(f"\n📋 Using provided device codes: {', '.join(device_codes)}")
        
        if not device_codes:
            print("⚠️  No device codes to analyze, returning empty results")
            empty_result = {
                "device_codes_with_desc": [],
                "internal_recoding_result": [],
                "no_change_results": [],
                "internal_llm_recoding_result": [],
                "external_full_llm_result": []
            }
            
            # Save empty result to cache
            output_dir = f"output/services_findings/{target_cpt}"
            os.makedirs(output_dir, exist_ok=True)
            
            file_name = "section_4_results.json"
            output_path = os.path.join(output_dir, file_name)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "service": "section 4 - device code analysis",
                    "update_time": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "target_cpt": target_cpt,
                    **empty_result
                }, f, indent=2, ensure_ascii=False)
            
            print(f"[Saved empty results to {output_path}]")
            
            return empty_result
        
        # Step 2: Get descriptions for all device codes (local first, then LLM if needed)
        print("\nStep 2: Getting descriptions for device codes...")
        device_codes_with_desc = []
        
        for code in device_codes:
            desc_info = get_or_generate_device_description(code, model=model, use_llm_fallback=True)
            device_codes_with_desc.append(desc_info)
            print(f"  {code}: {desc_info['description'][:80] if desc_info['description'] else 'N/A'}... [source: {desc_info['source']}]")
        
        # Sort by HCPCS code to maintain ascending order
        device_codes_with_desc = sorted(device_codes_with_desc, key=lambda x: x['hcpcs_code'])
        
        # Step 3: Check knowledge base for device code changes
        print("\nStep 3: Checking internal knowledge base for device code changes...")
        kb_results = []
        codes_without_kb = []
        
        for code in device_codes:
            knowledge = retrieve_knowledge(code)
            if knowledge:
                kb_results.append(knowledge)
                print(f"✅ Found in KB: {code}")
            else:
                codes_without_kb.append(code)
                print(f"❌ Not in KB: {code}")
        
        print(f"\n📊 Knowledge base results: {len(kb_results)} codes found")
        print(f"📊 Codes without changes since 2024: {len(codes_without_kb)}")
        
        # Step 4: For codes not in the change tracking KB, return standardized message
        no_change_results = []
        if codes_without_kb:
            no_change_message = "No changes to device code descriptions since 2024."
            for code in codes_without_kb:
                desc = get_or_generate_device_description(code, model=model, use_llm_fallback=False)
                no_change_results.append({
                    "hcpcs_code": code,
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
        file_name = "section_4_results.json"
        output_path = os.path.join(output_dir, file_name)
        result_obj = {
            "service": "section 4 - device code analysis",
            "update_time": dt_str,
            "target_cpt": target_cpt,
            "device_codes_with_desc": device_codes_with_desc,
            "internal_recoding_result": kb_results,
            "no_change_results": no_change_results
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, ensure_ascii=False, indent=2)
        print(f"[Saved findings to {output_path}]")
        
        return {
            "device_codes_with_desc": device_codes_with_desc,
            "internal_recoding_result": kb_results,
            "no_change_results": no_change_results,
            "internal_llm_recoding_result": [],
            "external_full_llm_result": []
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "device_codes_with_desc": [],
            "internal_recoding_result": [],
            "no_change_results": [],
            "internal_llm_recoding_result": [],
            "external_full_llm_result": []
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 4,
        "section_id": "section_4",
        "title": "Device Code Analysis",
        "description": "Analyze HCPCS device codes related to procedures",
        "agent_function": "analyze_device_code_analysis"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the complete agent workflow for Section 4"""
    test_cpt = "97810"
    
    print(f"📋 CPT Code: {test_cpt}\n")

    result1 = analyze_device_code_analysis(test_cpt, device_codes=None, model="gpt-4.1-mini", use_cache=False)
    print("\n" + "="*80)
    print("ANALYSIS RESULTS (Auto-identified)")
    print("="*80)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    


