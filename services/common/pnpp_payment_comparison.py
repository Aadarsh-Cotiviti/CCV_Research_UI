# python -m services.common.pnpp_payment_comparison
"""
PNPP Payment Comparison Data Loader

This module handles loading and preprocessing of CMS ASC payment rate data
from quarterly addendum files (2024-2026).
"""

import os
import pandas as pd
import re
from typing import Dict, List, Tuple
from .cms_exclusions import get_exclusions_for_cpt_list


# Expected columns to extract from each sheet
REQUIRED_COLUMNS = ['HCPCS', 'STATUS CODE', 'NON-FACILITY TOTAL', 'FACILITY TOTAL', 'CONV FACTOR']


def parse_sheet_name(sheet_name: str) -> Tuple[str, str]:
    """
    Parse sheet name to extract month and year
    
    Args:
        sheet_name: Sheet name like "Jan 24" (month abbreviation + 2-digit year)
        
    Returns:
        Tuple of (month, year)
    """
    # Pattern: Jan 24, Feb 24, etc. (Month + space + 2-digit year)
    # Use $ to ensure the pattern matches the entire string
    pattern = r'^(\w+)\s+(\d{2})$'
    match = re.match(pattern, sheet_name, re.IGNORECASE)
    
    if match:
        month, year_2digit = match.groups()
        # Convert 2-digit year to 4-digit (24 -> 2024, 25 -> 2025, 26 -> 2026)
        year = '20' + year_2digit
        return month, year
    
    return None, None


def filter_years(sheet_names: List[str], start_year: int = 2024, end_year: int = 2026, january_only: bool = True) -> List[str]:
    """
    Filter sheet names to only include those within the specified year range and optionally January only
    
    Args:
        sheet_names: List of all sheet names
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
        january_only: If True, only include January sheets (default: True)
        
    Returns:
        Filtered list of sheet names
    """
    filtered = []
    
    for sheet_name in sheet_names:
        month, year = parse_sheet_name(sheet_name)
        if year and start_year <= int(year) <= end_year:
            # If january_only is True, only include January sheets (Jan)
            if january_only and month != 'Jan':
                continue
            filtered.append(sheet_name)
    
    return filtered


def detect_header_row(excel_path: str, sheet_name: str, max_rows: int = 20) -> int:
    """
    Detect the row number where the actual table header is located
    
    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet name to analyze
        max_rows: Maximum rows to search for header (default: 20)
        
    Returns:
        Row number (0-indexed) where header is found, or 0 if not found
    """
    # Read first few rows without header to inspect
    df_peek = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=max_rows)
    
    # Look for row containing the required column names
    for idx, row in df_peek.iterrows():
        row_values = row.astype(str).str.strip().str.lower()
        
        # Check if this row contains our expected columns
        matches = sum([
            any('hcpcs' in val for val in row_values),
            any('status' in val and 'code' in val for val in row_values),
            any('non-facility' in val and 'total' in val for val in row_values),
            any('facility' in val and 'total' in val for val in row_values),
            any('conv' in val and 'factor' in val for val in row_values)
        ])
        
        # If we found at least 3 of our 4 expected columns, this is likely the header
        if matches >= 3:
            return idx
    
    # Default to row 0 if no clear header found
    return 0


