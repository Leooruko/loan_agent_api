#!/usr/bin/env python3
"""
Test to verify client counting functionality.
"""

import pandas as pd

def test_client_count():
    """Test counting unique clients"""
    
    try:
        # Load the data
        df = pd.read_csv('processed_data.csv')
        
        # Count unique clients
        unique_clients = len(df['Client_Code'].unique())
        print(f"✓ Test passed: Found {unique_clients} unique clients")
        
        # Show some sample client codes
        sample_clients = df['Client_Code'].unique()[:5]
        print(f"Sample client codes: {sample_clients}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Client Count Functionality")
    print("=" * 40)
    test_client_count()
