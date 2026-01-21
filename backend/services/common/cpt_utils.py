"""
Common CPT Code Utilities

Shared functions for CPT code description retrieval and generation.
"""

import pandas as pd
from pathlib import Path
from llm_wrapper import query_llm


def get_cpt_description_from_local(code):
    """
    Get CPT code description from local Excel file
    
    Args:
        code: CPT code (string)
        
    Returns:
        Description string if found, None otherwise
    """
    try:
        excel_path = Path("data/CPT Codes with Long Descriptions 2025.xlsx")
        if not excel_path.exists():
            print(f"⚠️  CPT Excel file not found: {excel_path}")
            return None
            
        df = pd.read_excel(excel_path)
        
        # Excel columns: CPTCd and FullDesc
        if 'CPTCd' not in df.columns or 'FullDesc' not in df.columns:
            print(f"⚠️  Expected columns 'CPTCd' and 'FullDesc' not found. Available: {df.columns.tolist()}")
            return None
        
        # Convert code to string for comparison
        code_str = str(code).strip()
        df['CPTCd'] = df['CPTCd'].astype(str).str.strip()
        
        code_df = df[df['CPTCd'] == code_str]
        if not code_df.empty:
            return code_df.iloc[0]['FullDesc']
        
        return None
    except Exception as e:
        print(f"⚠️  Could not load CPT description for {code}: {str(e)}")
        return None


def generate_cpt_description_with_llm(code, model="gpt-4.1-mini"):
    """
    Generate CPT code description using LLM when not found in local database
    
    Args:
        code: CPT code (string)
        model: LLM model to use
        
    Returns:
        Generated description string
    """
    prompt = f"""
As a certified medical coding specialist, provide the official CPT code description for: {code}

Return ONLY the description text itself, without any prefix or code number.

Example:
For CPT 97810, return: "Acupuncture, 1 or more needles; without electrical stimulation, initial 15 minutes of personal one-on-one contact with the patient"

NOT: "CPT 97810: Acupuncture..."

Guidelines:
- Use only official CPT code descriptions
- Be concise and accurate
- Return ONLY the description text
- If the code is not recognized or invalid, state "Code not found in CPT database"
- Do not include any additional explanations or formatting
"""
    
    try:
        messages = [
            {"role": "system", "content": "You are an expert medical coding specialist with knowledge of CPT codes."},
            {"role": "user", "content": prompt}
        ]
        description = query_llm(messages, model=model)
        return description.strip()
    except Exception as e:
        print(f"⚠️  Error generating description for {code}: {str(e)}")
        return "Description unavailable"


def get_or_generate_cpt_description(code, model="gpt-4.1-mini", use_llm_fallback=True):
    """
    Get CPT code description - first from local database, then from LLM if not found
    
    This is the main function that should be used throughout the application
    for retrieving CPT code descriptions.
    
    Args:
        code: CPT code (string)
        model: LLM model to use for generation (default: gpt-4.1-mini)
        use_llm_fallback: Whether to use LLM if local description not found (default: True)
        
    Returns:
        Dictionary with:
            - cpt_code: The CPT code
            - description: The description text
            - source: 'local' or 'llm'
    """
    # Try local database first
    local_desc = get_cpt_description_from_local(code)
    
    if local_desc:
        return {
            "cpt_code": code,
            "description": local_desc,
            "source": "internal_kb"
        }
    
    # If not found and LLM fallback is enabled, generate with LLM
    if use_llm_fallback:
        print(f"📝 Generating description for {code} using LLM...")
        llm_desc = generate_cpt_description_with_llm(code, model=model)
        return {
            "cpt_code": code,
            "description": llm_desc,
            "source": "llm"
        }
    
    # If no fallback, return None
    return {
        "cpt_code": code,
        "description": None,
        "source": "not_found"
    }
