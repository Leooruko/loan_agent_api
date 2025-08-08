#!/usr/bin/env python3
"""
Debug semicolon patterns individually.
"""

import pandas as pd

def debug_semicolon_patterns():
    """Debug each semicolon pattern individually"""
    
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
        
        # Test patterns individually
        patterns = [
            "len(pd.read_csv('processed_data.csv'))",
            "df = pd.read_csv('processed_data.csv'); df['Total_Paid'].sum()",
            "df = pd.read_csv('processed_data.csv'); len(df['Client_Code'].unique())",
            "df = pd.read_csv('processed_data.csv'); df['Client_Code'].unique()",
            "pd.read_csv('processed_data.csv')['Client_Code'].unique()"
        ]
        
        for i, pattern in enumerate(patterns, 1):
            try:
                result = eval(pattern, {"__builtins__": __builtins__}, local_namespace)
                print(f"✓ Pattern {i} works: {result}")
            except Exception as e:
                print(f"✗ Pattern {i} fails: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Debugging Semicolon Patterns")
    print("=" * 35)
    debug_semicolon_patterns()
