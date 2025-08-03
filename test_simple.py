#!/usr/bin/env python3
"""
Simple test script to verify the agent initialization fix
"""

import asyncio
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from utils_simple import promt_llm, fetch_data
        print("✅ utils_simple imports successful")
        return True
    except Exception as e:
        print(f"❌ utils_simple import failed: {e}")
        return False

def test_data_access():
    """Test if data file can be accessed"""
    print("\nTesting data access...")
    try:
        from config import DATA_CONFIG
        if os.path.exists(DATA_CONFIG['CSV_FILE_PATH']):
            print("✅ Data file found")
            return True
        else:
            print("❌ Data file not found")
            return False
    except Exception as e:
        print(f"❌ Data access test failed: {e}")
        return False

async def test_basic_query():
    """Test a simple query"""
    print("\nTesting basic query...")
    try:
        from utils_simple import promt_llm
        response = await promt_llm("How many active loans do we have?")
        print(f"✅ Query successful: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Simple Agent Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please check your installation.")
        return
    
    # Test data access
    if not test_data_access():
        print("\n❌ Data access test failed. Please check your data file.")
        return
    
    # Test basic query
    if not await test_basic_query():
        print("\n❌ Query test failed. Please check your Ollama setup.")
        return
    
    print("\n✅ All tests passed! The agent should work correctly now.")

if __name__ == "__main__":
    asyncio.run(main()) 