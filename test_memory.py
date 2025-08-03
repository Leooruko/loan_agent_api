#!/usr/bin/env python3
"""
Test script to verify conversation memory functionality
"""

import asyncio
import sys
import os
from utils_simple import promt_llm, get_conversation_memory, clear_conversation_memory

async def test_conversation_memory():
    """Test conversation memory functionality"""
    print("Testing conversation memory...")
    print("=" * 50)
    
    # Test conversation flow
    conversation_flow = [
        "How many active loans do we have?",
        "What about inactive loans?",
        "Can you show me the top 3 managers by number of clients?",
        "Now show me their total payments",
        "Compare this with the previous results"
    ]
    
    for i, question in enumerate(conversation_flow, 1):
        print(f"\n--- Question {i}: {question} ---")
        print("-" * 40)
        
        try:
            response = await promt_llm(question)
            print(f"Response: {response[:300]}...")
            
            # Check memory
            memory = get_conversation_memory()
            print(f"Memory messages: {len(memory)}")
            
        except Exception as e:
            print(f"Error: {e}")
        print()

async def test_memory_persistence():
    """Test that memory persists across multiple queries"""
    print("\nTesting memory persistence...")
    print("=" * 50)
    
    # First query
    print("\n1. Initial query about active loans...")
    response1 = await promt_llm("How many active loans do we have?")
    print(f"Response: {response1[:200]}...")
    
    # Second query that references the first
    print("\n2. Follow-up query...")
    response2 = await promt_llm("What percentage of total loans are active?")
    print(f"Response: {response2[:200]}...")
    
    # Third query that should build on previous context
    print("\n3. Contextual query...")
    response3 = await promt_llm("Show me the breakdown by loan product type")
    print(f"Response: {response3[:200]}...")
    
    # Check memory
    memory = get_conversation_memory()
    print(f"\nTotal conversation messages in memory: {len(memory)}")

async def test_memory_clear():
    """Test memory clearing functionality"""
    print("\nTesting memory clearing...")
    print("=" * 50)
    
    # Add some conversation
    await promt_llm("How many clients do we have?")
    await promt_llm("What's the average loan amount?")
    
    # Check memory before clearing
    memory_before = get_conversation_memory()
    print(f"Memory before clearing: {len(memory_before)} messages")
    
    # Clear memory
    clear_result = clear_conversation_memory()
    print(f"Clear result: {clear_result}")
    
    # Check memory after clearing
    memory_after = get_conversation_memory()
    print(f"Memory after clearing: {len(memory_after)} messages")
    
    # Test that AI doesn't remember previous conversation
    print("\nTesting if AI remembers previous conversation...")
    response = await promt_llm("What was the average loan amount we discussed?")
    print(f"Response: {response[:200]}...")

async def test_contextual_queries():
    """Test queries that should use previous context"""
    print("\nTesting contextual queries...")
    print("=" * 50)
    
    # Build context
    await promt_llm("Show me the top 5 loan managers by number of clients")
    
    # Follow-up queries that should reference previous results
    contextual_queries = [
        "What's their average loan amount?",
        "Show me the same managers but by total payments",
        "Which of these managers has the best performance?",
        "Compare the top manager with the others"
    ]
    
    for i, query in enumerate(contextual_queries, 1):
        print(f"\nContextual query {i}: {query}")
        print("-" * 40)
        try:
            response = await promt_llm(query)
            print(f"Response: {response[:300]}...")
        except Exception as e:
            print(f"Error: {e}")
        print()

async def main():
    """Main test function"""
    print("Conversation Memory Test")
    print("=" * 60)
    
    # Test basic conversation memory
    await test_conversation_memory()
    
    # Test memory persistence
    await test_memory_persistence()
    
    # Test memory clearing
    await test_memory_clear()
    
    # Test contextual queries
    await test_contextual_queries()
    
    print("\n✅ Conversation memory test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 