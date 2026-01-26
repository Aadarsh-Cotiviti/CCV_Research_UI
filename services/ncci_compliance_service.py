"""
NCCI Compliance Check Service (Section 5)

This service handles NCCI edits and modifier compliance analysis.
Designed as an independent agent for agentic workflow.
"""
import os
import sys
import json
import datetime
import pandas as pd
from pathlib import Path
from .utils import compute_audit_window
from llm_wrapper import query_llm
from services.data_preprocessing.ptp_table_preprocessing import download_ptp_table_from_s3, clean_column_names, subset_save_df
from services.code_description_service import load_cached_results as load_section1_cache, get_neighboring_codes_prompt
from services.common import get_or_generate_cpt_description

# Add project root and ncci_rag/src to path for ncci_rag import
project_root = Path(__file__).parent.parent
ncci_rag_src = project_root / "ncci_rag" / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(ncci_rag_src) not in sys.path:
    sys.path.insert(0, str(ncci_rag_src))

from ncci_rag.src.llm_extract import ncci_llm_analysis




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


def filter_ptp_tables_by_cpts(cpt_codes):
    """
    Load PTP edit tables (Modifier 0 and Modifier 1) from preprocessed files and filter by multiple CPT codes.
    Returns both tables separately for each CPT code.
    
    Args:
        cpt_codes: List of CPT codes to filter (target + neighboring codes)
        
    Returns:
        Dict with keys being CPT codes, values containing:
        - modifier_0: {record_count, dataframe} or None if no data
        - modifier_1: {record_count, dataframe} or None if no data
        - source: "local_kb"
        - has_data: boolean indicating if this CPT has any PTP edits
        Note: 'data' is only created when saving to JSON
    """
    print(f"\n📊 Loading and filtering PTP Edit Tables for {len(cpt_codes)} CPT code(s)...")
    
    modifier_0_path = "output/preprocessed_ptp_edit_table_modifier0.csv"
    modifier_1_path = "output/preprocessed_ptp_edit_table_modifier1.csv"
    
    results = {}
    
    try:
        # Load the full tables once
        df_mod0 = None
        df_mod1 = None
        
        if os.path.exists(modifier_0_path):
            df_mod0 = pd.read_csv(modifier_0_path)
            # Convert CPT code columns to string for consistent comparison
            df_mod0['CPT_code_1'] = df_mod0['CPT_code_1'].astype(str)
            df_mod0['CPT_code_2'] = df_mod0['CPT_code_2'].astype(str)
        else:
            print(f"   ⚠️  Modifier 0 file not found, attempting to download...")
            df = download_ptp_table_from_s3()
            df_cleaned = clean_column_names(df)
            subset_save_df(df_cleaned)
            if os.path.exists(modifier_0_path):
                df_mod0 = pd.read_csv(modifier_0_path)
                df_mod0['CPT_code_1'] = df_mod0['CPT_code_1'].astype(str)
                df_mod0['CPT_code_2'] = df_mod0['CPT_code_2'].astype(str)
        
        if os.path.exists(modifier_1_path):
            df_mod1 = pd.read_csv(modifier_1_path)
            # Convert CPT code columns to string for consistent comparison
            df_mod1['CPT_code_1'] = df_mod1['CPT_code_1'].astype(str)
            df_mod1['CPT_code_2'] = df_mod1['CPT_code_2'].astype(str)
        else:
            print(f"   ⚠️  Modifier 1 file not found (should have been created with Modifier 0 preprocessing)")
        
        # Filter for each CPT code
        for cpt_code in cpt_codes:
            print(f"\n   🔍 Filtering for CPT {cpt_code}...")
            
            # Ensure cpt_code is string for comparison
            cpt_code = str(cpt_code)
            
            result = {
                "modifier_0": None,  # All Modifier 0 edits (Code 1 + Code 2 combined)
                "modifier_1": None,  # All Modifier 1 edits (Code 1 + Code 2 combined)
                "source": "local_kb",
                "has_data": False
            }
            
            # Filter Modifier 0 - combine Code 1 and Code 2
            if df_mod0 is not None:
                df_mod0_filtered = df_mod0[
                    (df_mod0['CPT_code_1'] == cpt_code) | 
                    (df_mod0['CPT_code_2'] == cpt_code)
                ].copy()
                
                if len(df_mod0_filtered) > 0:
                    result["modifier_0"] = {
                        "record_count": len(df_mod0_filtered),
                        "dataframe": df_mod0_filtered
                    }
                    result["has_data"] = True
                    print(f"      ✅ Modifier 0 (Not Allowed): {len(df_mod0_filtered)} records")
            
            # Filter Modifier 1 - combine Code 1 and Code 2
            if df_mod1 is not None:
                df_mod1_filtered = df_mod1[
                    (df_mod1['CPT_code_1'] == cpt_code) | 
                    (df_mod1['CPT_code_2'] == cpt_code)
                ].copy()
                
                if len(df_mod1_filtered) > 0:
                    result["modifier_1"] = {
                        "record_count": len(df_mod1_filtered),
                        "dataframe": df_mod1_filtered
                    }
                    result["has_data"] = True
                    print(f"      ✅ Modifier 1 (Allowed with Modifier): {len(df_mod1_filtered)} records")
            
            # Summary for this CPT
            mod0_count = result["modifier_0"]["record_count"] if result.get("modifier_0") else 0
            mod1_count = result["modifier_1"]["record_count"] if result.get("modifier_1") else 0
            
            if not result["has_data"]:
                print(f"      ℹ️  No PTP edits found for CPT {cpt_code}")
            else:
                print(f"      ✅ Total: {mod0_count + mod1_count} PTP edits")
            
            results[cpt_code] = result
        
        return results
        
    except Exception as e:
        print(f"❌ Error loading PTP edit tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return {cpt: {"modifier_0": None, "modifier_1": None, "source": "local_kb", "has_data": False} for cpt in cpt_codes}


def extract_cpt_codes_from_ptp_tables(ptp_tables_by_cpt):
    """
    Extract all unique CPT codes from PTP edit tables
    
    Args:
        ptp_tables_by_cpt: Dict with CPT codes as keys, each containing modifier_0 and modifier_1 data
        
    Returns:
        List of unique CPT codes sorted
    """
    all_codes = set()
    
    for cpt_code, ptp_data in ptp_tables_by_cpt.items():
        # Add the CPT code itself
        all_codes.add(cpt_code)
        
        # Extract codes from Modifier 0 table
        if ptp_data.get('modifier_0') and ptp_data['modifier_0'].get('data'):
            df_mod0 = pd.DataFrame(ptp_data['modifier_0']['data'])
            if not df_mod0.empty:
                if 'CPT_code_1' in df_mod0.columns:
                    all_codes.update(df_mod0['CPT_code_1'].astype(str).unique())
                if 'CPT_code_2' in df_mod0.columns:
                    all_codes.update(df_mod0['CPT_code_2'].astype(str).unique())
        
        # Extract codes from Modifier 1 table
        if ptp_data.get('modifier_1') and ptp_data['modifier_1'].get('data'):
            df_mod1 = pd.DataFrame(ptp_data['modifier_1']['data'])
            if not df_mod1.empty:
                if 'CPT_code_1' in df_mod1.columns:
                    all_codes.update(df_mod1['CPT_code_1'].astype(str).unique())
                if 'CPT_code_2' in df_mod1.columns:
                    all_codes.update(df_mod1['CPT_code_2'].astype(str).unique())
    
    return sorted(all_codes)


def get_cpt_descriptions_for_ptp_tables(ptp_tables_by_cpt, target_cpt, model="gpt-4o-mini"):
    """
    Extract all CPT codes from PTP tables and get their descriptions
    
    Args:
        ptp_tables_by_cpt: Dict with CPT codes as keys, containing PTP table data
        target_cpt: Target CPT code
        model: LLM model for fallback descriptions
        
    Returns:
        Dict mapping CPT codes to their description info
    """
    # Extract all unique CPT codes from the tables
    cpt_codes = extract_cpt_codes_from_ptp_tables(ptp_tables_by_cpt)
    
    print(f"\n📋 Extracting descriptions for {len(cpt_codes)} CPT codes referenced in PTP tables...")
    
    # Get descriptions for all codes
    code_descriptions = {}
    for code in cpt_codes:
        desc_info = get_or_generate_cpt_description(code, model=model, use_llm_fallback=True)
        code_descriptions[code] = desc_info
        source_marker = "🟢" if desc_info['source'] == 'internal_kb' else "⚫"
        print(f"  {source_marker} {code}: {desc_info['description'][:60]}... [source: {desc_info['source']}]")
    
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
    file_name = "section_5_results.json"
    output_path = os.path.join(output_dir, file_name)
    
    if not os.path.exists(output_path):
        return None
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Extract the analysis results
        # Support both old format (ptp_tables) and new format (ptp_tables_by_cpt)
        result = {
            "analysis_content": cached_data.get("analysis_content", ""),
            "ptp_tables_by_cpt": cached_data.get("ptp_tables_by_cpt", cached_data.get("ptp_tables", {})),
            "ncci_manual_by_cpt": cached_data.get("ncci_manual_by_cpt", {}),
            "ncci_chunk_details_by_cpt": cached_data.get("ncci_chunk_details_by_cpt", {}),  # ADDED: Load chunk details for citations
            "neighboring_codes": cached_data.get("neighboring_codes", []),
            "cpt_descriptions": cached_data.get("cpt_descriptions", {}),
            "source": cached_data.get("source", "llm")
        }
        
        print(f"✅ Loaded cached results from {output_path}")
        print(f"   Cache timestamp: {cached_data.get('update_time', 'Unknown')}")
        
        # Debug: Print chunk details info
        chunk_details = result.get("ncci_chunk_details_by_cpt", {})
        if chunk_details:
            total_chunks = sum(len(chunks) for chunks in chunk_details.values())
            print(f"   📄 Loaded {total_chunks} chunk details across {len(chunk_details)} CPT codes")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error loading cached results: {str(e)}")
        return None

def ncci_manual_retrieval(target_cpt):
    """
    Retrieve NCCI manual information for a given CPT code using RAG pipeline.
    
    Args:
        target_cpt: Target CPT code to retrieve manual info for
        
    Returns:
        Dict containing:
        - analysis: Full markdown analysis from LLM
        - source: "internal_kb"
    """
    # Define ncci_rag path for output location
    ncci_rag_path = project_root / 'ncci_rag'
    
    print(f"\n📚 Retrieving NCCI manual information for CPT {target_cpt}...")
    
    # Define expected output path
    output_path = ncci_rag_path / 'output' / f'llm_analysis_cpt_{target_cpt}.md'
    
    # Check if analysis already exists
    if output_path.exists():
        print(f"   ✅ Found existing NCCI manual analysis")
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                manual_content = f.read()
            
            return {
                "analysis": manual_content,
                "source": "internal_kb"
            }
        except Exception as e:
            print(f"   ⚠️  Error reading existing file: {e}, regenerating...")
    
    # Generate new analysis
    print(f"   🔄 Generating new NCCI manual analysis...")
    try:
        output_file_path = ncci_llm_analysis(target_cpt)
        
        with open(output_file_path, 'r', encoding='utf-8') as f:
            manual_content = f.read()
        
        print(f"   ✅ NCCI manual analysis completed")
        
        return {
            "analysis": manual_content,
            "source": "internal_kb"
        }
        
    except Exception as e:
        print(f"   ❌ Error generating NCCI manual analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "analysis": None,
            "error": str(e),
            "source": "internal_kb"
        }

def extract_chunk_details_from_manual(target_cpt, manual_content):
    """
    Extract chunk IDs from NCCI manual analysis References section and map to full text.
    
    Args:
        target_cpt: Target CPT code
        manual_content: Dict containing 'analysis' field with markdown content
        
    Returns:
        Dict mapping chunk_id to full chunk details:
        {
            "chunk_000383": {
                "full_text": "...",
                "pages": [232],
                "section": "G. Ophthalmology",
                "chunk_id": "chunk_000383"
            },
            ...
        }
    """
    import re
    
    print(f"\n📋 Extracting chunk details from NCCI manual references...")
    
    # Get the analysis markdown content
    analysis_text = manual_content.get('analysis', '')
    
    if not analysis_text:
        print("   ⚠️  No analysis content found")
        return {}
    
    # Extract chunk IDs with their citation numbers from References section
    # Pattern: 1. `chunk_000383` - Pages 232-232, G. Ophthalmology
    # Pattern may also include citation marker: 1. `chunk_000383` - Pages 232-232, G. Ophthalmology ✓
    chunk_pattern = r'(\d+)\.\s*`(chunk_\d+)`'
    chunk_matches = re.findall(chunk_pattern, analysis_text)
    
    if not chunk_matches:
        print("   ⚠️  No chunk IDs found in References section")
        return {}
    
    print(f"   Found {len(chunk_matches)} chunk references")
    
    # Load retrieved chunks JSON
    chunks_path = project_root / 'ncci_rag' / 'output' / f'retrieved_chunks_cpt_{target_cpt}.json'
    
    if not chunks_path.exists():
        print(f"   ❌ Retrieved chunks file not found: {chunks_path}")
        return {}
    
    try:
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        all_chunks = chunks_data.get('chunks', [])
        
        # Build mapping from chunk_id to full chunk details (preserving citation numbers)
        chunk_details = {}
        for citation_num, chunk_id in chunk_matches:
            # Find matching chunk
            matching_chunk = next((c for c in all_chunks if c.get('chunk_id') == chunk_id), None)
            
            if matching_chunk:
                chunk_details[chunk_id] = {
                    "full_text": matching_chunk.get('full_text', ''),
                    "pages": matching_chunk.get('pages', []),
                    "section": matching_chunk.get('section', ''),
                    "chunk_id": chunk_id,
                    "topic_tags": matching_chunk.get('topic_tags', []),
                    "citation_number": int(citation_num)  # Preserve original citation number
                }
                print(f"   ✅ Mapped [{citation_num}] {chunk_id}: {matching_chunk.get('section', 'N/A')}")
            else:
                print(f"   ⚠️  Chunk {chunk_id} not found in retrieved chunks")
        
        print(f"   ✅ Successfully mapped {len(chunk_details)}/{len(chunk_matches)} chunks")
        return chunk_details
        
    except Exception as e:
        print(f"   ❌ Error loading retrieved chunks: {e}")
        import traceback
        traceback.print_exc()
        return {}

def analyze_ncci_compliance(target_cpt, model="gpt-4o-mini", use_cache=True):
    """
    Analyze NCCI compliance for a given CPT code and its neighboring codes
    
    Args:
        target_cpt: Target CPT code to analyze
        model: LLM model to use for analysis
        use_cache: If True, check for and use cached results (default: True)
        
    Returns:
        Dict with analysis results containing:
        - analysis_content: LLM analysis text
        - ptp_tables_by_cpt: Dict with CPT codes as keys, each containing modifier_0 and modifier_1 data
        - neighboring_codes: List of neighboring CPT codes analyzed
        - source: "llm"
    """
    print(f"\n🔍 Starting NCCI compliance check for CPT code: {target_cpt}")
    
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
        
        # Filter tables for target CPT and neighboring codes
        all_codes = [target_cpt] + neighboring_codes
        filtered_tables_by_cpt = filter_ptp_tables_by_cpts(all_codes)
        
        # Get NCCI manual information for all CPT codes (target + neighboring)
        # This replaces the old LLM-based analysis from PTP tables
        print("\n📚 Retrieving NCCI manual analysis from internal knowledge base...")
        all_cpt_codes = [target_cpt] + neighboring_codes
        ncci_manual_by_cpt = {}
        ncci_chunk_details_by_cpt = {}
        
        for cpt_code in all_cpt_codes:
            print(f"\n📚 Retrieving NCCI manual information for CPT {cpt_code}...")
            manual_content = ncci_manual_retrieval(cpt_code)
            if manual_content:
                ncci_manual_by_cpt[cpt_code] = manual_content
                # Extract chunk details for this CPT
                chunk_details = extract_chunk_details_from_manual(cpt_code, manual_content)
                if chunk_details:
                    ncci_chunk_details_by_cpt[cpt_code] = chunk_details
        
        # Prepare PTP tables for saving (convert dataframe to dict for JSON serialization)
        ptp_tables_for_save = {}
        
        for cpt_code, filtered_tables in filtered_tables_by_cpt.items():
            ptp_tables_for_save[cpt_code] = {
                "modifier_0": {
                    "data": filtered_tables["modifier_0"]["dataframe"].to_dict(orient='records'),
                    "record_count": filtered_tables["modifier_0"]["record_count"]
                } if filtered_tables.get("modifier_0") else None,
                "modifier_1": {
                    "data": filtered_tables["modifier_1"]["dataframe"].to_dict(orient='records'),
                    "record_count": filtered_tables["modifier_1"]["record_count"]
                } if filtered_tables.get("modifier_1") else None,
                "has_data": filtered_tables.get("has_data", False),
                "source": "local_kb"
            }
        
        # Extract CPT codes and get their descriptions
        cpt_descriptions = get_cpt_descriptions_for_ptp_tables(ptp_tables_for_save, target_cpt, model)
        
        # Save findings to JSON file
        output_dir = f"output/services_findings/{target_cpt}"
        os.makedirs(output_dir, exist_ok=True)
        dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = "section_5_results.json"
        output_path = os.path.join(output_dir, file_name)
        
        result_obj = {
            "service": "section 5 - NCCI compliance check",
            "update_time": dt_str,
            "cpt_code": target_cpt,
            "neighboring_codes": neighboring_codes,
            "ptp_tables_by_cpt": ptp_tables_for_save,
            "ncci_manual_by_cpt": ncci_manual_by_cpt,
            "ncci_chunk_details_by_cpt": ncci_chunk_details_by_cpt,
            "analysis_content": "",  # No longer needed - analysis is in ncci_manual_by_cpt
            "cpt_descriptions": cpt_descriptions,            
            "source": "internal_kb"  # Changed from "llm" since we use internal KB
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved findings to {output_path}")
        
        return {
            "analysis_content": "",  # No longer needed
            "ptp_tables_by_cpt": ptp_tables_for_save,
            "ncci_manual_by_cpt": ncci_manual_by_cpt,
            "ncci_chunk_details_by_cpt": ncci_chunk_details_by_cpt,
            "neighboring_codes": neighboring_codes,
            "cpt_descriptions": cpt_descriptions,
            "source": "internal_kb"
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "content": None,
            "error": str(e),
            "section_id": "section_5",
            "section_title": "NCCI Compliance Check"
        }


def get_section_metadata():
    """Get metadata about this section for orchestration"""
    return {
        "section_num": 5,
        "section_id": "section_5",
        "title": "NCCI Compliance Check",
        "description": "Check NCCI edits and modifier compliance"
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the NCCI compliance workflow"""
    test_cpt = "97810"
    
    print(f"\n🔍 CPT Code: {test_cpt}\n")
    
    result = analyze_ncci_compliance(test_cpt, model="gpt-4o-mini", use_cache=False)
    
    if result and "analysis_content" in result:
        print("\n" + "="*80)
        print("NCCI COMPLIANCE CHECK RESULTS:")
        print("="*80)
        print(result["analysis_content"])