def load_payment_data(
    excel_path: str = None,
    start_year: int = 2024,
    end_year: int = 2026
) -> Dict[str, pd.DataFrame]:
    """
    Load payment rate data from quarterly Excel file
    
    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        start_year: Starting year to include (default: 2024)
        end_year: Ending year to include (default: 2026)
        
    Returns:
        Dictionary mapping sheet names to DataFrames with columns:
        ['HCPCS', 'STATUS CODE','Non-Facility Total', 'Facility Total', 'Conversion Factor']
    """
    # Default path
    if excel_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        excel_path = os.path.join(base_dir, 'data', 'pnpp_fee_schedule.xlsx')
    
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Payment data file not found: {excel_path}")
    
    print(f"📊 Loading payment data from: {excel_path}")
    
    # Read all sheet names
    excel_file = pd.ExcelFile(excel_path)
    all_sheets = excel_file.sheet_names
    print(f"   Found {len(all_sheets)} total sheets")
    
    # Filter to desired years
    target_sheets = filter_years(all_sheets, start_year, end_year)
    print(f"   Filtering to {start_year}-{end_year}: {len(target_sheets)} sheets")
    
    # Load and process each sheet
    payment_data = {}
    
    for sheet_name in target_sheets:
        try:
            # Detect where the actual table starts
            header_row = detect_header_row(excel_path, sheet_name)
            
            # Read the sheet with correct header row
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
            
            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Check if required columns exist
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            
            if missing_cols:
                print(f"   ⚠️  Sheet '{sheet_name}' missing columns: {missing_cols}")
                # Try to find similar column names
                available_cols = df.columns.tolist()
                print(f"       Available columns: {available_cols}")
                print(f"       (Header detected at row {header_row})")
                continue
            
            # Extract only required columns
            df_filtered = df[REQUIRED_COLUMNS].copy()
            
            # Clean data
            # Remove rows where HCPCS is NaN
            df_filtered = df_filtered.dropna(subset=['HCPCS'])
            
            # Convert HCPCS to string and strip whitespace
            df_filtered['HCPCS'] = df_filtered['HCPCS'].astype(str).str.strip()
            
            # Remove any completely empty rows
            df_filtered = df_filtered.dropna(how='all')
            
            # Calculate payment rates
            df_filtered['Non-Facility Payment Rate'] = df_filtered['NON-FACILITY TOTAL'] * df_filtered['CONV FACTOR']
            df_filtered['Facility Payment Rate'] = df_filtered['FACILITY TOTAL'] * df_filtered['CONV FACTOR']
            
            payment_data[sheet_name] = df_filtered
            print(f"   ✅ Loaded '{sheet_name}': {len(df_filtered)} records (header at row {header_row})")
            
        except Exception as e:
            print(f"   ❌ Error loading sheet '{sheet_name}': {str(e)}")
            continue
    
    print(f"\n✅ Successfully loaded {len(payment_data)} sheets")
    return payment_data


def pnpp_get_payment_history_for_multiple_cpts(
    cpt_codes: List[str],
    excel_path: str = None,
    january_only: bool = True
) -> pd.DataFrame:
    """
    Get payment history for multiple CPT codes directly from Excel file
    
    Args:
        cpt_codes: List of CPT codes to look up
        excel_path: Path to Excel file. If None, uses default path.
        january_only: If True, only return January data for each year (default: True)
        
    Returns:
        DataFrame with payment history for all specified CPT codes
    """
    # Load payment data from Excel
    payment_data = load_payment_data(excel_path=excel_path)
    
    # Convert CPT codes to strings
    cpt_codes_str = [str(code) for code in cpt_codes]
    
    # Collect records for all CPT codes
    all_records = []
    for sheet_name, df in payment_data.items():
        # Parse period information
        month, year = parse_sheet_name(sheet_name)
        
        # Filter for specified CPT codes
        cpt_rows = df[df['HCPCS'].isin(cpt_codes_str)]

        # Filter for specific STATUS CODE
        keep_SC = ['A']
        cpt_rows = cpt_rows[cpt_rows['STATUS CODE'].isin(keep_SC)]
        
        # Add period columns to each matching record
        for _, row in cpt_rows.iterrows():
            record = {
                'HCPCS': row['HCPCS'],
                'Year': year,
                'Month': month,
                'Period': sheet_name,
                'STATUS CODE': row['STATUS CODE'],
                'Non-Facility Payment Rate': row['Non-Facility Payment Rate'],
                'Facility Payment Rate': row['Facility Payment Rate'],
                'NON-FACILITY TOTAL': row['NON-FACILITY TOTAL'],
                'FACILITY TOTAL': row['FACILITY TOTAL'],
                'CONV FACTOR': row['CONV FACTOR']
            }
            all_records.append(record)
    
    # Create DataFrame and sort
    combined_history = pd.DataFrame(all_records)
    if not combined_history.empty:
        combined_history = combined_history.sort_values(['HCPCS', 'Year'])
    
    return combined_history


