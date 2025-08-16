import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_simple import python_calculator

def test_groupby_fix():
    # Test the problematic code that was causing the error
    problematic_code = "import pandas as pd; df = pd.read_csv('processed_data.csv'); arrears = df['Arrears'].groupby('Managed_By').sum().to_dict(); print(arrears)"
    
    print("Testing python_calculator with problematic groupby code:")
    print("=" * 60)
    print(f"Input code: {problematic_code}")
    print("-" * 60)
    
    try:
        result = python_calculator(problematic_code)
        print(f"Result: {result}")
        print("✅ SUCCESS: The code was fixed and executed successfully!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("The fix didn't work as expected.")

if __name__ == "__main__":
    test_groupby_fix()
