"""
Payment Rate Comparison Service (Section 3)

This service handles APC payment rate analysis and comparisons.
Designed as an independent agent for agentic workflow.
"""
import os
import json
import datetime
from .utils import compute_audit_window
from .common.apc_payment_comparison import get_apc_payment_history_with_exclusions
from .common.asc_payment_comparison import get_asc_payment_history_with_exclusions
from .common.pnpp_payment_comparison import get_pnpp_payment_history_with_exclusions
from .code_description_service import load_cached_results as load_section1_cache, get_neighboring_codes_prompt
from .common import get_or_generate_cpt_description
from llm_wrapper import query_llm


def get_neighboring_codes_from_llm(target_cpt, model="gpt-4o-mini"):
    """
    Generate neighboring codes using LLM when Section 1 cache is not available
    
    Args:
        target_cpt: Target CPT code
        model: LLM model to use
        
    Returns:
        List of neighboring CPT codes
    """
    print(f"🤖 Generating neighboring codes using LLM (Section 1 logic)...")
    
    try:
        # Use the same prompt from Section 1
        neighboring_prompt = get_neighboring_codes_prompt(target_cpt)
        messages = [
            {"role": "system", "content": "You are an expert medical coding analyst."},
            {"role": "user", "content": neighboring_prompt}
        ]
        
        neighboring_codes_result = query_llm(messages, model=model)
        
        # Parse the result
        neighboring_codes = [code.strip() for code in neighboring_codes_result.strip().split(',') if code.strip()]
        
        # Remove target_cpt if it's included
        neighboring_codes = [code for code in neighboring_codes if code != target_cpt]
        
        if neighboring_codes:
            print(f"✅ Generated {len(neighboring_codes)} neighboring codes: {', '.join(neighboring_codes)}")
        else:
            print("ℹ️  No neighboring codes generated")
        
        return neighboring_codes
        
    except Exception as e:
        print(f"⚠️  Error generating neighboring codes: {str(e)}")
        return []


