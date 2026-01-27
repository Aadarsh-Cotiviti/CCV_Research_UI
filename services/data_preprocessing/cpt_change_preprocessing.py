#python -m services.data_preprocessing.cpt_change_preprocessing
"""
Data Cleaning Script for CPT Change Tracking
Preprocesses combined parquet files to create clean CPT change tracking data
"""

import pandas as pd
from datetime import datetime
import os
from services.utils import load_s3_parquet_files

def load_combined_parquet(file_path):
    """
    Load combined parquet file
    
    Args:
        file_path: Path to combined parquet file
        s3_folder_path: S3 folder path to load parquet files from (optional)
    Returns:
        DataFrame with loaded data
    """
    print(f"📂 Loading parquet file: {file_path}")
    df = pd.read_parquet(file_path)
    print(f"✅ Loaded {len(df)} records")
    # Loaded 407,727 rows, 17 columns 
    # Columns: ['CPTCd', 'ChangeType', 'OriginalStart', 'VersionEnd', 'RevisedStart', 
    # 'DateTerm', 'StatusInd', 'ReplCodeXwalk', 'OldDesc', 'NewDesc', 'ReleaseDt', 'EffectiveDt',
    #  'EndDt', 'LastUpdateUser', 'SFileDate', 'SFileName', 'AutoId']
    print(f"📊 Columns: {list(df.columns)}")
    return df


def check_duplicates(df):
    """
    Check for duplicate records
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with duplicates info
    """
    print("\n🔍 Checking for duplicate records...")
    
    # Count total duplicates
    total_duplicates = df.duplicated().sum()
    print(f"   Total duplicate rows: {total_duplicates}")
    
    # Check duplicates based on CPT code and effective date
    if 'CPTCd' in df.columns and 'EffectiveDt' in df.columns:
        key_duplicates = df.duplicated(subset=['CPTCd', 'EffectiveDt']).sum()
        print(f"   Duplicates by CPT code + effective date: {key_duplicates}")
        
        if key_duplicates > 0:
            print("\n📋 Sample duplicate records:")
            duplicated_df = df[df.duplicated(subset=['CPTCd', 'EffectiveDt'], keep=False)]
            print(duplicated_df[['CPTCd', 'EffectiveDt', 'ChangeType']].head(10))
            return duplicated_df
    
    return None


def clean_and_filter_data(df):
    """
    Clean and filter CPT change data
    
    Filters:
    - End date > today (current valid changes)
    - Changes in 2025 and 2026
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned and filtered DataFrame
    """
    print("\n🧹 Cleaning and filtering data...")
    
    today = datetime.now()
    print(f"   Today's date: {today.date()}")
    
    # Create working copy
    df_clean = df.copy()
    
    # Convert date columns to datetime if they're not already
    date_columns = ['EffectiveDt', 'EndDt']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    initial_count = len(df_clean)
    print(f"   Initial records: {initial_count}")
    
    # Filter 1: ChangeType = 'N' or 'C' (New or Changed)
    if 'ChangeType' in df_clean.columns:
        df_clean = df_clean[df_clean['ChangeType'].isin(['N', 'C'])]
        print(f"   After filtering ChangeType N/C: {len(df_clean)} records")
  
    # Filter 2: Changes in 2023, 2024 and 2025
    if 'EffectiveDt' in df_clean.columns:
        df_clean = df_clean[
            (df_clean['EffectiveDt'].dt.year == 2023) | 
            (df_clean['EffectiveDt'].dt.year == 2024) |
            (df_clean['EffectiveDt'].dt.year == 2025)
        ]
        print(f"   After filtering 2023-2025 changes: {len(df_clean)} records")
    
    # Remove duplicates (keep first occurrence)
    df_clean = df_clean.drop_duplicates(subset=['CPTCd', 'EffectiveDt'], keep='first')
    print(f"   After removing duplicates: {len(df_clean)} records")
    
    print(f"   Total records removed: {initial_count - len(df_clean)}")
    
    return df_clean


def create_preprocessed_table(df):
    """
    Create preprocessed CPT change tracking table with required columns
    
    Columns:
    - CPTCd: CPT code
    - ChangeType: Change type (N/C)
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
    required_columns = ['CPTCd', 'ChangeType', 'OldDesc', 'NewDesc', 'EffectiveDt', 'EndDt']
    
    # Check which columns exist
    available_columns = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"   ⚠️  Missing columns: {missing_columns}")
        print(f"   Available columns in data: {list(df.columns)}")
    
    # Create table with available columns
    df_preprocessed = df[available_columns].copy()
    
    # Sort by CPT code and effective date
    if 'CPTCd' in df_preprocessed.columns and 'EffectiveDt' in df_preprocessed.columns:
        df_preprocessed = df_preprocessed.sort_values(['CPTCd', 'EffectiveDt'])
    
    print(f"   ✅ Preprocessed table created with {len(df_preprocessed)} records")
    print(f"   Columns: {list(df_preprocessed.columns)}")
    
    return df_preprocessed


def save_to_csv(df, output_path):
    """
    Save preprocessed data to CSV
    
    Args:
        df: DataFrame to save
        output_path: Output file path
    """
    print(f"\n💾 Saving to CSV: {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"   ✅ Saved {len(df)} records to {output_path}")
    
   

# ==================== Main Execution ====================

if __name__ == "__main__":
    print("CPT CHANGE TRACKING - DATA CLEANING")
    
    df = load_s3_parquet_files(
        s3_folder_path="AI-Research/data/ml_globalhccnlymedicalcodeslibrary/Ing_CPTChange/"
    ) # output saved to local under 'data' folder: ing_cptchange_combined.parquet
    
    # Configuration
    INPUT_FILE = "data/ing_cptchange_combined.parquet"  # Update this path
    OUTPUT_FILE = "output/preprocessed_cpt_change_tracking.csv"
    
    try:
        # Step 1: Load combined parquet file
        df = load_combined_parquet(INPUT_FILE)
        
        # Step 2: Check for duplicates
        duplicates = check_duplicates(df)
        
        # Step 3: Clean and filter data
        df_clean = clean_and_filter_data(df)
        
        # Step 4: Create preprocessed table
        df_preprocessed = create_preprocessed_table(df_clean)
        
        # Step 5: Save to CSV
        save_to_csv(df_preprocessed, OUTPUT_FILE)
    
        print("\n✅ Data cleaning completed successfully!")
        
    except FileNotFoundError:
        print(f"\n❌ Error: Input file not found: {INPUT_FILE}")
        print("   Please update the INPUT_FILE path in the script")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