def get_pnpp_payment_history_with_exclusions(
    cpt_codes: List[str],
    exclusion_category: str = 'PNPP',
    excel_path: str = None,
    january_only: bool = True
) -> Dict:
    """
    Get payment history for multiple CPT codes and filter out excluded codes
    
    Args:
        cpt_codes: List of CPT codes to look up
        exclusion_category: CMS exclusion category - 'APC', 'ASC', or 'PNPP' (default: 'PNPP')
        excel_path: Path to Excel file. If None, uses default path.
        january_only: If True, only return January data for each year (default: True)
        
    Returns:
        Dictionary containing:
            - 'data': Full payment history (all codes)
            - 'data_filtered': Payment history with excluded codes removed
            - 'exclusions': Dictionary of excluded codes with their info
            - 'excluded_cpt_codes': List of excluded CPT codes
            - 'record_count': Total number of records
            - 'record_count_filtered': Number of records after filtering
    """
    # Get payment history for all codes (directly from Excel)
    payment_history_df = pnpp_get_payment_history_for_multiple_cpts(
        cpt_codes=cpt_codes,
        excel_path=excel_path,
        january_only=january_only
    )
    
    if payment_history_df.empty:
        return {
            "data": [],
            "data_filtered": [],
            "data_filtered_df": pd.DataFrame(),  # Empty DataFrame
            "exclusions": {},
            "excluded_cpt_codes": [],
            "record_count": 0,
            "record_count_filtered": 0
        }
    
    # Check for exclusions
    print(f"\n🔍 Checking CMS {exclusion_category} exclusions list...")
    exclusions_info = get_exclusions_for_cpt_list(cpt_codes, category=exclusion_category)
    excluded_cpt_codes = list(exclusions_info.keys())
    
    if exclusions_info:
        print(f"⚠️  Found {len(exclusions_info)} excluded code(s) in {exclusion_category}:")
        for cpt, info in exclusions_info.items():
            print(f"   - {cpt}: Payment Indicator '{info['status_indicator']}'")
    else:
        print(f"✅ No codes found in {exclusion_category} exclusions list")
    
    # Filter out excluded codes from payment table
    payment_history_filtered_df = payment_history_df[
        ~payment_history_df['HCPCS'].isin(excluded_cpt_codes)
    ].copy()

    if len(excluded_cpt_codes) > 0:
        print(f"📋 Payment table will show {len(payment_history_filtered_df)} records (excluded codes removed)")
    
    # Return both full and filtered data
    return {
        "data": payment_history_df.to_dict(orient='records'),
        "data_filtered": payment_history_filtered_df.to_dict(orient='records'),
        "data_filtered_df": payment_history_filtered_df,  # DataFrame for markdown conversion
        "exclusions": exclusions_info if exclusions_info else {},
        "excluded_cpt_codes": excluded_cpt_codes,
        "record_count": len(payment_history_df),
        "record_count_filtered": len(payment_history_filtered_df)
    }


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the payment data loading"""
    test_cpt_list = ["97810", "11042"]
    history = get_pnpp_payment_history_with_exclusions(
        cpt_codes=test_cpt_list,
        exclusion_category='PNPP',
        january_only=True
    )
    print(f"\n✅ Test completed!")
    print(f"   Found {history['record_count']} total records")
    print(f"   After filtering: {history['record_count_filtered']} records")
    print(f"   Excluded codes: {history['excluded_cpt_codes']}")

    
