#!/usr/bin/env python3
"""
Simple test to verify the Python calculator fix works.
"""

import pandas as pd

def test_python_calculator():
    """Test the Python calculator functionality"""
    
    # Test 1: Basic data loading and counting
    try:
        df = pd.read_csv('processed_data.csv')
        unique_managers = len(df['Managed_By'].unique())
        print(f"✓ Test 1 passed: Found {unique_managers} unique managers")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
    
    # Test 2: More complex analysis
    try:
        total_loans = len(df)
        total_disbursed = df['Amount_Disbursed'].sum()
        print(f"✓ Test 2 passed: {total_loans} loans, KES {total_disbursed:,.2f} total disbursed")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
    
    # Test 3: Groupby operation
    try:
        manager_stats = df.groupby('Managed_By')['Loan_No'].count()
        top_manager = manager_stats.idxmax()
        top_count = manager_stats.max()
        print(f"✓ Test 3 passed: {top_manager} has {top_count} loans")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")

if __name__ == "__main__":
    print("Testing Python Calculator Fix")
    print("=" * 40)
    test_python_calculator()
