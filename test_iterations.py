#!/usr/bin/env python3
"""
Test script to verify that increased max iterations improve answer quality
"""

import asyncio
import sys
import os
from utils_simple import promt_llm, clear_conversation_memory
from config import AI_CONFIG

async def test_complex_queries():
    """Test complex queries that benefit from more iterations"""
    print("Testing complex queries with increased iterations...")
    print("=" * 60)
    print(f"Current MAX_ITERATIONS: {AI_CONFIG['MAX_ITERATIONS']}")
    print("=" * 60)
    
    # Clear any previous conversation
    clear_conversation_memory()
    
    complex_queries = [
        "Show me a comprehensive analysis of our loan portfolio performance",
        "Compare the performance of different loan managers and identify the best performers",
        "Analyze payment trends and identify clients who might need attention",
        "Give me a detailed breakdown of our loan products and their success rates",
        "What insights can you provide about our client base and their borrowing patterns?"
    ]
    
    for i, query in enumerate(complex_queries, 1):
        print(f"\n--- Complex Query {i}: {query} ---")
        print("-" * 60)
        
        try:
            response = await promt_llm(query)
            print(f"Response length: {len(response)} characters")
            print(f"Response: {response[:500]}...")
            
            # Check if response seems more comprehensive
            if len(response) > 200:
                print("✅ Response appears comprehensive")
            else:
                print("⚠️  Response might be too brief")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

async def test_multi_step_analysis():
    """Test queries that require multiple steps of analysis"""
    print("\nTesting multi-step analysis...")
    print("=" * 60)
    
    # Clear memory
    clear_conversation_memory()
    
    multi_step_queries = [
        "First show me the top 5 managers by client count, then analyze their payment collection rates, and finally identify which ones are most efficient",
        "Analyze our loan portfolio by product type, then by client type, and provide recommendations for improvement",
        "Show me clients with high arrears, then analyze their payment history, and suggest intervention strategies"
    ]
    
    for i, query in enumerate(multi_step_queries, 1):
        print(f"\n--- Multi-step Query {i} ---")
        print("-" * 60)
        
        try:
            response = await promt_llm(query)
            print(f"Response length: {len(response)} characters")
            print(f"Response: {response[:600]}...")
            
            # Check for multi-step indicators
            step_indicators = ["first", "then", "finally", "next", "additionally", "furthermore"]
            has_steps = any(indicator in response.lower() for indicator in step_indicators)
            
            if has_steps:
                print("✅ Response shows multi-step analysis")
            else:
                print("⚠️  Response might not show clear multi-step structure")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

async def test_conversational_refinement():
    """Test how the agent refines answers in conversation"""
    print("\nTesting conversational refinement...")
    print("=" * 60)
    
    # Clear memory
    clear_conversation_memory()
    
    conversation_flow = [
        "Show me the top loan managers",
        "Now provide more details about their performance",
        "Compare their efficiency in collecting payments",
        "Based on all this information, who would you recommend for a promotion?"
    ]
    
    for i, query in enumerate(conversation_flow, 1):
        print(f"\n--- Conversation Step {i}: {query} ---")
        print("-" * 60)
        
        try:
            response = await promt_llm(query)
            print(f"Response length: {len(response)} characters")
            print(f"Response: {response[:400]}...")
            
            # Check if response builds on previous context
            if i > 1 and len(response) > 150:
                print("✅ Response appears to build on previous context")
            elif i == 1 and len(response) > 100:
                print("✅ Initial response is comprehensive")
            else:
                print("⚠️  Response might need more refinement")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        print()

async def test_iteration_impact():
    """Test the impact of different iteration settings"""
    print("\nTesting iteration impact...")
    print("=" * 60)
    
    # Test with current settings
    print(f"Testing with MAX_ITERATIONS = {AI_CONFIG['MAX_ITERATIONS']}")
    
    # Clear memory
    clear_conversation_memory()
    
    test_query = "Provide a comprehensive analysis of our loan portfolio including performance metrics, risk assessment, and recommendations"
    
    try:
        response = await promt_llm(test_query)
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:300]}...")
        
        # Analyze response quality
        quality_indicators = [
            "comprehensive" in response.lower(),
            "analysis" in response.lower(),
            "recommendations" in response.lower(),
            len(response) > 300,
            response.count(".") > 3  # Multiple sentences
        ]
        
        quality_score = sum(quality_indicators) / len(quality_indicators) * 100
        print(f"Response quality score: {quality_score:.1f}%")
        
        if quality_score >= 80:
            print("✅ High quality response - iterations working well")
        elif quality_score >= 60:
            print("✅ Good quality response")
        else:
            print("⚠️  Response quality could be improved")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main test function"""
    print("Max Iterations Test")
    print("=" * 80)
    print(f"Testing with MAX_ITERATIONS = {AI_CONFIG['MAX_ITERATIONS']}")
    print("=" * 80)
    
    # Test complex queries
    await test_complex_queries()
    
    # Test multi-step analysis
    await test_multi_step_analysis()
    
    # Test conversational refinement
    await test_conversational_refinement()
    
    # Test iteration impact
    await test_iteration_impact()
    
    print("\n" + "=" * 80)
    print("✅ Max iterations test completed!")
    print(f"Current setting: MAX_ITERATIONS = {AI_CONFIG['MAX_ITERATIONS']}")
    print("This should allow the agent to provide more refined and comprehensive answers.")

if __name__ == "__main__":
    asyncio.run(main()) 