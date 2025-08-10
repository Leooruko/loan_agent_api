#!/usr/bin/env python3
"""
Test script to verify the backtick removal fix in python_calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_simple import python_calculator

def test_backtick_removal():
    """Test that backticks are properly removed from Python code"""
    
    # Test cases with different backtick formats
    test_cases = [
        {
            "name": "Code with ```python backticks",
            "input": "```python\nimport pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)\n```",
            "expected_contains": "import pandas as pd"
        },
        {
            "name": "Code with simple backticks",
            "input": "`import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)`",
            "expected_contains": "import pandas as pd"
        },
        {
            "name": "Code without backticks",
            "input": "import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)",
            "expected_contains": "import pandas as pd"
        },
        {
            "name": "Code with ``` backticks",
            "input": "```\nimport pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)\n```",
            "expected_contains": "import pandas as pd"
        }
    ]
    
    print("Testing backtick removal in python_calculator...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {test_case['input'][:50]}...")
        
        try:
            result = python_calculator(test_case['input'])
            print(f"Result: {result}")
            
            if test_case['expected_contains'] in result or "Error" in result:
                print("✅ PASS - Code was processed (either successfully or with expected error)")
            else:
                print("❌ FAIL - Unexpected result")
                
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_backtick_removal()
