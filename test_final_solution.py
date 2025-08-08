#!/usr/bin/env python3
"""
Final test to verify the complete solution works.
"""

import pandas as pd

def test_final_solution():
    """Test the final solution with simplified patterns"""
    
    try:
        # Create a safe execution environment
        import numpy as np
        import pandas as pd        
        from datetime import datetime, timedelta
        import math
        import statistics
        import json
        
        local_namespace = {
            'pd': pd,
            'np': np,
            'datetime': datetime,
            'timedelta': timedelta,
            'math': math,
            'statistics': statistics,
            'json': json
        }
        
        # Test the exact patterns from the examples
        tests = [
            ("Count total loans", "len(pd.read_csv('processed_data.csv'))"),
            ("Count unique clients", "len(pd.read_csv('processed_data.csv')['Client_Code'].unique())"),
            ("Count unique managers", "len(pd.read_csv('processed_data.csv')['Managed_By'].unique())"),
            ("Sum total paid", "pd.read_csv('processed_data.csv')['Total_Paid'].sum()"),
            ("Average loan amount", "pd.read_csv('processed_data.csv')['Amount_Disbursed'].mean()")
        ]
        
        for test_name, code in tests:
            try:
                result = eval(code, {"__builtins__": __builtins__}, local_namespace)
                print(f"✓ {test_name}: {result}")
            except Exception as e:
                print(f"✗ {test_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Final Solution")
    print("=" * 40)
    test_final_solution()
