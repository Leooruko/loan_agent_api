#!/usr/bin/env python3
"""
Test the best performing manager pattern.
"""

import pandas as pd

def test_best_manager():
    """Test finding the best performing manager"""
    
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
        
        # Test the exact pattern from Example 9
        code = "pd.read_csv('processed_data.csv').groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1).index[0]"
        
        result = eval(code, {"__builtins__": __builtins__}, local_namespace)
        print(f"✓ Best performing manager: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Best Performing Manager Pattern")
    print("=" * 45)
    test_best_manager()
