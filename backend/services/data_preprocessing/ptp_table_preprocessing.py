#python -m services.data_preprocessing.ptp_table_preprocessing
"""
PTP Edit Table Download and Preprocessing Script
Downloads PTP edit table from S3 and processes it with correct headers
"""

import pandas as pd
from datetime import datetime
import os
import boto3
from io import BytesIO
from pathlib import Path
from ..storage import fileStorage

def download_ptp_table_from_s3():
    """
    Download PTP edit table from S3 and save to local data folder
    
    S3 Path: s3://ml-ccv-unrestricted/AI-Research/webcrawling/CMS/Medicare NCCI Procedure to Procedure (PTP) Edits/Oct2025/Practitioner PTP Edits v313r0 (675130 Records) 2552501810 -- 37700G0471_110126_08102025/ccipra-v313r0-f2.xlsx
    Tab: ccipra-v313r0-f2
    
    Returns:
        DataFrame with processed PTP edit data
    """
    print("📥 Downloading PTP edit table from S3...")
    
    # S3 configuration
    bucket_name = "ml-ccv-unrestricted"
    s3_key = "AI-Research/webcrawling/CMS/Medicare NCCI Procedure to Procedure (PTP) Edits/Oct2025/Practitioner PTP Edits v313r0 (675130 Records) 2552501810 -- 37700G0471_110126_08102025/ccipra-v313r0-f2.xlsx"
    sheet_name = "ccipra-v313r0-f2"
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        excel_data = response['Body'].read()
        
        print(f"✅ Downloaded {len(excel_data)} bytes from S3")
        
        # Read Excel file from memory
        # Row 0-2: top headers
        # Row 3: actual column headers
        # Rows 4-6: skip these rows
        # Row 7+: data starts
        print(f"\n📊 Reading Excel sheet: {sheet_name}")
        
        # Read with skiprows to skip rows 4, 5, 6 (0-indexed)
        # Use row 3 (0-indexed) as header
        df = pd.read_excel(
            BytesIO(excel_data),
            sheet_name=sheet_name,
            header=2,  # Use row 2 (0-indexed) as header
            skiprows=[3, 4, 5]  # Skip rows 3, 4, 5 (0-indexed)
        )
        print(f"✅ Loaded {len(df)} records")
        print(f"📋 Original columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading from S3: {str(e)}")
        raise



def clean_column_names(df):
    """
    Clean and standardize column names
    
    Expected columns based on attachment:
    - Column 1 (CPT/HCPCS code)
    - Column 2 (CPT/HCPCS code) 
    - *= in existence
    - Effective
    - Deletion
    - Modifier
    - PTP Edit Rationale
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with cleaned column names
    """
    print("\n🔄 Cleaning column names...")
    print(f"   Original columns: {list(df.columns)}")
    
    # Define standard column names based on actual Excel structure
    # You can also rename by position if column names vary
    column_mapping = {
        'Column 1': 'CPT_code_1',
        'Column 2': 'CPT_code_2',
        '*=in existence': 'In_Existence',
        'Effective': 'Effective_Date',
        'Deletion': 'Deletion_Date',
        'Modifier': 'Modifier',
        'PTP Edit Rationale': 'PTP_Edit_Rationale'
    }
    
    # Alternative: Rename by column position (more robust if column names have variations)
    # df.columns = ['CPT_code_1', 'CPT_code_2', 'In_Existence', 'Effective_Date', 'Deletion_Date', 'Modifier', 'PTP_Edit_Rationale']
    
    # Rename columns that exist in the mapping
    df_cleaned = df.rename(columns=column_mapping)
    
    # Remove any unnamed columns
    df_cleaned = df_cleaned.loc[:, ~df_cleaned.columns.str.contains('^Unnamed', na=False)]
    
    print(f"📋 Cleaned columns: {list(df_cleaned.columns)}")
    return df_cleaned

def subset_save_df(df):
    """
    Subset DataFrame and save to local data folder
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (modifier_0_filename, modifier_1_filename)
    """
    print("\n💾 Subsetting and saving PTP edit data...")
    output_dir = Path("output")
    os.makedirs(output_dir, exist_ok=True)
    modifier_0_filename = fileStorage.get_path("data", "preprocessed_ptp_edit_table_modifier0.csv")
    modifier_1_filename = fileStorage.get_path("data", "preprocessed_ptp_edit_table_modifier1.csv")
   
    # Convert Effective_Date to numeric for comparison if it's not already
    # Ensure proper date comparison (20230101 format)
    # Note: Deletion_Date uses '*' to indicate "no deletion date", not NaN
    print(f"   Filtering records with Effective_Date >= 20230101 and Deletion_Date='*' (active records)...")
    
    modifier_0_df = df[(df['Modifier'] == 0) & (df['Effective_Date'] >= 20230101) & (df['Deletion_Date'] == '*')]
    modifier_1_df = df[(df['Modifier'] == 1) & (df['Effective_Date'] >= 20230101) & (df['Deletion_Date'] == '*')]
    
    print(f"   Modifier 0 (not allowed): {len(modifier_0_df)} records")
    print(f"   Modifier 1 (allowed): {len(modifier_1_df)} records")
    
    # Save to CSV
    fileStorage.write_csv(modifier_0_filename, modifier_0_df)
    fileStorage.write_csv(modifier_1_filename, modifier_1_df)
    
    print(f"✅ Saved Modifier 0 data to: {modifier_0_filename}")
    print(f"✅ Saved Modifier 1 data to: {modifier_1_filename}")
    
    return modifier_0_filename, modifier_1_filename

def main():
    """Main preprocessing pipeline"""
    print("=" * 80)
    print("PTP Edit Table Download and Preprocessing")
    print("=" * 80)
    
    # Step 1: Download from S3
    df = download_ptp_table_from_s3()
    
    # Step 2: Clean column names
    df_cleaned = clean_column_names(df)
    
    # Step 3: Basic data quality checks
    print("\n📊 Data Quality Summary:")
    print(f"   Total records: {len(df_cleaned)}")
    print(f"   Modifier distribution:")
    print(f"      {df_cleaned['Modifier'].value_counts().to_dict()}")
    print(f"   Date range:")
    print(f"      Effective: {df_cleaned['Effective_Date'].min()} to {df_cleaned['Effective_Date'].max()}")
    print(f"   Records with Deletion Date: {df_cleaned['Deletion_Date'].notna().sum()}")
    
    # Step 4: Save to local data folder
    modifier_0_filename, modifier_1_filename = subset_save_df(df_cleaned)
    
    print("\n" + "=" * 80)
    print("✅ PTP Edit Table Preprocessing Complete!")
    print("=" * 80)
    
    return df_cleaned, modifier_0_filename, modifier_1_filename

if __name__ == "__main__":
    main()
