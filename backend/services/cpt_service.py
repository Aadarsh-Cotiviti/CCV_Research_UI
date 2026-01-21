# python -m services.cpt_service 
"""
CPT Code Service

This module handles CPT code generation, parsing, and description management.
Designed to be independent and reusable for agentic workflows.
"""

from llm_wrapper import query_llm
from services.common import get_or_generate_cpt_description


def generate_cpt_codes_from_topic(topic, model="gpt-4.1-mini"):
    """
    Generate relevant CPT codes from a medical procedure topic
    
    Args:
        topic: Medical procedure or condition description
        model: LLM model to use for generation
        
    Returns:
        Raw LLM response with CPT codes
    """
    prompt = f"""
You are a medical coding expert. Given the following medical procedure or condition topic, provide the top 5 most relevant CPT codes.

Topic: {topic}

For each CPT code, provide:
1. The CPT code number
2. A brief description (one line)

Format your response EXACTLY as follows (one code per line):
CODE: [5-digit code] | DESCRIPTION: [brief description]

Example format:
CODE: 99213 | DESCRIPTION: Office visit, established patient, moderate complexity
CODE: 99214 | DESCRIPTION: Office visit, established patient, high complexity

Provide exactly 5 CPT codes. If the topic is too vague or unclear, provide the most commonly associated codes.
"""
    
    messages = [
        {"role": "system", "content": "You are an expert medical coding specialist with deep knowledge of CPT codes."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = query_llm(messages, model=model)
        return response
    except Exception as e:
        return f"Error generating CPT codes: {str(e)}"


def parse_cpt_codes(llm_response):
    """
    Parse LLM response to extract CPT codes and get descriptions from xlsx
    
    Args:
        llm_response: Raw response from LLM containing CPT codes
        
    Returns:
        List of dictionaries with 'code' and 'description' keys
    """
    codes = []
    lines = llm_response.strip().split('\n')
    
    for line in lines:
        if 'CODE:' in line and 'DESCRIPTION:' in line:
            try:
                parts = line.split('|')
                code_part = parts[0].split('CODE:')[1].strip()
                llm_desc = parts[1].split('DESCRIPTION:')[1].strip()
                
                # Get description from local file or LLM (use_llm_fallback=False to only check local)
                desc_info = get_or_generate_cpt_description(code_part, use_llm_fallback=False)
                
                if desc_info and desc_info.get('description'):
                    # Use local description if available
                    codes.append({
                        "code": code_part, 
                        "description": desc_info['description'], 
                        "source": desc_info['source']
                    })
                else:
                    # Fallback to LLM description from parsing
                    codes.append({"code": code_part, "description": llm_desc, "source": 'llm'})
               
            except Exception:
                continue
    
    return codes


def get_cpt_codes_for_topic(topic, model="gpt-4.1-mini"):
    """
    High-level function to generate and parse CPT codes
    
    Args:
        topic: Medical procedure or condition description
        model: LLM model to use
        
    Returns:
        List of CPT code dictionaries
    """
    llm_response = generate_cpt_codes_from_topic(topic, model)
    return parse_cpt_codes(llm_response)


# ==================== Simple Test Function ====================

if __name__ == "__main__":
    test_topic = "bronchial biopsy"
    
    codes = get_cpt_codes_for_topic(test_topic, model="gpt-4.1-mini")
        
    print(f"✅ Successfully generated {len(codes)} CPT codes:\n")
    for i, code_info in enumerate(codes, 1):
        print(f"{i}. {code_info['code']}")
        print(f"   {code_info['description']}...")
        print()
        