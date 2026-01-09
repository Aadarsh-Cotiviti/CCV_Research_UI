"""
Payment Comparison Data Loader

This module handles loading and preprocessing of CMS APC payment rate data
from quarterly addendum files (2023-2025).
"""

import os
import pandas as pd
import re
from typing import Dict, List, Tuple


# Expected columns to extract from each sheet
REQUIRED_COLUMNS = ['HCPCS Code', 'SI', 'APC Code', 'Payment Rate']


def parse_sheet_name(sheet_name: str) -> Tuple[str, str, str]:
    """
    Parse sheet name to extract year, month, and addendum type
    
    Args:
        sheet_name: Sheet name like "2025 October Addendum B"
        
    Returns:
        Tuple of (year, month, addendum_type)
    """
    # Pattern: YYYY Month Addendum X
    pattern = r'(\d{4})\s+(\w+)\s+Addendum\s+([A-Z])'
    match = re.match(pattern, sheet_name, re.IGNORECASE)
    
    if match:
        year, month, addendum = match.groups()
        return year, month, addendum
    
    return None, None, None


def filter_years(sheet_names: List[str], start_year: int = 2023, end_year: int = 2025) -> List[str]:
    """
    Filter sheet names to only include those within the specified year range
    
    Args:
        sheet_names: List of all sheet names
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
        
    Returns:
        Filtered list of sheet names
    """
    filtered = []
    
    for sheet_name in sheet_names:
        year, month, addendum = parse_sheet_name(sheet_name)
        if year and start_year <= int(year) <= end_year:
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
            any('hcpcs' in val and 'code' in val for val in row_values),
            any('si' == val for val in row_values),
            any('apc' in val for val in row_values),
            any('payment' in val and 'rate' in val for val in row_values)
        ])
        
        # If we found at least 3 of our 4 expected columns, this is likely the header
        if matches >= 3:
            return idx
    
    # Default to row 0 if no clear header found
    return 0


