# python -m services.common.cms_exclusions
"""
CMS exclustions data loader for APC, ASC and PNPP Payment Comparison
"""

import os
import pandas as pd
import re
from typing import Dict, List, Tuple


def parse_cpt_code_range(code_str: str) -> List[str]:
    """
    Parse CPT code string that may contain ranges.
    
    Args:
        code_str: CPT code string, can be:
            - Single code: "11042"
            - Range: "15100-15277"
            - Multiple ranges: "33214-33229, 33249-33285"
    
    Returns:
        List of individual CPT codes in order
        
    Examples:
        "11042" -> ["11042"]
        "15100-15277" -> ["15100", "15101", ..., "15277"]
        "33214-33229, 33249-33285" -> ["33214", ..., "33229", "33249", ..., "33285"]
    """
    code_str = str(code_str).strip()
    codes = []
    
    # Split by comma to handle multiple ranges
    parts = [p.strip() for p in code_str.split(',')]
    
    for part in parts:
        if '-' in part:
            # This is a range
            try:
                start, end = part.split('-')
                start = start.strip()
                end = end.strip()
                
                # Extract numeric part and prefix (if any)
                # CPT codes can be like "15100" or "0479T"
                start_match = re.match(r'(\d+)([A-Z]?)', start)
                end_match = re.match(r'(\d+)([A-Z]?)', end)
                
                if start_match and end_match:
                    start_num = int(start_match.group(1))
                    end_num = int(end_match.group(1))
                    suffix = start_match.group(2)  # Use suffix from start
                    
                    # Generate all codes in range (in order)
                    for num in range(start_num, end_num + 1):
                        codes.append(f"{num}{suffix}")
                else:
                    # Can't parse as range, add as-is
                    codes.append(part)
            except:
                # If parsing fails, add as-is
                codes.append(part)
        else:
            # Single code
            codes.append(part)
    
    return codes


def load_cms_exclusions_data(
    excel_path: str = None
) -> Dict[str, pd.DataFrame]:
    """
    Load CMS exclusions data from an Excel file.
    
    Args:
        excel_path: Path to the Excel file. If None, uses default path.
    """
    # Default path
    if excel_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        excel_path = os.path.join(base_dir, 'data', 'cms_exclusions.xlsx')
    
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"CMS exclusions file not found: {excel_path}")
    
    # Load all sheets into a dictionary of DataFrames
    xls = pd.ExcelFile(excel_path)
    data = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
    
    return data


def get_exclusions_df(category: str, expand_ranges: bool = True) -> pd.DataFrame:
    """
    Get exclusions as an expanded DataFrame for a specific category.
    Automatically expands CPT code ranges if requested.
    
    Args:
        category: Exclusion category - 'APC', 'ASC', or 'PNPP' (default: 'APC')
        expand_ranges: If True, expands code ranges (e.g., "15100-15277" becomes 178 rows)
        
    Returns:
        DataFrame with columns: ['CPT Code', 'Status Indicator', 'Long Descriptor', 'Original Code']
        
    Example:
        # For APC exclusions
        df = get_exclusions_df('APC')
        
        # For ASC exclusions
        df = get_exclusions_df('ASC')
        
        CPT Code | Status Indicator | Long Descriptor | Original Code
        11042    | T                | Debridement...  | 11042
        15100    | T                | Split...        | 15100-15277
        15101    | T                | Split...        | 15100-15277
        ...
    """
    # Map category to sheet name
    sheet_mapping = {
        'APC': 'APC Exc',
        'ASC': 'ASC Exc',
        'PNPP': 'PNPP Exc'
    }
    
    category_upper = category.upper()
    if category_upper not in sheet_mapping:
        raise ValueError(f"Invalid category '{category}'. Must be one of: APC, ASC, PNPP")
    
    sheet_name = sheet_mapping[category_upper]
    
    data = load_cms_exclusions_data()
    exclusions_df = data.get(sheet_name, pd.DataFrame())
    
    if exclusions_df.empty:
        print(f"⚠️  Warning: No data found for sheet '{sheet_name}'")
        return pd.DataFrame(columns=['CPT Code', 'Status Indicator',  'Original Code'])
    
    # Clean column names (remove trailing spaces)
    exclusions_df.columns = exclusions_df.columns.str.strip()
    
    if not expand_ranges:
        # Return as-is, just rename columns
        df = exclusions_df.copy()
        df.rename(columns={'Excluded CPT Code': 'CPT Code'}, inplace=True)
        df['Original Code'] = df['CPT Code']
        return df
    
    # Expand ranges
    expanded_rows = []
    
    for _, row in exclusions_df.iterrows():
        original_code = str(row['Excluded CPT Code']).strip()
        status_indicator = str(row['Status Indicator']).strip()
        
        # Expand code ranges for cpt range in excel
        expanded_codes = parse_cpt_code_range(original_code)
        
        # Create a row for each expanded code
        for code in expanded_codes:
            expanded_rows.append({
                'CPT Code': code,
                'Status Indicator': status_indicator,
                'Original Code': original_code
            })
    
    return pd.DataFrame(expanded_rows)


def get_exclusions_for_cpt_list(cpt_codes: List[str], category: str = 'APC') -> Dict[str, Dict]:
    """
    Get exclusion information for a list of CPT codes.
    Uses DataFrame filtering for efficient batch processing.
    
    Args:
        cpt_codes: List of CPT codes to check
        category: Exclusion category - 'APC', 'ASC', or 'PNPP' (default: 'APC')
        
    Returns:
        Dictionary mapping CPT codes to their exclusion info (if excluded)
        
    Example:
        # Check APC exclusions
        exclusions = get_exclusions_for_cpt_list(['15150', '97810'], category='APC')
        
        # Check ASC exclusions
        exclusions = get_exclusions_for_cpt_list(['15150', '97810'], category='ASC')
        
        # Returns:
        {
            '15150': {
                'status_indicator': 'T',
                'original_code': '15100-15277'
            }
        }
    """
    # Load exclusions DataFrame once
    exclusions_df = get_exclusions_df(category=category)
    
    # Convert to string and strip for comparison
    cpt_codes_clean = [str(c).strip() for c in cpt_codes]
    
    # Filter DataFrame in one operation (much faster than iterating)
    matches = exclusions_df[exclusions_df['CPT Code'].isin(cpt_codes_clean)]
    
    # Convert to dictionary
    results = {}
    for _, row in matches.iterrows():
        results[row['CPT Code']] = {
            'status_indicator': row['Status Indicator'],
            'original_code': row['Original Code']
        }
    return results


# ==================== Test Function ====================

if __name__ == "__main__":
    cpt_list = ['11042', '11043', '97810', '15150', '15278', '33220', '99999']
    exclusions_found = get_exclusions_for_cpt_list(cpt_list, category='APC')
    
    

