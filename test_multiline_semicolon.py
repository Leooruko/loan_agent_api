#!/usr/bin/env python3
"""
Test the multi-line semicolon approach.
"""

import pandas as pd

def test_multiline_semicolon():
    """Test multi-line code with semicolons"""
    
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
        
        # Test the multi-line semicolon pattern
        tests = [
            ("Simple count", "len(pd.read_csv('processed_data.csv'))"),
            ("Best manager", "df = pd.read_csv('processed_data.csv'); top_manager = df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1); manager_name = top_manager.index[0]; manager_name"),
            ("Total paid", "df = pd.read_csv('processed_data.csv'); df['Total_Paid'].sum()"),
            ("Unique clients", "df = pd.read_csv('processed_data.csv'); len(df['Client_Code'].unique())")
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
    print("Testing Multi-line Semicolon Approach")
    print("=" * 45)
    test_multiline_semicolon()
