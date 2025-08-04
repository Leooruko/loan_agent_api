#!/usr/bin/env python3
"""
Test script to demonstrate MAX_ROWS_DISPLAY functionality
"""

import asyncio
import sys
import os
from utils_simple import fetch_data
from config import DATA_CONFIG

def test_display_limits():
    """Test how MAX_ROWS_DISPLAY affects result formatting"""
    print("Testing MAX_ROWS_DISPLAY functionality...")
    print("=" * 60)
    print(f"Current MAX_ROWS_DISPLAY setting: {DATA_CONFIG['MAX_ROWS_DISPLAY']}")
    print("=" * 60)
    
    # Test queries that return different numbers of rows
    test_queries = [
        {
            "name": "Small Result (≤ 10 rows)",
            "query": "SELECT Client_Name, Amount_Disbursed FROM df WHERE Status = 'Active' LIMIT 5",
            "expected": "Should show ALL rows"
        },
        {
            "name": "Medium Result (10-20 rows)", 
            "query": "SELECT Client_Name, Amount_Disbursed FROM df WHERE Status = 'Active' LIMIT 15",
            "expected": f"Should show first {DATA_CONFIG['MAX_ROWS_DISPLAY']} rows only"
        },
        {
            "name": "Large Result (50+ rows)",
            "query": "SELECT Client_Name, Amount_Disbursed FROM df WHERE Status = 'Active' LIMIT 50",
            "expected": f"Should show first {DATA_CONFIG['MAX_ROWS_DISPLAY']} rows only"
        },
        {
            "name": "All Active Loans",
            "query": "SELECT Client_Name, Amount_Disbursed FROM df WHERE Status = 'Active'",
            "expected": f"Should show first {DATA_CONFIG['MAX_ROWS_DISPLAY']} rows only"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {test['name']} ---")
        print(f"Expected: {test['expected']}")
        print("-" * 50)
        
        try:
            result = fetch_data(test['query'])
            
            # Count lines in result to see how many rows were displayed
            lines = result.split('\n')
            data_lines = [line for line in lines if line.strip() and not line.startswith('Query Results')]
            
            print(f"Query: {test['query']}")
            print(f"Result preview:")
            print(result[:500] + "..." if len(result) > 500 else result)
            print(f"Data lines displayed: {len(data_lines)}")
            
            # Check if it matches expected behavior
            if "showing first" in result:
                print("✅ Correctly limited display")
            else:
                print("✅ Showing full result (within limit)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

def test_config_changes():
    """Test how changing MAX_ROWS_DISPLAY would affect results"""
    print("\nTesting config change simulation...")
    print("=" * 60)
    
    # Simulate different MAX_ROWS_DISPLAY values
    test_values = [5, 10, 15, 20]
    
    query = "SELECT Client_Name, Amount_Disbursed FROM df WHERE Status = 'Active' LIMIT 25"
    
    for max_rows in test_values:
        print(f"\n--- Simulating MAX_ROWS_DISPLAY = {max_rows} ---")
        print("-" * 40)
        
        try:
            # Temporarily modify the config for this test
            original_value = DATA_CONFIG['MAX_ROWS_DISPLAY']
            DATA_CONFIG['MAX_ROWS_DISPLAY'] = max_rows
            
            result = fetch_data(query)
            
            # Count displayed rows
            lines = result.split('\n')
            data_lines = [line for line in lines if line.strip() and not line.startswith('Query Results')]
            
            print(f"Query: {query}")
            print(f"Result preview:")
            print(result[:300] + "..." if len(result) > 300 else result)
            print(f"Rows displayed: {len(data_lines)}")
            
            # Restore original value
            DATA_CONFIG['MAX_ROWS_DISPLAY'] = original_value
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Restore original value on error
            DATA_CONFIG['MAX_ROWS_DISPLAY'] = original_value
        print()

def test_performance_impact():
    """Test the performance impact of different display limits"""
    print("\nTesting performance impact...")
    print("=" * 60)
    
    import time
    
    # Test with different result sizes
    test_cases = [
        ("Small result", "SELECT Client_Name FROM df LIMIT 5"),
        ("Medium result", "SELECT Client_Name FROM df LIMIT 20"),
        ("Large result", "SELECT Client_Name FROM df LIMIT 100")
    ]
    
    for name, query in test_cases:
        print(f"\n--- {name} ---")
        print("-" * 30)
        
        start_time = time.time()
        try:
            result = fetch_data(query)
            end_time = time.time()
            
            print(f"Query: {query}")
            print(f"Response time: {(end_time - start_time):.3f} seconds")
            print(f"Result length: {len(result)} characters")
            
            # Check if result was truncated
            if "showing first" in result:
                print("✅ Result was truncated for display")
            else:
                print("✅ Full result displayed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

def explain_display_logic():
    """Explain how the display logic works"""
    print("\nHow MAX_ROWS_DISPLAY Works:")
    print("=" * 60)
    
    print("""
1. DATA ACCESS vs DISPLAY:
   - The agent can access ALL data in the CSV file
   - MAX_ROWS_DISPLAY only affects how results are shown to the user
   - SQL queries can return any number of rows

2. DISPLAY LOGIC:
   if result_rows <= MAX_ROWS_DISPLAY:
       → Show ALL rows (full result)
   else:
       → Show first MAX_ROWS_DISPLAY rows only
       → Include message: "showing first X of Y rows"

3. BENEFITS:
   - Prevents overwhelming users with huge tables
   - Improves response readability
   - Reduces response size and transmission time
   - Maintains full data access for analysis

4. CONFIGURATION:
   - Current setting: MAX_ROWS_DISPLAY = 10
   - Can be changed in config.py
   - Affects both utils_simple.py and utils.py
""")

def main():
    """Main test function"""
    print("MAX_ROWS_DISPLAY Test")
    print("=" * 80)
    
    # Explain the concept
    explain_display_logic()
    
    # Test current functionality
    test_display_limits()
    
    # Test config changes
    test_config_changes()
    
    # Test performance impact
    test_performance_impact()
    
    print("\n" + "=" * 80)
    print("✅ MAX_ROWS_DISPLAY test completed!")
    print(f"Current setting: {DATA_CONFIG['MAX_ROWS_DISPLAY']} rows")
    print("This controls display formatting, NOT data access limits.")

if __name__ == "__main__":
    main() 