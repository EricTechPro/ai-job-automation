#!/usr/bin/env python3
"""
Simple test script to validate Claude Computer Use integration
"""

import os
import asyncio
from dotenv import load_dotenv
from hyperbrowser import Hyperbrowser
from browser_agent import BrowserAgent

load_dotenv()

async def test_basic_computer_use():
    """Test basic Claude Computer Use functionality"""
    print("Testing Claude Computer Use integration...")
    
    # Check API keys
    hb_key = os.getenv('HYPERBROWSER_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not hb_key:
        print("❌ HYPERBROWSER_API_KEY not found in environment")
        return False
        
    print("✅ Hyperbrowser API key found")
    if anthropic_key:
        print("✅ Custom Anthropic API key found")
    else:
        print("ℹ️ Using Hyperbrowser's built-in Claude access")
    
    # Initialize clients
    client = Hyperbrowser(api_key=hb_key)
    agent = BrowserAgent(client, anthropic_key)
    
    # Test simple Computer Use task
    try:
        print("\n🔍 Testing Claude Computer Use with a simple task...")
        
        result = agent.execute_computer_use_task(
            task="Go to google.com and search for 'Claude Computer Use'. Tell me what you find.",
            max_steps=10
        )
        
        if result["success"]:
            print("✅ Computer Use test successful!")
            print(f"Result: {result['result'][:300]}...")
            return True
        else:
            print(f"❌ Computer Use test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

async def test_job_search():
    """Test job search functionality"""
    print("\n🔎 Testing job search functionality...")
    
    # Check API keys
    hb_key = os.getenv('HYPERBROWSER_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not hb_key:
        print("❌ Hyperbrowser API key not found")
        return False
    
    # Initialize clients
    client = Hyperbrowser(api_key=hb_key)
    agent = BrowserAgent(client, anthropic_key)
    
    # Simple AI context for testing
    test_context = """
    CANDIDATE PROFILE:
    - Software Engineer with 5 years experience
    - YouTube Creator (@EricWTech, 20K+ subscribers)
    - Skills: Python, React, TypeScript, AI/ML, Cloud Services
    - Looking for Developer Advocate or DevRel roles
    - Preferred companies: OpenAI, Google, Microsoft, Meta
    - Remote work preferred
    """
    
    try:
        result = agent.search_and_analyze_jobs(
            job_search_query="Developer Advocate",
            ai_context=test_context,
            max_steps=20
        )
        
        if result["success"]:
            print("✅ Job search test successful!")
            print(f"Search result summary: {result['result'][:400]}...")
            return True
        else:
            print(f"❌ Job search test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error during job search test: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Claude Computer Use Integration Tests")
    print("=" * 50)
    
    # Test 1: Basic Computer Use
    basic_success = await test_basic_computer_use()
    
    # Test 2: Job Search (only if basic test passes)
    if basic_success:
        job_search_success = await test_job_search()
    else:
        job_search_success = False
        print("⏭️ Skipping job search test due to basic test failure")
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    print(f"Basic Computer Use: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Job Search: {'✅ PASS' if job_search_success else '❌ FAIL'}")
    
    if basic_success and job_search_success:
        print("\n🎉 All tests passed! The integration is working correctly.")
        print("You can now run 'python main.py' to start the full job automation.")
    else:
        print("\n⚠️ Some tests failed. Check your API keys and network connection.")
    
if __name__ == "__main__":
    asyncio.run(main())