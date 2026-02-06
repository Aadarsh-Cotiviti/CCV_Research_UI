"""
CPT Code Description Comparison Tool

This module compares CPT code descriptions between 2025 and 2026 to identify changes.
"""

import os
import pandas as pd
from typing import Tuple, Dict
from ..storage import fileStorage

def load_cpt_descriptions(file_path: str, year: str) -> pd.DataFrame:
    """
    Load CPT codes and descriptions from Excel file
    
    Args:
        file_path: Path to Excel file
        year: Year label (e.g., "2025", "2026")
        
    Returns:
        DataFrame with CPT codes and descriptions
    """
    if not fileStorage.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read first sheet
    df = pd.read_excel(fileStorage.read_bytes(file_path), sheet_name=0)
    
    print(f"📄 Loading {year} CPT descriptions from: {file_path}")
    print(f"   Columns found: {df.columns.tolist()}")
    
    # Try to identify CPT code and description columns
    # Common column names variations
    cpt_col = None
    desc_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'cpt' in col_lower or 'code' in col_lower or 'hcpcs' in col_lower:
            if cpt_col is None:
                cpt_col = col
        if 'desc' in col_lower or 'description' in col_lower:
            if desc_col is None:
                desc_col = col
    
    if cpt_col is None or desc_col is None:
        raise ValueError(f"Could not identify CPT code and description columns. Available columns: {df.columns.tolist()}")
    
    # Extract and clean data
    df_clean = df[[cpt_col, desc_col]].copy()
    df_clean.columns = ['CPT_Code', f'Description_{year}']
    
    # Remove rows with missing CPT codes
    df_clean = df_clean.dropna(subset=['CPT_Code'])
    
    # Convert CPT code to string and clean
    df_clean['CPT_Code'] = df_clean['CPT_Code'].astype(str).str.strip()
    
    # Clean descriptions
    df_clean[f'Description_{year}'] = df_clean[f'Description_{year}'].fillna('').astype(str).str.strip()
    
    print(f"   ✅ Loaded {len(df_clean)} CPT codes for {year}")
    
    return df_clean


def compare_descriptions(df_2025: pd.DataFrame, df_2026: pd.DataFrame) -> pd.DataFrame:
    """
    Compare CPT descriptions between 2025 and 2026
    
    Args:
        df_2025: DataFrame with 2025 descriptions
        df_2026: DataFrame with 2026 descriptions
        
    Returns:
        Merged DataFrame with comparison results
    """
    print("\n🔍 Comparing descriptions between 2025 and 2026...")
    
    # Merge the two dataframes
    merged = pd.merge(
        df_2025,
        df_2026,
        on='CPT_Code',
        how='outer',
        indicator=True
    )
    
    # Add status flags
    merged['Status'] = merged['_merge'].map({
        'left_only': 'Removed in 2026',
        'right_only': 'New in 2026',
        'both': 'Exists in both'
    })
    
    # Check if descriptions changed
    def check_description_change(row):
        if row['_merge'] == 'both':
            desc_2025 = str(row['Description_2025']).strip().lower()
            desc_2026 = str(row['Description_2026']).strip().lower()
            if desc_2025 != desc_2026:
                return 'Changed'
            else:
                return 'Unchanged'
        else:
            return 'N/A'
    
    merged['Description_Change'] = merged.apply(check_description_change, axis=1)
    
    # Drop the merge indicator column
    merged = merged.drop('_merge', axis=1)
    
    # Reorder columns
    column_order = ['CPT_Code', 'Status', 'Description_Change', 'Description_2025', 'Description_2026']
    merged = merged[column_order]
    
    # Sort by CPT code
    merged = merged.sort_values('CPT_Code')
    
    # Print statistics
    print("\n📊 Comparison Statistics:")
    print(f"   Total CPT codes analyzed: {len(merged)}")
    print(f"   Codes in both years: {len(merged[merged['Status'] == 'Exists in both'])}")
    print(f"   Removed in 2026: {len(merged[merged['Status'] == 'Removed in 2026'])}")
    print(f"   New in 2026: {len(merged[merged['Status'] == 'New in 2026'])}")
    print(f"   Description changed: {len(merged[merged['Description_Change'] == 'Changed'])}")
    print(f"   Description unchanged: {len(merged[merged['Description_Change'] == 'Unchanged'])}")
    
    return merged


