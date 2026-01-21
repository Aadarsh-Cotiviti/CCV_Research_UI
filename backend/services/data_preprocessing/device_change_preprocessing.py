#python -m services.data_preprocessing.device_change_preprocessing
"""
Data Cleaning Script for HCPCS Device Code Change Tracking
Preprocesses combined parquet files to create clean device code change tracking data
"""

import pandas as pd
from datetime import datetime
import os
from services.utils import load_s3_parquet_files


def load_and_merge_parquets(s3_folder_path):
    """
    Load and merge all parquet files from S3 folder
    
    Args:
        s3_folder_path: S3 folder path containing parquet files
        
    Returns:
        Combined DataFrame with all data
    """
    print(f"📂 Loading parquet files from: {s3_folder_path}")
    
    # Load all parquet files
    df = load_s3_parquet_files(s3_folder_path)
    
    print(f"✅ Loaded {len(df)} total records")
    print(f"📊 Columns: {list(df.columns)}")
    
    return df


def standardize_column_names(df):
    """
    Standardize column names across different parquet files
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    print("\n🔄 Standardizing column names...")
    
    # Define column name mappings (handle variations)
    column_mapping = {
        'HCPCSCode': 'hcpcscode',
        'Change_Type': 'ChangeType',
        'OldDesc': 'OldDesc',
        'NewDesc': 'NewDesc',
        'EffectiveDt': 'EffectiveDt',
        'EndDt': 'EndDt'
    }
    
    # Rename columns that exist in the mapping
    df_renamed = df.rename(columns=column_mapping)
    
    print(f"   Columns after standardization: {list(df_renamed.columns)}")
    
    return df_renamed


def deduplicate(df):
    """
    Remove duplicate records based on key columns
    
    Deduplication strategy:
    - Key columns: hcpcscode, ChangeType, EffectiveDt
    - Priority: Records with both OldDesc and NewDesc > one desc > no desc
    
    Args:
        df: DataFrame with standardized column names
        
    Returns:
        DataFrame with duplicates removed
    """
    print("\n🔍 Removing duplicate records...")
    
    initial_count = len(df)
    
    # Check if key columns exist
    required_cols = ['hcpcscode', 'ChangeType', 'EffectiveDt']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"   ⚠️  Warning: Missing key columns {missing_cols}, skipping deduplication")
        return df
    
    print(f"   Deduplication keys: {required_cols}")
    
    # Smart deduplication: prioritize records with descriptions
    if 'OldDesc' in df.columns and 'NewDesc' in df.columns:
        print(f"   Prioritizing records with non-null descriptions...")
        
        # Create priority column (lower is better)
        # 0 = both OldDesc and NewDesc have values
        # 1 = only one has value  
        # 2 = both are null
        df['_priority'] = 2
        df.loc[df['OldDesc'].notna() | df['NewDesc'].notna(), '_priority'] = 1
        df.loc[df['OldDesc'].notna() & df['NewDesc'].notna(), '_priority'] = 0
        
        # Sort by key columns and priority
        df = df.sort_values(by=['hcpcscode', 'ChangeType', 'EffectiveDt', '_priority'])
        
        # Drop duplicates keeping first (best priority)
        df = df.drop_duplicates(subset=['hcpcscode', 'ChangeType', 'EffectiveDt'], keep='first')
        
        # Remove priority column
        df = df.drop(columns=['_priority'])
    else:
        # Simple deduplication if description columns not found
        df = df.drop_duplicates(subset=['hcpcscode', 'ChangeType', 'EffectiveDt'], keep='first')
    
    removed_count = initial_count - len(df)
    print(f"   Removed {removed_count} duplicate records ({removed_count/initial_count*100:.2f}%)")
    print(f"   Remaining records: {len(df)}")
    
    return df


def clean_and_filter_data(df):
    """
    Clean and filter HCPCS device code change data
    
    Filters:
    - ChangeType in ['N', 'C', 'R', 'D']
    - Effective date in 2023, 2024, or 2025
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned and filtered DataFrame
    """
    print("\n🧹 Cleaning and filtering data...")
    
    # Create working copy
    df_clean = df.copy()
    
    # Convert date columns to datetime if they're not already
    date_columns = ['EffectiveDt', 'EndDt']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    initial_count = len(df_clean)
    print(f"   Initial records: {initial_count}")
    
    # Filter: ChangeType = 'N', 'C', 'R', or 'D'
    if 'ChangeType' in df_clean.columns:
        df_clean = df_clean[df_clean['ChangeType'].isin(['N', 'C', 'R', 'D'])]
        print(f"   After filtering ChangeType N/C/R/D: {len(df_clean)} records")
    
    # Filter: Changes in 2023, 2024 and 2025
    if 'EffectiveDt' in df_clean.columns:
        df_clean = df_clean[
            (df_clean['EffectiveDt'].dt.year == 2023) | 
            (df_clean['EffectiveDt'].dt.year == 2024) |
            (df_clean['EffectiveDt'].dt.year == 2025)
        ]
        print(f"   After filtering 2023-2025 changes: {len(df_clean)} records")
    
    print(f"   Total records removed: {initial_count - len(df_clean)}")
    
    return df_clean


def create_preprocessed_table(df):
    """
    Create preprocessed HCPCS device code change tracking table
    
    Columns:
    - hcpcscode: HCPCS code
    - ChangeType: Change type (N/C/R/D)
    - OldDesc: Old description
    - NewDesc: New description
    - EffectiveDt: Effective date
    - EndDt: End date
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        DataFrame with required columns only
    """
    print("\n📋 Creating preprocessed table...")
    
    # Define required columns
    required_columns = ['hcpcscode', 'ChangeType', 'OldDesc', 'NewDesc', 'EffectiveDt', 'EndDt']
    
    # Check which columns exist
    available_columns = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"   ⚠️  Missing columns: {missing_columns}")
        print(f"   Available columns in data: {list(df.columns)}")
    
    # Create table with available columns
    df_preprocessed = df[available_columns].copy()
    
    # Sort by HCPCS code and effective date
    if 'hcpcscode' in df_preprocessed.columns and 'EffectiveDt' in df_preprocessed.columns:
        df_preprocessed = df_preprocessed.sort_values(['hcpcscode', 'EffectiveDt'])
    
    print(f"   ✅ Created table with {len(df_preprocessed)} records and {len(available_columns)} columns")
    
    return df_preprocessed


def save_preprocessed_data(df, output_path):
    """
    Save preprocessed data to CSV file
    
    Args:
        df: Preprocessed DataFrame
        output_path: Output file path
    """
    print(f"\n💾 Saving preprocessed data...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"   ✅ Saved {len(df)} records to: {output_path}")
    print(f"   File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")


def main():
    """Main preprocessing pipeline"""
    print("=" * 80)
    print("HCPCS Device Code Change Preprocessing Pipeline")
    print("=" * 80)
    
    # Configuration
    S3_FOLDER_PATH = "AI-Research/data/ml_globalhccnlymedicalcodeslibrary/Ing_HCPCSChange/"
    OUTPUT_FILE = "output/preprocessed_device_code_change_tracking.csv"
    
    # Step 1: Load and merge all parquet files
    df_combined = load_and_merge_parquets(S3_FOLDER_PATH)
    
    # Step 2: Standardize column names
    df_standardized = standardize_column_names(df_combined)
    
    # Step 3: Remove duplicates
    df_deduped = deduplicate(df_standardized)
    
    # Step 4: Clean and filter data
    df_cleaned = clean_and_filter_data(df_deduped)
    
    # Step 5: Create preprocessed table
    df_preprocessed = create_preprocessed_table(df_cleaned)
    
    # Step 6: Save to CSV
    save_preprocessed_data(df_preprocessed, OUTPUT_FILE)
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    if 'ChangeType' in df_preprocessed.columns:
        print("\nChange Type Distribution:")
        print(df_preprocessed['ChangeType'].value_counts())
    
    if 'EffectiveDt' in df_preprocessed.columns:
        print("\nEffective Date Range:")
        print(f"   Earliest: {df_preprocessed['EffectiveDt'].min()}")
        print(f"   Latest: {df_preprocessed['EffectiveDt'].max()}")
    
    print("\n✅ Preprocessing completed successfully!")


if __name__ == "__main__":
    main()