def load_payment_data(
    excel_path: str = None,
    start_year: int = 2023,
    end_year: int = 2025
) -> Dict[str, pd.DataFrame]:
    """
    Load payment rate data from quarterly addendum Excel file
    
    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        start_year: Starting year to include (default: 2023)
        end_year: Ending year to include (default: 2025)
        
    Returns:
        Dictionary mapping sheet names to DataFrames with columns:
        ['HCPCS Code', 'SI', 'APC Code', 'Payment Rate']
    """
    # Default path
    if excel_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        excel_path = os.path.join(base_dir, 'data', 'cpt_payment_changes_quarterly.xlsx')
    
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
            # Remove rows where HCPCS Code is NaN
            df_filtered = df_filtered.dropna(subset=['HCPCS Code'])
            
            # Convert HCPCS Code to string and strip whitespace
            df_filtered['HCPCS Code'] = df_filtered['HCPCS Code'].astype(str).str.strip()
            
            # Rename APC column to APC Code and convert to string to preserve codes (e.g., "5072" not 5072)
            if 'APC' in df_filtered.columns:
                df_filtered.rename(columns={'APC': 'APC Code'}, inplace=True)
            # Convert to numeric first, then to int, then to string to remove decimals
            df_filtered['APC Code'] = pd.to_numeric(df_filtered['APC Code'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            
            # Remove any completely empty rows
            df_filtered = df_filtered.dropna(how='all')
            
            payment_data[sheet_name] = df_filtered
            
            year, month, addendum = parse_sheet_name(sheet_name)
            print(f"   ✅ Loaded '{sheet_name}': {len(df_filtered)} records (header at row {header_row})")
            
        except Exception as e:
            print(f"   ❌ Error loading sheet '{sheet_name}': {str(e)}")
            continue
    
    print(f"\n✅ Successfully loaded {len(payment_data)} sheets")
    return payment_data


def preprocess_all_payment_data(
    excel_path: str = None,
    start_year: int = 2023,
    end_year: int = 2025,
    output_path: str = None
) -> pd.DataFrame:
    """
    Preprocess all payment data and save to CSV file
    
    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        start_year: Starting year to include (default: 2023)
        end_year: Ending year to include (default: 2025)
        output_path: Path to save CSV. If None, uses default output folder.
        
    Returns:
        Combined DataFrame with all payment records sorted by CPT code and date
    """
    # Load all payment data
    payment_data = load_payment_data(excel_path=excel_path, start_year=start_year, end_year=end_year)
    
    # Collect all records
    all_records = []
    
    print(f"\n📝 Processing all CPT codes from {len(payment_data)} sheets...")
    
    for sheet_name, df in payment_data.items():
        # Parse period information
        year, month, addendum = parse_sheet_name(sheet_name)
        
        # Add period columns to each record
        for _, row in df.iterrows():
            record = {
                'HCPCS Code': row['HCPCS Code'],
                'Year': year,
                'Month': month,
                'Addendum': addendum,
                'Period': sheet_name,
                'SI': row['SI'],
                'APC Code': row['APC Code'],
                'Payment Rate': row['Payment Rate']
            }
            all_records.append(record)
    
    # Convert to DataFrame
    combined_df = pd.DataFrame(all_records)
    
    # Ensure APC Code is stored as string (APC codes like "5072", not integers with decimals)
    # Convert to numeric first, then to int, then to string to remove decimals
    combined_df['APC Code'] = pd.to_numeric(combined_df['APC Code'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
    
    # Sort by HCPCS Code, Year, and Month
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    combined_df['Month_Num'] = combined_df['Month'].apply(
        lambda x: month_order.index(x) if x in month_order else 99
    )
    combined_df = combined_df.sort_values(['HCPCS Code', 'Year', 'Month_Num'])
    combined_df = combined_df.drop('Month_Num', axis=1)
    
    # Reorder columns for better readability
    column_order = ['HCPCS Code', 'Year', 'Month', 'Addendum', 'Period', 'SI', 'APC Code', 'Payment Rate']
    combined_df = combined_df[column_order]
    
    # Save to CSV
    if output_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_dir = os.path.join(base_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'preprocessed_payment_comparison.csv')
    
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ Saved {len(combined_df)} records to {output_path}")
    print(f"   Total unique CPT codes: {combined_df['HCPCS Code'].nunique()}")
    
    return combined_df


def load_preprocessed_payment_data(file_path: str = None) -> pd.DataFrame:
    """
    Load preprocessed payment data from CSV
    
    Args:
        file_path: Path to the preprocessed CSV file. If None, uses default path.
        
    Returns:
        DataFrame with all payment records
    """
    if file_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_dir, 'output', 'preprocessed_payment_comparison.csv')
    
    # If file doesn't exist, generate it first
    if not os.path.exists(file_path):
        print(f"⚠️  Preprocessed file not found: {file_path}")
        print("📝 Generating preprocessed data...")
        preprocess_all_payment_data(output_path=file_path)
    
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"✅ Loaded {len(df)} payment records from {file_path}")
    return df


def get_payment_history_for_cpt(
    cpt_code: str,
    preprocessed_data: pd.DataFrame = None,
    january_only: bool = True
) -> pd.DataFrame:
    """
    Get payment history for a specific CPT code from preprocessed data
    
    Args:
        cpt_code: CPT code to look up
        preprocessed_data: Preloaded preprocessed DataFrame. If None, will load from file.
        january_only: If True, only return January data for each year (default: True)
        
    Returns:
        DataFrame with payment history for the specified CPT code
    """
    # Load preprocessed data if not provided
    if preprocessed_data is None:
        preprocessed_data = load_preprocessed_payment_data()
    
    # Filter for specific CPT code
    cpt_history = preprocessed_data[preprocessed_data['HCPCS Code'] == str(cpt_code)].copy()
    
    # Filter to January only if requested
    if january_only and not cpt_history.empty:
        cpt_history = cpt_history[cpt_history['Month'] == 'January'].copy()
    
    return cpt_history


def get_payment_history_for_multiple_cpts(
    cpt_codes: List[str],
    preprocessed_data: pd.DataFrame = None,
    january_only: bool = True
) -> pd.DataFrame:
    """
    Get payment history for multiple CPT codes from preprocessed data
    
    Args:
        cpt_codes: List of CPT codes to look up
        preprocessed_data: Preloaded preprocessed DataFrame. If None, will load from file.
        january_only: If True, only return January data for each year (default: True)
        
    Returns:
        DataFrame with payment history for all specified CPT codes
    """
    # Load preprocessed data if not provided
    if preprocessed_data is None:
        preprocessed_data = load_preprocessed_payment_data()
    
    # Filter for specified CPT codes
    cpt_codes_str = [str(code) for code in cpt_codes]
    combined_history = preprocessed_data[preprocessed_data['HCPCS Code'].isin(cpt_codes_str)].copy()
    
    # Filter to January only if requested
    if january_only and not combined_history.empty:
        combined_history = combined_history[combined_history['Month'] == 'January'].copy()
    
    # Sort by CPT code and year for better readability
    combined_history = combined_history.sort_values(['HCPCS Code', 'Year'])
    
    return combined_history


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the payment data loading and preprocessing"""
    combined_df = preprocess_all_payment_data(start_year=2023, end_year=2025)
    loaded_df = load_preprocessed_payment_data()
    
    test_cpt = "97810"
    history = get_payment_history_for_cpt(test_cpt, loaded_df)
    