def analyze_cpt_description_changes(
    file_2025: str = None,
    file_2026: str = None,
    output_dir: str = None
) -> Dict[str, pd.DataFrame]:
    """
    Main function to analyze CPT description changes between 2025 and 2026
    
    Args:
        file_2025: Path to 2025 Excel file. If None, uses default.
        file_2026: Path to 2026 Excel file. If None, uses default.
        output_dir: Directory to save comparison results. If None, uses default.
        
    Returns:
        Dictionary with three DataFrames: 'full_comparison', 'new_in_2026', 'removed_in_2026'
    """
    # Default paths
    if file_2025 is None:
        file_2025 = fileStorage.get_path('data', 'CPT Codes with Long Descriptions 2025.xlsx')
    
    if file_2026 is None:
        file_2026 = fileStorage.get_path('data', 'CPT Codes with Long Descriptions 2026.xlsx')
    
    if output_dir is None:
        output_dir = fileStorage.get_path('output', '2025_2026_cpt_changes')
    
    
    print("=" * 80)
    print("CPT Code Description Comparison Analysis (2025 vs 2026)")
    print("=" * 80)
    
    # Load both files
    df_2025 = load_cpt_descriptions(file_2025, "2025")
    df_2026 = load_cpt_descriptions(file_2026, "2026")
    
    # Compare descriptions
    comparison_df = compare_descriptions(df_2025, df_2026)
    
    # Generate three tables
    print("\n📁 Generating output tables...")
    
    # Table 1: Full comparison (all CPT codes)
    full_comparison_path = os.path.join(output_dir, 'full_comparison_2025_2026.csv')
    comparison_df.to_csv(full_comparison_path, index=False, encoding='utf-8')
    print(f"   ✅ Saved full comparison to: {full_comparison_path}")
    
    # Table 2: New codes in 2026
    new_codes = comparison_df[comparison_df['Status'] == 'New in 2026'].copy()
    new_codes_path = os.path.join(output_dir, 'new_codes_2026.csv')
    new_codes.to_csv(new_codes_path, index=False, encoding='utf-8')
    print(f"   ✅ Saved new codes (2026) to: {new_codes_path}")
    print(f"      Total new codes: {len(new_codes)}")
    
    # Table 3: Removed codes (in 2025 but not in 2026)
    removed_codes = comparison_df[comparison_df['Status'] == 'Removed in 2026'].copy()
    removed_codes_path = os.path.join(output_dir, 'removed_codes_2026.csv')
    removed_codes.to_csv(removed_codes_path, index=False, encoding='utf-8')
    print(f"   ✅ Saved removed codes to: {removed_codes_path}")
    print(f"      Total removed codes: {len(removed_codes)}")
    
    print(f"\n✅ All tables saved to: {output_dir}")
    
    return {
        'full_comparison': comparison_df,
        'new_in_2026': new_codes,
        'removed_in_2026': removed_codes
    }


def get_changed_descriptions(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to only show CPT codes with changed descriptions
    
    Args:
        comparison_df: Full comparison DataFrame
        
    Returns:
        DataFrame with only changed descriptions
    """
    changed = comparison_df[comparison_df['Description_Change'] == 'Changed'].copy()
    print(f"\n📝 Found {len(changed)} CPT codes with changed descriptions")
    return changed


def get_new_codes(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to only show new CPT codes in 2026
    
    Args:
        comparison_df: Full comparison DataFrame
        
    Returns:
        DataFrame with only new codes
    """
    new_codes = comparison_df[comparison_df['Status'] == 'New in 2026'].copy()
    print(f"\n🆕 Found {len(new_codes)} new CPT codes in 2026")
    return new_codes


def get_removed_codes(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to only show removed CPT codes
    
    Args:
        comparison_df: Full comparison DataFrame
        
    Returns:
        DataFrame with only removed codes
    """
    removed = comparison_df[comparison_df['Status'] == 'Removed in 2026'].copy()
    print(f"\n❌ Found {len(removed)} CPT codes removed in 2026")
    return removed


# ==================== Test Function ====================

if __name__ == "__main__":
    """Test the CPT description comparison"""
    
    # Run full analysis and get all three tables
    results = analyze_cpt_description_changes()
    
    full_comparison = results['full_comparison']
    new_codes = results['new_in_2026']
    removed_codes = results['removed_in_2026']
    
    print("\n" + "=" * 80)
    print("SUMMARY OF CHANGES")
    print("=" * 80)
    
    # Changed descriptions
    changed = full_comparison[full_comparison['Description_Change'] == 'Changed']
    print(f"\n📝 Description Changes:")
    print(f"   Total codes with changed descriptions: {len(changed)}")
    if not changed.empty:
        print("\n   Sample of changed descriptions (first 3):")
        for idx, row in changed.head(3).iterrows():
            print(f"\n   CPT {row['CPT_Code']}:")
            print(f"      2025: {row['Description_2025'][:80]}...")
            print(f"      2026: {row['Description_2026'][:80]}...")
    
    # New codes
    print(f"\n🆕 New Codes in 2026:")
    print(f"   Total new codes: {len(new_codes)}")
    if not new_codes.empty:
        print("\n   Sample of new codes (first 5):")
        for idx, row in new_codes.head(5).iterrows():
            print(f"      {row['CPT_Code']}: {row['Description_2026'][:60]}...")
    
    # Removed codes
    print(f"\n❌ Removed Codes in 2026:")
    print(f"   Total removed codes: {len(removed_codes)}")
    if not removed_codes.empty:
        print("\n   Sample of removed codes (first 5):")
        for idx, row in removed_codes.head(5).iterrows():
            print(f"      {row['CPT_Code']}: {row['Description_2025'][:60]}...")
