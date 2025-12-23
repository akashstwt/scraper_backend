"""
Excel handling utilities for reading OEM codes and writing results.
"""
import pandas as pd
import os


def read_oem_codes(filepath):
    """
    Read OEM codes from an Excel file.
    
    Args:
        filepath (str): Path to the Excel file containing OEM codes
        
    Returns:
        list: List of OEM codes
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the Excel file doesn't have an 'OEM_CODE' column
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
    
    if 'OEM_CODE' not in df.columns:
        raise ValueError("Excel file must contain an 'OEM_CODE' column")
    
    # Remove duplicates and NaN values
    oem_codes = df['OEM_CODE'].dropna().unique().tolist()
    
    print(f"📋 Loaded {len(oem_codes)} unique OEM codes from {filepath}")
    return oem_codes


def save_results(results, output_file):
    """
    Save scraping results to an Excel file.
    
    Args:
        results (list): List of dictionaries containing scraped data
        output_file (str): Path to save the output Excel file
        
    Returns:
        bool: True if save was successful
    """
    if not results:
        print("⚠️  No results to save!")
        return False
    
    try:
        df = pd.DataFrame(results)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save to Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✅ Results saved to {output_file}")
        print(f"📊 Total records: {len(df)}")
        
        # Display summary
        if 'Website' in df.columns:
            print("\n🌐 Results by website:")
            print(df['Website'].value_counts().to_string())
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False


def save_results_with_summary(results, output_file):
    """
    Save results with a summary sheet showing statistics.
    
    Args:
        results (list): List of dictionaries containing scraped data
        output_file (str): Path to save the output Excel file
    """
    if not results:
        print("⚠️  No results to save!")
        return False
    
    try:
        df = pd.DataFrame(results)
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write main results
            df.to_excel(writer, sheet_name='Price Comparison', index=False)
            
            # Create summary statistics
            if 'Website' in df.columns and 'Price' in df.columns:
                summary_data = {
                    'Website': df['Website'].unique().tolist(),
                    'Products Found': [len(df[df['Website'] == site]) for site in df['Website'].unique()]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"✅ Results with summary saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False
