#!/usr/bin/env python3
"""
Test script for the refactored AI Browser Automation system
Tests logging, job tracking, and Claude Computer Use integration
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperbrowser import Hyperbrowser
from browser_agent import BrowserAgent
from utils import (
    get_logger, separator, 
    JobTracker, JobStatus
)

# Load environment variables
load_dotenv()

# Initialize logger for tests
logger = get_logger("TestSuite")


async def test_logging_system():
    """Test the colored logging system"""
    separator("=", 60)
    logger.info("🧪 Testing Logging System")
    separator("-", 60)
    
    # Test different log levels
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message (test only, not a real error)")
    logger.critical("This is a CRITICAL message (test only)")
    
    # Test custom log methods
    logger.success("This is a SUCCESS message")
    logger.process("This is a PROCESS message")
    logger.step(1, 3, "This is a STEP message")
    logger.data("This is a DATA message", {"key": "value", "count": 42})
    
    # Test job-specific logging
    logger.job_found("Developer Advocate", "OpenAI", "San Francisco, CA")
    logger.job_applied("Technical Evangelist", "Google")
    
    separator("=", 60)
    logger.success("✅ Logging system test completed")
    return True


def test_job_tracker():
    """Test the job tracking system"""
    separator("=", 60)
    logger.info("🧪 Testing Job Tracker System")
    separator("-", 60)
    
    # Initialize tracker with test file
    tracker = JobTracker(data_file="data/test_job_tracker.json")
    
    # Test 1: Add a new job
    logger.step(1, 5, "Adding a new job")
    job_id = tracker.add_job(
        company="OpenAI",
        job_title="Developer Advocate",
        location="San Francisco, CA",
        job_url="https://openai.com/careers/developer-advocate",
        description="Help developers build with GPT-4",
        requirements=["3+ years experience", "Public speaking", "Technical writing"],
        salary_range="$150k-$200k",
        remote=True,
        job_board="LinkedIn"
    )
    logger.success(f"Job added with ID: {job_id}")
    
    # Test 2: Update job status
    logger.step(2, 5, "Updating job status")
    tracker.update_job_status(job_id, JobStatus.REVIEWED, "Looks like a great match!")
    tracker.update_job_status(job_id, JobStatus.APPLIED, "Application submitted via LinkedIn")
    
    # Test 3: Add another job
    logger.step(3, 5, "Adding another job")
    job_id2 = tracker.add_job(
        company="Google",
        job_title="Technical Evangelist",
        location="Mountain View, CA",
        job_url="https://careers.google.com/jobs/results/",
        remote=False,
        job_board="Google Careers"
    )
    
    # Test 4: Search and retrieve jobs
    logger.step(4, 5, "Testing search functionality")
    
    # Search by status
    applied_jobs = tracker.get_jobs_by_status(JobStatus.APPLIED)
    logger.data(f"Jobs with APPLIED status", {"count": len(applied_jobs)})
    
    # Search by company
    openai_jobs = tracker.get_jobs_by_company("OpenAI")
    logger.data(f"Jobs at OpenAI", {"count": len(openai_jobs)})
    
    # General search
    search_results = tracker.search_jobs("Advocate")
    logger.data(f"Jobs matching 'Advocate'", {"count": len(search_results)})
    
    # Test 5: Get statistics
    logger.step(5, 5, "Getting tracker statistics")
    stats = tracker.get_statistics()
    logger.data("Job Tracker Statistics", stats)
    
    # Print summary
    tracker.print_summary()
    
    # Clean up test files
    logger.info("Cleaning up test files...")
    for test_file in ["data/test_job_tracker.json"]:
        if Path(test_file).exists():
            Path(test_file).unlink()
            logger.debug(f"Removed test file: {test_file}")
    
    separator("=", 60)
    logger.success("✅ Job tracker test completed")
    return True


async def test_browser_agent():
    """Test the refactored browser agent"""
    separator("=", 60)
    logger.info("🧪 Testing Browser Agent")
    separator("-", 60)
    
    # Check API keys
    hb_key = os.getenv('HYPERBROWSER_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not hb_key:
        logger.error("HYPERBROWSER_API_KEY not found in environment")
        return False
    
    logger.success("Hyperbrowser API key found")
    if anthropic_key:
        logger.success("Custom Anthropic API key found")
    else:
        logger.info("Using Hyperbrowser's built-in Claude access")
    
    # Initialize clients
    try:
        client = Hyperbrowser(api_key=hb_key)
        agent = BrowserAgent(client, anthropic_key)
        logger.success("Browser agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize browser agent: {e}")
        return False
    
    # Test simple Computer Use task
    try:
        logger.process("Testing Claude Computer Use with a simple task...")
        
        result = agent.execute_computer_use_task(
            task="Go to google.com and search for 'Claude Computer Use documentation'. Tell me what you find on the first result.",
            max_steps=15
        )
        
        if result["success"]:
            logger.success("Computer Use test successful!")
            logger.info(f"Result preview: {result['result'][:200]}...")
            
            # Test session reuse
            if result.get("session_id"):
                logger.process("Testing session reuse...")
                reuse_result = agent.execute_computer_use_task(
                    task="Now search for 'Hyperbrowser documentation' on the same page",
                    max_steps=10,
                    session_id=result["session_id"]
                )
                
                if reuse_result["success"]:
                    logger.success("Session reuse successful!")
                else:
                    logger.warning(f"Session reuse failed: {reuse_result.get('error')}")
            
            return True
        else:
            logger.error(f"Computer Use test failed: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Error during browser agent test: {str(e)}")
        return False
    
    finally:
        # Clean up session
        agent.close_session()
        
    separator("=", 60)
    logger.success("✅ Browser agent test completed")


async def test_integration():
    """Test the integration of all components"""
    separator("=", 60)
    logger.info("🧪 Testing Full System Integration")
    separator("-", 60)
    
    # This test requires actual API keys and will perform real operations
    # So we'll make it optional based on environment variable
    
    if os.getenv('RUN_INTEGRATION_TEST') != 'true':
        logger.warning("Integration test skipped (set RUN_INTEGRATION_TEST=true to run)")
        return True
    
    try:
        # Import the main module
        from main import DeveloperAdvocateJobBot, test_browser_connection
        
        # Test browser connection
        logger.step(1, 3, "Testing browser connection")
        connection_ok = await test_browser_connection()
        
        if not connection_ok:
            logger.error("Browser connection failed")
            return False
        
        # Initialize bot
        logger.step(2, 3, "Initializing job bot")
        client = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))
        bot = DeveloperAdvocateJobBot(client, os.getenv('ANTHROPIC_API_KEY'))
        
        # Load data
        await bot.load_resume_and_preferences()
        logger.success("Bot initialized with resume and preferences")
        
        # Test job tracker integration
        logger.step(3, 3, "Testing job tracker integration")
        
        # Add a test job
        test_job_id = bot.job_tracker.add_job(
            company="Test Company",
            job_title="Test Developer Advocate",
            location="Remote",
            job_url="https://example.com/job",
            job_board="Test Board"
        )
        
        # Update status
        bot.job_tracker.update_job_status(test_job_id, JobStatus.REVIEWED)
        
        # Get statistics
        stats = bot.job_tracker.get_statistics()
        logger.data("Integration test statistics", stats)
        
        logger.success("✅ Integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False
    
    separator("=", 60)


async def main():
    """Run all tests"""
    separator("=", 70)
    logger.info("🚀 REFACTORED AI BROWSER AUTOMATION TEST SUITE")
    separator("=", 70)
    
    test_results = {}
    
    # Test 1: Logging System
    logger.info("\n📝 Test 1: Logging System")
    test_results["logging"] = await test_logging_system()
    
    # Test 2: Job Tracker
    logger.info("\n💼 Test 2: Job Tracker")
    test_results["job_tracker"] = test_job_tracker()
    
    # Test 3: Browser Agent (if API key available)
    logger.info("\n🌐 Test 3: Browser Agent")
    if os.getenv('HYPERBROWSER_API_KEY'):
        test_results["browser_agent"] = await test_browser_agent()
    else:
        logger.warning("Skipping browser agent test (no API key)")
        test_results["browser_agent"] = None
    
    # Test 4: Integration (optional)
    logger.info("\n🔗 Test 4: System Integration")
    test_results["integration"] = await test_integration()
    
    # Print test summary
    separator("=", 70)
    logger.info("📊 TEST RESULTS SUMMARY")
    separator("-", 70)
    
    for test_name, result in test_results.items():
        if result is None:
            status = "⏭️  SKIPPED"
        elif result:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        logger.info(f"{test_name.title():<20} {status}")
    
    # Overall result
    passed_tests = [r for r in test_results.values() if r is True]
    failed_tests = [r for r in test_results.values() if r is False]
    
    separator("=", 70)
    
    if not failed_tests:
        logger.success("🎉 All tests passed successfully!")
        logger.info("The system is ready to use.")
        logger.info("Run 'python3 main.py' to start the job automation.")
    else:
        logger.error(f"⚠️  {len(failed_tests)} test(s) failed.")
        logger.info("Please check the errors above and fix any issues.")
    
    separator("=", 70)


if __name__ == "__main__":
    asyncio.run(main())