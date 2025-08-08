#!/usr/bin/env python3
"""
Debug the exact pattern that works.
"""

import pandas as pd

def test_patterns():
    """Test different patterns to find the working one"""
    
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
    
    # Test different patterns
    patterns = [
        "len(pd.read_csv('processed_data.csv'))",
        "len(pd.read_csv('processed_data.csv')['Client_Code'].unique())",
        "pd.read_csv('processed_data.csv')['Total_Paid'].sum()",
        "pd.read_csv('processed_data.csv')['Amount_Disbursed'].mean()"
    ]
    
    for i, pattern in enumerate(patterns, 1):
        try:
            result = eval(pattern, {"__builtins__": __builtins__}, local_namespace)
            print(f"✓ Pattern {i} works: {result}")
        except Exception as e:
            print(f"✗ Pattern {i} fails: {e}")

if __name__ == "__main__":
    print("Testing Different Patterns")
    print("=" * 40)
    test_patterns()
