#!/usr/bin/env python3
"""
Test the exact pattern that the model should follow.
"""

import pandas as pd

def test_exact_pattern():
    """Test the exact pattern from the examples"""
    
    try:
        # Test the exact pattern from Example 7
        code = "import pandas as pd; df = pd.read_csv('processed_data.csv'); unique_clients = len(df['Client_Code'].unique()); result = f'Total Unique Clients: {unique_clients}'; result"
        
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
        
        # Execute the code
        result = eval(code, {"__builtins__": {}}, local_namespace)
        print(f"✓ Test passed: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Exact Pattern")
    print("=" * 30)
    test_exact_pattern()
