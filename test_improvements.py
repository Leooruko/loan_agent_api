#!/usr/bin/env python3
"""
Test script for the improved loan agent system
"""

import asyncio
import sys
import os
from utils import promt_llm, fetch_data
import pandas as pd

async def test_basic_queries():
    """Test basic loan data queries"""
    print("Testing basic queries...")
    print("=" * 50)
    
    test_queries = [
        "How many active loans do we have?",
        "What is our total loan portfolio value?",
        "Which clients have the highest arrears?",
        "Show me the top 5 loan managers by number of clients",
        "What are our most popular loan products?",
        "How many clients have multiple loans?",
        "What is the average loan amount?",
        "Show me clients with arrears greater than 5000"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        try:
            response = await promt_llm(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        print()

async def test_error_handling():
    """Test error handling with invalid queries"""
    print("Testing error handling...")
    print("=" * 50)
    
    invalid_queries = [
        "",  # Empty query
        "What's the weather like?",  # Non-loan question
        "SELECT * FROM users",  # Wrong table
        "DROP TABLE df",  # Malicious query
        "A" * 1000,  # Very long query
    ]
    
    for query in invalid_queries:
        print(f"\nInvalid Query: {query[:50]}...")
        print("-" * 30)
        try:
            response = await promt_llm(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        print()

def test_data_access():
    """Test direct data access"""
    print("Testing data access...")
    print("=" * 50)
    
    try:
        # Test if data file exists
        from config import DATA_CONFIG
        if os.path.exists(DATA_CONFIG['CSV_FILE_PATH']):
            df = pd.read_csv(DATA_CONFIG['CSV_FILE_PATH'])
            print(f"Data file loaded successfully. Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print(f"Sample data:")
            print(df.head(3))
        else:
            print("Data file not found!")
    except Exception as e:
        print(f"Error loading data: {e}")

def test_fetch_data_tool():
    """Test the fetch_data tool directly"""
    print("Testing fetch_data tool...")
    print("=" * 50)
    
    test_queries = [
        "SELECT COUNT(*) FROM df WHERE Status = 'Active'",
        "SELECT SUM(Amount_Disbursed) FROM df WHERE Status = 'Active'",
        "SELECT Client_Name, Arrears FROM df WHERE Arrears > 0 ORDER BY Arrears DESC LIMIT 5",
        "SELECT Managed_By, COUNT(*) as client_count FROM df GROUP BY Managed_By ORDER BY client_count DESC LIMIT 5"
    ]
    
    for query in test_queries:
        print(f"\nSQL Query: {query}")
        print("-" * 30)
        try:
            result = fetch_data(query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
        print()

async def main():
    """Main test function"""
    print("Loan Agent System Test")
    print("=" * 60)
    
    # Test data access first
    test_data_access()
    print("\n" + "=" * 60)
    
    # Test fetch_data tool
    test_fetch_data_tool()
    print("\n" + "=" * 60)
    
    # Test basic queries
    await test_basic_queries()
    print("\n" + "=" * 60)
    
    # Test error handling
    await test_error_handling()
    print("\n" + "=" * 60)
    
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 