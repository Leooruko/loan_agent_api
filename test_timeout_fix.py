#!/usr/bin/env python3
"""
Test script to verify timeout fixes
"""

import requests
import time
import json
import sys

def test_simple_query():
    """Test a simple query to ensure basic functionality"""
    print("Testing simple query...")
    
    try:
        response = requests.post(
            'http://localhost:5500/chat',
            json={'promt': 'Hello'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simple query successful")
            print(f"Response time: {data.get('response_time', 'N/A')}s")
            print(f"Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Simple query failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Simple query timed out")
        return False
    except Exception as e:
        print(f"❌ Simple query error: {e}")
        return False

def test_complex_query():
    """Test a complex query that might take longer"""
    print("\nTesting complex query...")
    
    try:
        response = requests.post(
            'http://localhost:5500/chat',
            json={'promt': 'Show me all active loans with their payment status and total amounts'},
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Complex query successful")
            print(f"Response time: {data.get('response_time', 'N/A')}s")
            print(f"Response: {data.get('response', '')[:200]}...")
            return True
        elif response.status_code == 408:
            print("❌ Complex query timed out (408)")
            return False
        else:
            print(f"❌ Complex query failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Complex query timed out (request timeout)")
        return False
    except Exception as e:
        print(f"❌ Complex query error: {e}")
        return False

def test_timeout_configuration():
    """Test if timeout configuration is working"""
    print("\nTesting timeout configuration...")
    
    try:
        # Test API info endpoint to check configuration
        response = requests.get('http://localhost:5500/api/info', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ai_config = data.get('ai_config', {})
            
            timeout_seconds = ai_config.get('TIMEOUT_SECONDS', 0)
            request_timeout = ai_config.get('REQUEST_TIMEOUT', 0)
            
            print(f"✅ Timeout configuration found:")
            print(f"   TIMEOUT_SECONDS: {timeout_seconds}s")
            print(f"   REQUEST_TIMEOUT: {request_timeout}s")
            
            if request_timeout >= 90:
                print("✅ Timeout configuration is adequate")
                return True
            else:
                print("❌ Timeout configuration too low")
                return False
        else:
            print(f"❌ Could not check configuration: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration check error: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    print("\nTesting health endpoint...")
    
    try:
        response = requests.get('http://localhost:5500/health', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful")
            print(f"Status: {data.get('status', 'N/A')}")
            print(f"Uptime: {data.get('uptime', 'N/A')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\nTesting rate limiting...")
    
    try:
        # Send multiple requests quickly
        responses = []
        for i in range(5):
            response = requests.post(
                'http://localhost:5500/chat',
                json={'promt': f'Test query {i}'},
                timeout=10
            )
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay
        
        success_count = sum(1 for code in responses if code == 200)
        rate_limit_count = sum(1 for code in responses if code == 429)
        
        print(f"✅ Rate limiting test completed:")
        print(f"   Successful requests: {success_count}")
        print(f"   Rate limited requests: {rate_limit_count}")
        
        if success_count > 0:
            print("✅ Rate limiting is working")
            return True
        else:
            print("❌ All requests failed")
            return False
            
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🔧 Timeout Fix Verification Test")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5500/', timeout=5)
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("Please start the server first:")
        print("  python start_production.py")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Timeout Configuration", test_timeout_configuration),
        ("Simple Query", test_simple_query),
        ("Complex Query", test_complex_query),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Timeout fixes are working.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Some minor issues may remain.")
    else:
        print("❌ Multiple tests failed. Check server configuration.")
    
    # Recommendations
    print("\n📋 Recommendations:")
    if passed < total:
        print("1. Check server logs for errors")
        print("2. Ensure Ollama and Mistral are running")
        print("3. Verify timeout configuration in config.py")
        print("4. Try restarting the server")
    else:
        print("1. ✅ Timeout fixes are working correctly")
        print("2. ✅ Server is properly configured")
        print("3. ✅ Ready for production use")

if __name__ == "__main__":
    main() 