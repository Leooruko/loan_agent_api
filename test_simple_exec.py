#!/usr/bin/env python3
"""
Test using exec instead of eval for code execution.
"""

import pandas as pd

def test_exec():
    """Test using exec for code execution"""
    
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
        
        # Test the code using exec
        code = """
import pandas as pd
df = pd.read_csv('processed_data.csv')
unique_clients = len(df['Client_Code'].unique())
result = str(unique_clients)
"""
        
        exec(code, {"__builtins__": {}}, local_namespace)
        result = local_namespace.get('result', 'No result')
        print(f"✓ Exec test passed: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exec test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Exec Method")
    print("=" * 30)
    test_exec()
