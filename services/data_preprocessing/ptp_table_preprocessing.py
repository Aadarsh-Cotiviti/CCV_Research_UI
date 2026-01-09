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
        import pdb; pdb.set_trace()
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
    
    # Define standard column names
    column_mapping = {
        'Column 1': 'Code_1',
        'Column 2': 'Code_2',
        '*=in existence': 'In_Existence',
        'Effective': 'Effective_Date',
        'Deletion': 'Deletion_Date',
        'Modifier': 'Modifier',
        'PTP Edit Rationale': 'PTP_Edit_Rationale'
    }
    
    # Rename columns that exist in the mapping
    df_cleaned = df.rename(columns=column_mapping)
    
    # Remove any unnamed columns
    df_cleaned = df_cleaned.loc[:, ~df_cleaned.columns.str.contains('^Unnamed')]
    
    print(f"📋 Cleaned columns: {list(df_cleaned.columns)}")
    
    return df_cleaned



def save_to_local(df, filename="ptp_edit_table.csv"):
    """
    Save processed data to local data folder
    
    Args:
        df: DataFrame to save
        filename: Output filename
        
    Returns:
        Path to saved file
    """
    print(f"\n💾 Saving to local data folder...")
    
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_folder = os.path.join(project_root, 'data')
    
    # Create data folder if it doesn't exist
    os.makedirs(data_folder, exist_ok=True)
    
    output_path = os.path.join(data_folder, filename)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"✅ Saved to: {output_path}")
    print(f"   Records: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    return output_path


def main():
    """Main preprocessing pipeline"""
    print("=" * 80)
    print("PTP Edit Table Download and Preprocessing")
    print("=" * 80)
    
    # Step 1: Download from S3
    df = download_ptp_table_from_s3()
    
    # Step 2: Clean column names
    df_cleaned = clean_column_names(df)
    
    # Step 3: Preview data
    print(f"\n🔍 Data preview:")
    print(df_cleaned.head())
    
    # Step 4: Save to local data folder
    output_path = save_to_local(df_cleaned)
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total records: {len(df_cleaned)}")
    print(f"Columns: {list(df_cleaned.columns)}")
    
    if 'Effective_Date' in df_cleaned.columns:
        print(f"\nEffective Date Range:")
        print(f"   Earliest: {df_cleaned['Effective_Date'].min()}")
        print(f"   Latest: {df_cleaned['Effective_Date'].max()}")
    
    if 'Code_1' in df_cleaned.columns:
        print(f"\nUnique Code_1 values: {df_cleaned['Code_1'].nunique()}")
    
    if 'Code_2' in df_cleaned.columns:
        print(f"Unique Code_2 values: {df_cleaned['Code_2'].nunique()}")
    
    print("\n" + "=" * 80)
    print("✅ Processing Complete!")
    print(f"📁 Output file: {output_path}")
    print("=" * 80)
    
    return df_cleaned, output_path


if __name__ == "__main__":
    main()