def build_payment_rate_prompt(target_cpt, apc_payment_table_md, asc_payment_table_md, pnpp_payment_table_md, neighboring_codes=None):
    """
    Build prompt for Payment Rate Comparison analysis
    
    Args:
        target_cpt: Target CPT code to analyze
        apc_payment_table_md: APC payment history table in markdown format
        asc_payment_table_md: ASC payment history table in markdown format
        pnpp_payment_table_md: PNPP payment history table in markdown format
        neighboring_codes: List of neighboring CPT codes (optional)
        
    Returns:
        Formatted prompt string for LLM
    """
    window_start, window_end = compute_audit_window()
    
    codes_info = f"CPT {target_cpt}"
    if neighboring_codes and len(neighboring_codes) > 0:
        codes_info += f" and its neighboring codes ({', '.join(neighboring_codes)})"
    
    prompt = f"""
Analyze payment rate changes for {codes_info} (Audit Window: {window_start} - {window_end}).

Payment History Data (January data for each year):
APC:
{apc_payment_table_md}

ASC:
{asc_payment_table_md}

PNPP:
{pnpp_payment_table_md}

Provide structured analysis:

1. **Summary**: Key payment trends, significant changes, rate stability assessment
   - Primary focus on target CPT {target_cpt}
   - Compare with neighboring codes to identify patterns

2. **Payment Trends**: 
   - Identify rate increases/decreases over time for {target_cpt}
   - Compare rates with neighboring codes across years
   - Note any divergence in payment trends between related codes

3. **Anomalies & Changes**: Flag unusual patterns, sudden changes, inconsistencies
   - Different rate changes between related codes
   - Unexpected rate increases/decreases

4. **Audit Opportunities**:
   - Matching rates across periods → No action needed
   - Differing rates → Investigate billing discrepancies
   - Compare payment rates between {target_cpt} and neighboring codes for potential coding optimization
   - Underpayment/overpayment risk assessment

Format: Section headers with bullet points. Focus on actionable insights.
Do not include introductory/concluding remarks. Start directly with section 1.
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
    file_name = "section_3_results.json"
    output_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(output_path):
        return None
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Extract the analysis results
        result = {
            "analysis_content": cached_data.get("analysis_content", ""),
            "target_cpt_payment_history": cached_data.get("target_cpt_payment_history", {}),
            "cpt_descriptions": cached_data.get("cpt_descriptions", {}),
            "source": cached_data.get("source", "llm")
        }
        
        print(f"✅ Loaded cached results from {output_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error loading cached results: {str(e)}")
        return None


def analyze_payment_rate_comparison(target_cpt, model="gpt-4.1-mini", use_cache=True):
    """
    Analyze payment rate comparison for a given CPT code
    
    Args:
        target_cpt: Target CPT code to analyze
        model: LLM model to use for analysis
        use_cache: If True, check for and use cached results (default: True)
        exclusion_category: CMS exclusion category to check - 'APC', 'ASC', or 'PNPP' (default: 'APC')
        
    Returns:
        Dict with analysis results
    """
    print(f"\n💰 Starting payment rate comparison for CPT code: {target_cpt}")
    
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
        # Try to get neighboring codes from Section 1 cache
        print("\n🔍 Checking Section 1 cache for neighboring codes...")
        section1_data = load_section1_cache(target_cpt)
        neighboring_codes = []
        
        if section1_data and "neighbouring_codes" in section1_data:
            # Extract just the CPT codes from neighbouring_codes
            neighboring_codes = [item['cpt_code'] for item in section1_data['neighbouring_codes'] if item['cpt_code'] != target_cpt]
            if neighboring_codes:
                print(f"✅ Found {len(neighboring_codes)} neighboring codes from Section 1 cache: {', '.join(neighboring_codes)}")
            else:
                print("ℹ️  No neighboring codes found in cache (only target code)")
        else:
            # Section 1 cache not available, generate neighboring codes using LLM
            print("ℹ️  Section 1 cache not available, generating neighboring codes...")
            neighboring_codes = get_neighboring_codes_from_llm(target_cpt, model=model)
        
        # Get payment history from local knowledge base (with exclusions filtering)
        print("\n📊 Retrieving payment history from local knowledge base...")
        
        # Include neighboring codes if available
        all_codes = [target_cpt] + neighboring_codes
        
        # Get payment history with exclusions already filtered
        apc_payment_data = get_apc_payment_history_with_exclusions(
                cpt_codes=all_codes,
                exclusion_category='APC',
                january_only=True
            )
        
        asc_payment_data = get_asc_payment_history_with_exclusions(
                cpt_codes=all_codes,
                exclusion_category='ASC',
                january_only=True
            )
        
        pnpp_payment_data = get_pnpp_payment_history_with_exclusions(
                cpt_codes=all_codes,
                exclusion_category='PNPP',
                january_only=True
            )

        if apc_payment_data['record_count'] == 0:
            print(f"⚠️  No payment data found for CPT {target_cpt}")
            return {
                "success": False,
                "error": f"No payment data found for CPT {target_cpt}",
                "section_id": "section_3",
                "section_title": "Payment Rate Comparison"
            }
        
        # Extract data from payment_data dict
        apc_payment_history_filtered_df = apc_payment_data['data_filtered_df']
        apc_exclusions_info = apc_payment_data['exclusions']
        apc_excluded_cpt_codes = apc_payment_data['excluded_cpt_codes']
        asc_payment_history_filtered_df = asc_payment_data['data_filtered_df']
        asc_exclusions_info = asc_payment_data['exclusions']
        asc_excluded_cpt_codes = asc_payment_data['excluded_cpt_codes']
        pnpp_payment_history_filtered_df = pnpp_payment_data['data_filtered_df']
        pnpp_exclusions_info = pnpp_payment_data['exclusions']
        pnpp_excluded_cpt_codes = pnpp_payment_data['excluded_cpt_codes']
        
        # Build result dict with source metadata for all three payment types
        payment_history_dict = {
            "apc": {
                "data": apc_payment_data['data'],
                "data_filtered": apc_payment_data['data_filtered'],
                "data_filtered_df": apc_payment_history_filtered_df,
                "exclusions": apc_exclusions_info,
                "excluded_cpt_codes": apc_excluded_cpt_codes,
                "record_count": apc_payment_data['record_count'],
                "record_count_filtered": apc_payment_data['record_count_filtered']
            },
            "asc": {
                "data": asc_payment_data['data'],
                "data_filtered": asc_payment_data['data_filtered'],
                "data_filtered_df": asc_payment_history_filtered_df,
                "exclusions": asc_exclusions_info,
                "excluded_cpt_codes": asc_excluded_cpt_codes,
                "record_count": asc_payment_data['record_count'],
                "record_count_filtered": asc_payment_data['record_count_filtered']
            },
            "pnpp": {
                "data": pnpp_payment_data['data'],
                "data_filtered": pnpp_payment_data['data_filtered'],
                "data_filtered_df": pnpp_payment_history_filtered_df,
                "exclusions": pnpp_exclusions_info,
                "excluded_cpt_codes": pnpp_excluded_cpt_codes,
                "record_count": pnpp_payment_data['record_count'],
                "record_count_filtered": pnpp_payment_data['record_count_filtered']
            },
            "source": "local_kb",
            "cpt_codes_analyzed": all_codes,
            "neighboring_codes": neighboring_codes
        }
        
        # Extract all unique CPT codes from payment tables and get descriptions
        print("\n📋 Extracting CPT code descriptions...")
        all_cpt_codes_in_tables = set()
        
        # Extract from APC table
        if not apc_payment_history_filtered_df.empty and 'HCPCS Code' in apc_payment_history_filtered_df.columns:
            all_cpt_codes_in_tables.update(apc_payment_history_filtered_df['HCPCS Code'].astype(str).unique())
        
        # Extract from ASC table
        if not asc_payment_history_filtered_df.empty and 'HCPCS Code' in asc_payment_history_filtered_df.columns:
            all_cpt_codes_in_tables.update(asc_payment_history_filtered_df['HCPCS Code'].astype(str).unique())
        
        # Extract from PNPP table
        if not pnpp_payment_history_filtered_df.empty and 'HCPCS' in pnpp_payment_history_filtered_df.columns:
            all_cpt_codes_in_tables.update(pnpp_payment_history_filtered_df['HCPCS'].astype(str).unique())
        
        # Get descriptions for all codes
        cpt_descriptions = {}
        for code in sorted(all_cpt_codes_in_tables):
            desc_info = get_or_generate_cpt_description(code, model=model, use_llm_fallback=True)
            cpt_descriptions[code] = desc_info
            source_marker = "🟢" if desc_info['source'] == 'internal_kb' else "⚫"
            print(f"  {source_marker} {code}: {desc_info['description'][:60]}... [source: {desc_info['source']}]")
        
        print(f"✅ Retrieved descriptions for {len(cpt_descriptions)} CPT codes")
        
        # Convert filtered data to markdown for LLM prompt
        apc_payment_table_md = apc_payment_history_filtered_df.to_markdown(index=False)
        asc_payment_table_md = asc_payment_history_filtered_df.to_markdown(index=False)
        pnpp_payment_table_md = pnpp_payment_history_filtered_df.to_markdown(index=False)

        # Build prompt and query LLM
        print("\nGenerating payment rate analysis...")
        prompt = build_payment_rate_prompt(target_cpt, apc_payment_table_md, 
                                           asc_payment_table_md, pnpp_payment_table_md, 
                                           neighboring_codes)
        
        messages = [
            {"role": "system", "content": "You are an expert medical billing analyst specializing in APC payment rate analysis and audit opportunities."},
            {"role": "user", "content": prompt}
        ]
        
        analysis_result = query_llm(messages, model=model)
        print(f"✅ Analysis completed")
        
        # Save findings to JSON file
        output_dir = f"output/services_findings/{target_cpt}"
        os.makedirs(output_dir, exist_ok=True)
        dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = "section_3_results.json"
        output_path = os.path.join(output_dir, file_name)
        
        # Create JSON-safe version (remove DataFrames)
        payment_history_json = {}
        for payment_type in ['apc', 'asc', 'pnpp']:
            payment_history_json[payment_type] = {
                k: v for k, v in payment_history_dict[payment_type].items() 
                if k != 'data_filtered_df'
            }
        payment_history_json['source'] = payment_history_dict['source']
        payment_history_json['cpt_codes_analyzed'] = payment_history_dict['cpt_codes_analyzed']
        payment_history_json['neighboring_codes'] = payment_history_dict['neighboring_codes']
        
        result_obj = {
            "service": "section 3 - payment rate comparison",
            "update_time": dt_str,
            "cpt_code": target_cpt,
            "target_cpt_payment_history": payment_history_json,
            "cpt_descriptions": cpt_descriptions,
            "analysis_content": analysis_result,
            "source": "llm"
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, ensure_ascii=False, indent=2)
        print(f"[Saved findings to {output_path}]")
        
        return {
            "analysis_content": analysis_result,
            "target_cpt_payment_history": payment_history_dict,
            "cpt_descriptions": cpt_descriptions,
            "source": "llm"
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "content": None,
            "error": str(e),
            "section_id": "section_3",
            "section_title": "Payment Rate Comparison"
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 3,
        "section_id": "section_3",
        "title": "Payment Rate Comparison",
        "description": "Analyze and compare APC payment rates"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the payment rate comparison workflow"""
    test_codes = ['11042', '15150', '97810', '14301', '52234']
    
    result = analyze_payment_rate_comparison(test_codes, model="gpt-4.1-mini", use_cache=False)
    
    if result and "analysis_content" in result:
        print("\n" + "="*80)
        print("PAYMENT RATE COMPARISON RESULTS:")
        print("="*80)
        print(result["analysis_content"])
