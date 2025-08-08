#!/usr/bin/env python3
"""
Test script for the improved loan agent with enhanced Python coding capabilities.
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import utils_simple
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_simple import promt_llm

async def test_agent():
    """Test the improved agent with various queries"""
    
    test_queries = [
        "What is our total loan portfolio value?",
        "Which manager has the most loans?",
        "How many clients have arrears?",
        "What is the average loan amount?",
        "Show me the top performing loan product",
        "Calculate the portfolio performance rate"
    ]
    
    print("Testing Improved Loan Agent")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 30)
        
        try:
            response = await promt_llm(query)
            print(f"Response: {response[:200]}...")  # Show first 200 chars
        except Exception as e:
            print(f"Error: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_agent())
