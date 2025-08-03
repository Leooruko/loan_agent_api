#!/usr/bin/env python3
"""
Test script to verify the column name fix for columns with spaces
"""

import asyncio
import sys
import os
from utils_simple import fetch_data

def test_column_names_with_spaces():
    """Test queries with column names that contain spaces"""
    print("Testing column names with spaces...")
    print("=" * 50)
    
    test_queries = [
        "SELECT Managed_By, SUM(`Total Paid`) FROM df GROUP BY Managed_By ORDER BY SUM(`Total Paid`) DESC LIMIT 5",
        "SELECT Client_Name, `Total Paid`, `Total Charged` FROM df WHERE `Total Paid` > 0 LIMIT 5",
        "SELECT AVG(`Total Paid`) as avg_paid FROM df WHERE Status = 'Active'",
        "SELECT COUNT(*) as total_loans, SUM(`Total Charged`) as total_charged FROM df"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)
        try:
            result = fetch_data(query)
            print(f"✅ Success: {result[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

def test_invalid_column_names():
    """Test queries with invalid column name usage"""
    print("\nTesting invalid column name usage...")
    print("=" * 50)
    
    invalid_queries = [
        "SELECT Managed_By, SUM(Total Paid) FROM df GROUP BY Managed_By",  # Missing backticks
        "SELECT Client_Name, Total Charged FROM df LIMIT 5",  # Missing backticks
        "SELECT SUM(`Total Paid`) FROM df WHERE `Total Paid` > 1000"  # Should work
    ]
    
    for i, query in enumerate(invalid_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)
        try:
            result = fetch_data(query)
            if "Error" in result:
                print(f"✅ Correctly caught error: {result}")
            else:
                print(f"⚠️  Unexpected success: {result[:100]}...")
        except Exception as e:
            print(f"✅ Caught exception: {e}")
        print()

async def test_ai_queries():
    """Test AI-generated queries that should use proper column names"""
    print("\nTesting AI queries...")
    print("=" * 50)
    
    from utils_simple import promt_llm
    
    test_questions = [
        "Show me the total payments by each loan manager",
        "What is the average amount paid by clients?",
        "Show me clients with high total charged amounts",
        "Which managers have the highest total payments?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 40)
        try:
            response = await promt_llm(question)
            print(f"Response: {response[:300]}...")
        except Exception as e:
            print(f"Error: {e}")
        print()

def main():
    """Main test function"""
    print("Column Name Fix Test")
    print("=" * 60)
    
    # Test direct SQL queries
    test_column_names_with_spaces()
    
    # Test invalid queries
    test_invalid_column_names()
    
    # Test AI queries
    asyncio.run(test_ai_queries())
    
    print("\n✅ Column name fix test completed!")

if __name__ == "__main__":
    main() 