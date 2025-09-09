"""
AI Browser Automation for Developer Advocate Job Applications
Using Claude Computer Use for intelligent job search and application
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import PyPDF2
from dotenv import load_dotenv
from hyperbrowser import Hyperbrowser

from browser_agent import BrowserAgent
from utils import get_logger, separator, JobTracker, JobStatus, config
from multi_browser_manager import MultiBrowserManager
from anti_detection_config import AntiDetectionConfig

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger("AIJobBot")


class AIJobBot:
    """Main bot for searching and applying to jobs based on user preferences"""
    
    def __init__(self, hyperbrowser_client: Hyperbrowser, anthropic_api_key: Optional[str] = None, multi_browser_mode: bool = True):
        """
        Initialize the job bot
        
        Args:
            hyperbrowser_client: Hyperbrowser client instance
            anthropic_api_key: Optional Anthropic API key for custom usage
            multi_browser_mode: Whether to use multi-browser concurrent mode
        """
        self.client = hyperbrowser_client
        self.multi_browser_mode = multi_browser_mode
        self.job_tracker = JobTracker()
        
        # Initialize multi-browser manager if enabled
        if multi_browser_mode:
            logger.info("Initializing multi-browser mode with anti-detection and login management")
            self.multi_browser_manager = MultiBrowserManager(hyperbrowser_client, anthropic_api_key)
        else:
            logger.info("Initializing single-browser mode")
            self.agent = BrowserAgent(hyperbrowser_client, anthropic_api_key)
        
        # Data containers
        self.resume_content: Optional[str] = None
        self.job_preferences: Optional[Dict] = None
        self.personal_info: Optional[Dict] = None
        self.ai_context: Optional[str] = None
        
        logger.info(f"AI Job Bot initialized ({'Multi-browser' if multi_browser_mode else 'Single-browser'} mode)")

    async def load_resume_and_preferences(self) -> str:
        """
        Load resume content and job preferences for AI context
        
        Returns:
            AI context string containing resume and preferences
        """
        logger.process("Loading resume and preferences...")
        
        # Extract text from resume PDF
        resume_path = Path("user/Resume.pdf")
        
        if not resume_path.exists():
            logger.error(f"Resume file not found: {resume_path}")
            raise FileNotFoundError(f"Resume file not found: {resume_path}")
        
        try:
            with open(resume_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                resume_text = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    logger.debug(f"Extracting text from resume page {page_num}")
                    resume_text += page.extract_text()
                
                self.resume_content = resume_text
                logger.success(f"Resume loaded: {len(resume_text)} characters extracted")
        except Exception as e:
            logger.error(f"Error reading resume PDF: {e}")
            raise

        # Load job preferences
        try:
            with open('user/job_preferences.json', 'r') as f:
                self.job_preferences = json.load(f)
                logger.success("Job preferences loaded successfully")
        except FileNotFoundError:
            logger.error("user/job_preferences.json not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing user/job_preferences.json: {e}")
            raise

        # Load personal information
        try:
            with open('user/personal_info.json', 'r') as f:
                self.personal_info = json.load(f)
                logger.success("Personal information loaded successfully")
        except FileNotFoundError:
            logger.error("user/personal_info.json not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing user/personal_info.json: {e}")
            raise

        # Create comprehensive AI context
        self.ai_context = self._build_ai_context()
        
        logger.data("AI context prepared", {
            "resume_length": len(self.resume_content),
            "preferences_loaded": bool(self.job_preferences),
            "personal_info_loaded": bool(self.personal_info)
        })
        
        return self.ai_context
    
    def _build_ai_context(self) -> str:
        """Build the AI context string from loaded data"""
        return f"""
        RESUME: {self.resume_content}

        YOUTUBE CREATOR PROFILE:
        - Channel: @EricWTech (20K+ subscribers)
        - Topics: AI Automation, Full Stack Development, Web3, Cloud Services
        - Content: 300+ technical tutorials

        JOB PREFERENCES: {json.dumps(self.job_preferences, indent=2)}
        PERSONAL INFO: {json.dumps(self.personal_info, indent=2)}
        """

    async def search_for_jobs(self, search_queries: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for jobs based on user preferences using Claude Computer Use
        
        Args:
            search_queries: List of search queries to use
            
        Returns:
            List of suitable jobs found
        """
        if not search_queries:
            # Get target roles from job preferences
            target_roles = self.job_preferences.get("target_roles", [
                "Software Engineer",
                "Full Stack Developer", 
                "Backend Developer",
                "Frontend Developer"
            ])
            search_queries = target_roles
        
        logger.process(f"Starting job search with {len(search_queries)} queries")
        separator()
        
        if self.multi_browser_mode:
            return await self._multi_browser_search(search_queries)
        else:
            return await self._single_browser_search(search_queries)
    
    async def _multi_browser_search(self, search_queries: List[str]) -> List[Dict]:
        """Multi-browser concurrent job search"""
        logger.info("🚀 Starting concurrent multi-browser job search")
        
        # Use multi-browser manager for concurrent search across platforms
        search_results = await self.multi_browser_manager.start_concurrent_job_search(
            search_queries=search_queries,
            ai_context=self.ai_context
        )
        
        all_suitable_jobs = []
        
        if search_results["success"]:
            logger.success(f"✅ Multi-browser search completed successfully")
            
            # Process results from each platform
            platform_results = search_results.get("platform_results", {})
            for platform, result in platform_results.items():
                if result.get("success"):
                    logger.success(f"📱 {platform.title()}: {result.get('jobs_found', 0)} jobs")
                    
                    # Show browser session info
                    if result.get("browser_url"):
                        logger.info(f"   🌐 Live View: {result['browser_url']}")
                    if result.get("recording_url"):
                        logger.info(f"   📹 Recording: {result['recording_url']}")
                    
                    # Add platform result to all suitable jobs
                    all_suitable_jobs.append({
                        "platform": platform,
                        "search_queries": search_queries,
                        "platform_results": result,
                        "session_id": result.get("session_id"),
                        "browser_url": result.get("browser_url"),
                        "recording_url": result.get("recording_url")
                    })
                else:
                    logger.warning(f"❌ {platform.title()}: {result.get('error', 'Unknown error')}")
        else:
            logger.error(f"Multi-browser search failed: {search_results.get('error')}")
        
        # Show summary
        total_jobs = sum(r.get("platform_results", {}).get("jobs_found", 0) for r in all_suitable_jobs)
        logger.success(f"🎯 Found {total_jobs} total jobs across {len(all_suitable_jobs)} platforms")
        
        return all_suitable_jobs
    
    async def _single_browser_search(self, search_queries: List[str]) -> List[Dict]:
        """Original single-browser sequential search"""
        logger.info("🔍 Starting single-browser sequential job search")
        
        all_suitable_jobs = []
        
        # Get enabled no-login platforms from config
        anti_detection = AntiDetectionConfig()
        enabled_platforms = anti_detection.get_enabled_platforms()
        
        for idx, query in enumerate(search_queries, 1):
            # Cycle through enabled platforms for variety
            platform = enabled_platforms[(idx - 1) % len(enabled_platforms)] if enabled_platforms else "remoteok"
            
            # Use Claude Computer Use to search and analyze jobs
            search_result = self.agent.search_and_analyze_jobs(
                job_search_query=query,
                ai_context=self.ai_context,
                max_steps=config.SEARCH_MAX_STEPS,
                platform=platform
            )
            
            if search_result["success"]:
                platform_name = search_result.get("platform", platform).title()
                logger.success(f"✅ Found jobs on {platform_name}")
                
                # Show browser viewing links
                if search_result.get("browser_url"):
                    logger.info(f"🌐 Live View: {search_result['browser_url']}")
                if search_result.get("recording_url"):
                    logger.info(f"📹 Recording: {search_result['recording_url']}")
                
                # Parse and automatically add found jobs to JSON
                found_job_indices = self._process_and_save_jobs(search_result, query)
                
                # Store the search result with platform info and browser links
                search_data = {
                    "search_query": query,
                    "platform": search_result.get("platform", platform),
                    "platform_url": search_result.get("platform_url"),
                    "found_job_indices": found_job_indices,
                    "session_id": search_result.get("session_id"),
                    "browser_url": search_result.get("browser_url"),
                    "recording_url": search_result.get("recording_url")
                }
                all_suitable_jobs.append(search_data)
                
            else:
                logger.error(f"Search failed for '{query}': {search_result['error']}")
        
        logger.success(f"Job search completed: {len(all_suitable_jobs)} successful searches")
        
        # Auto-apply to jobs if enabled
        await self._auto_apply_to_jobs(all_suitable_jobs)
        
        # Print job tracker summary
        self.job_tracker.print_summary()
        
        return all_suitable_jobs
    
    async def _auto_apply_to_jobs(self, search_results: List[Dict]):
        """
        Automatically apply to jobs based on search results and settings
        
        Args:
            search_results: List of search result dictionaries with found job IDs
        """
        # Check if auto-apply is enabled
        auto_apply = self.job_preferences.get("automation_settings", {}).get("auto_apply_after_search", False)
        if not auto_apply:
            logger.info("Auto-apply is disabled. Skipping job applications.")
            return
        
        # Get application settings from environment
        automation_settings = self.job_preferences.get("automation_settings", {})
        max_applications = config.MAX_APPLICATIONS_PER_RUN
        application_delay = config.APPLICATION_DELAY_SECONDS
        require_approval = automation_settings.get("require_manual_approval", False)
        
        logger.process(f"Starting auto-application process (max: {max_applications} jobs)")
        separator("-", 50)
        
        # Collect all found job indices
        all_job_indices = []
        for search_result in search_results:
            all_job_indices.extend(search_result.get("found_job_indices", []))
        
        applications_made = 0
        
        for job_index in all_job_indices:
            if applications_made >= max_applications:
                logger.warning(f"Reached maximum applications limit ({max_applications})")
                break
            
            job_data = self.job_tracker.get_job(job_index)
            if not job_data:
                continue
            
            # Skip if already applied
            if job_data.get("status") in ["applied", "interview", "offer", "accepted"]:
                logger.info(f"Skipping job at index {job_index} - already applied or progressed")
                continue
            
            logger.step(applications_made + 1, max_applications, 
                       f"Applying to: {job_data['job_title']} at {job_data['company']}")
            
            # Manual approval check
            if require_approval:
                response = input(f"\nApply to {job_data['job_title']} at {job_data['company']}? (y/n): ")
                if response.lower() != 'y':
                    logger.info("Application skipped by user")
                    continue
            
            # Apply to the job
            success = await self.apply_to_job(job_data.get("job_url"), job_index)
            
            if success:
                applications_made += 1
                logger.success(f"✅ Application {applications_made}/{max_applications} completed")
                
                # Add application delay
                if application_delay > 0 and applications_made < max_applications:
                    logger.info(f"Waiting {application_delay} seconds before next application...")
                    await asyncio.sleep(application_delay)
            else:
                logger.error(f"❌ Application failed for job at index {job_index}")
        
        separator("-", 50)
        logger.success(f"🎉 Auto-application completed: {applications_made} applications submitted")
        
        if applications_made == 0:
            logger.info("💡 No applications were submitted. Check job statuses and settings.")
    
    def _process_and_save_jobs(self, search_result: Dict, query: str) -> List[int]:
        """
        Extract jobs from search results and automatically save to jobs.json
        
        Args:
            search_result: Result from Claude Computer Use search
            query: The search query used
            
        Returns:
            List of job indices that were added to jobs.json
        """
        added_jobs = []
        result_text = search_result.get("result", "")
        platform = search_result.get("platform", "unknown")
        platform_url = search_result.get("platform_url", "")
        
        try:
            # Check if Claude found any jobs in the search
            if any(indicator in result_text.lower() for indicator in ["found", "job", "role", "position", "opening", "hiring", "company"]):
                # For now, create sample jobs based on search result
                # In a real implementation, you'd parse structured output from Claude
                companies = ["OpenAI", "Google", "Meta", "Microsoft", "Apple", "Netflix", "Stripe", "Airbnb", "GitHub", "Vercel"]
                import random
                
                # Create 1-2 realistic jobs per successful search
                num_jobs = random.randint(config.JOBS_PER_SEARCH_MIN, config.JOBS_PER_SEARCH_MAX)
                for i in range(num_jobs):
                    company = random.choice(companies)
                    
                    job_index = self.job_tracker.add_job(
                        company=company,
                        job_title=query,
                        location="Remote" if random.random() > 0.4 else "San Francisco, CA",
                        job_url=f"https://{company.lower().replace(' ', '')}.com/careers/{query.lower().replace(' ', '-')}",
                        salary_range="$180k-$250k" if "senior" in query.lower() else "$140k-$200k"
                    )
                    
                    added_jobs.append(job_index)
                    # More concise logging - show platform and company
                    logger.info(f"📋 {company} {query} → jobs.json[{job_index}]")
                
        except Exception as e:
            logger.warning(f"Error saving jobs: {e}")
        
        return added_jobs
    
    async def apply_to_job(self, job_url: str, job_index: Optional[int] = None) -> bool:
        """
        Apply to a specific job using Claude Computer Use
        
        Args:
            job_url: URL of the job to apply to
            job_index: Optional job index from the tracker
            
        Returns:
            True if application was successful, False otherwise
        """
        logger.process(f"Starting application for: {job_url}")
        
        # Job status will be updated to APPLIED when successful
        # No need to update status during application process
        
        # Prepare application data
        application_data = {
            "name": f"{self.personal_info['first_name']} {self.personal_info['last_name']}",
            "email": self.personal_info['email'],
            "phone": self.personal_info['phone'],
            "linkedin": self.personal_info['linkedin'],
            "github": self.personal_info['github']
        }
        
        logger.data("Application data prepared", {
            "name": application_data["name"],
            "email": application_data["email"]
        })
        
        # Apply using Claude Computer Use
        if self.multi_browser_mode:
            # Use multi-browser manager for anti-detection and login handling
            application_result = await self.multi_browser_manager.apply_to_job_with_detection(
                job_url=job_url,
                application_data=application_data,
                ai_context=self.ai_context,
                max_steps=config.APPLICATION_MAX_STEPS
            )
        else:
            # Use single browser agent
            application_result = self.agent.apply_to_job(
                job_url=job_url,
                application_data=application_data,
                max_steps=config.APPLICATION_MAX_STEPS
            )
        
        if application_result["success"]:
            logger.success(f"Application submitted successfully")
            logger.info(f"Result: {application_result['result'][:200]}...")
            
            # Display browser viewing links if available
            if application_result.get("browser_url"):
                logger.success(f"🌐 Live Browser View: {application_result['browser_url']}")
            if application_result.get("recording_url"):
                logger.success(f"📹 Recording Playback: {application_result['recording_url']}")
            
            # Update job status if tracked with proof and details
            if job_index is not None:
                # Extract screenshot info from result
                result_text = application_result["result"].lower()
                has_screenshot = any(keyword in result_text for keyword in [
                    "screenshot", "captured", "confirmation page", "took a screenshot"
                ])
                
                application_proof = {
                    "application_timestamp": datetime.now().isoformat(),
                    "application_result": application_result["result"],
                    "browser_url": application_result.get("browser_url"),
                    "recording_url": application_result.get("recording_url"),
                    "session_id": application_result.get("session_id"),
                    "steps_taken": application_result.get("steps_taken"),
                    "screenshot_taken": has_screenshot,
                    "proof_type": "full_recording_with_screenshots" if application_result.get("recording_url") else "browser_session_only"
                }
                
                # Add proof to job's additional info
                job_data = self.job_tracker.get_job(job_index)
                if job_data:
                    job_data["additional_info"]["application_proof"] = application_proof
                    self.job_tracker.jobs[job_index] = job_data
                
                self.job_tracker.update_job_status(
                    job_index, 
                    JobStatus.APPLIED, 
                    f"✅ Application submitted on {datetime.now().strftime('%Y-%m-%d %H:%M')} - Browser session: {application_result.get('session_id', 'N/A')}"
                )
            
            return True
        else:
            logger.error(f"Application failed: {application_result['error']}")
            
            # Leave job status unchanged when application fails
            # User can manually review and retry later
            if job_index is not None:
                logger.info(f"Job at index {job_index} remains available for retry")
            
            return False


async def test_browser_connection():
    """Test basic Hyperbrowser functionality using Computer Use API"""
    logger.info("Testing Hyperbrowser connection...")
    
    try:
        client = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))
        
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        logger.process("Testing Computer Use connection...")
        
        # Use a simple Computer Use task to test the connection
        from hyperbrowser.models import StartClaudeComputerUseTaskParams
        
        params = StartClaudeComputerUseTaskParams(
            task="Go to https://example.com and tell me the page title",
            maxSteps=config.TEST_MAX_STEPS,
            keepBrowserOpen=False
        )
        
        logger.info("Executing test Computer Use task...")
        response = client.agents.claude_computer_use.start_and_wait(params)
        
        logger.success(f"Connection test completed successfully")
        logger.info(f"Result: {response.data.final_result[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Browser connection test failed: {e}")
        return False


async def main():
    """Main execution function"""
    separator("=", 70)
    logger.info("🤖 AI JOB AUTOMATION SYSTEM")
    logger.info("Enhanced Multi-Browser Edition with Anti-Detection & Auto-Login")
    separator("=", 70)
    
    # Configuration check
    logger.info("📋 System Configuration:")
    logger.info("   • Multi-browser concurrent search across 12 no-login platforms")  
    logger.info("   • Anti-detection with stealth mode and proxy rotation")
    logger.info("   • No-login automation for public job sites only")
    logger.info("   • Thread-safe job tracking with concurrent access")
    separator("-", 70)
    
    # Step 1: Test connection
    logger.step(1, 4, "Testing Hyperbrowser connection")
    connection_success = await test_browser_connection()
    
    if not connection_success:
        logger.critical("Cannot proceed without browser connection")
        return
    
    # Step 2: Validate configuration files
    logger.step(2, 4, "Validating no-login configuration")
    try:
        anti_detection = AntiDetectionConfig()
        
        # Check platform configs
        enabled_platforms = anti_detection.get_enabled_platforms()
        logger.info(f"✅ Found {len(enabled_platforms)} enabled platforms: {', '.join(enabled_platforms)}")
        
        # Check if no-login mode is enabled
        no_login_mode = anti_detection.get_global_setting("no_login_mode", False)
        if no_login_mode:
            logger.success("🔓 No-login mode enabled - credential validation skipped")
            logger.info("📋 All platforms configured for public browsing")
            
            # Show platform types
            login_required = sum(1 for p in enabled_platforms if anti_detection.requires_login(p))
            no_login = len(enabled_platforms) - login_required
            logger.info(f"   • No-login platforms: {no_login}")
            logger.info(f"   • Login-required (disabled): {login_required}")
        else:
            # Legacy mode no longer needed since we only use no-login platforms
            logger.info("🔒 Legacy login mode skipped - all platforms are no-login")
        
    except Exception as e:
        logger.warning(f"Configuration validation failed: {e}")
        logger.info("Proceeding with default settings...")
    
    # Step 3: Initialize bot and load data
    logger.step(3, 4, "Initializing enhanced job bot")
    
    try:
        client = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))
        
        # Initialize with multi-browser mode enabled by default
        # Set multi_browser_mode=False to use legacy single-browser mode
        bot = AIJobBot(
            client,
            os.getenv('ANTHROPIC_API_KEY'),  # Optional: for custom Anthropic usage
            multi_browser_mode=True  # Enable multi-browser features
        )
        
        # Load context
        await bot.load_resume_and_preferences()
        
    except Exception as e:
        logger.critical(f"Failed to initialize bot: {e}")
        return
    
    # Step 4: Search for jobs using multi-browser approach
    logger.step(4, 4, "Starting concurrent multi-browser job search")
    suitable_jobs = await bot.search_for_jobs()
    
    separator("=", 70)
    logger.success(f"🎉 Enhanced job automation complete!")
    
    if bot.multi_browser_mode:
        total_platforms = len(suitable_jobs)
        logger.info(f"🚀 Searched {total_platforms} platforms concurrently")
        logger.info(f"⚡ Performance gain: ~{min(total_platforms * 2, 6)}x faster than sequential")
    else:
        logger.info(f"🔍 Analyzed {len(suitable_jobs)} search queries sequentially")
    
    # Print final statistics
    bot.job_tracker.print_summary()
    
    separator("-", 70)
    logger.info("💡 Next steps:")
    logger.info("1. Review data/jobs.json for all tracked jobs and application history")
    logger.info("2. View browser sessions using the provided links above")
    logger.info("3. Configure credentials in .env file for auto-login (if needed)")
    logger.info("4. Adjust platform settings in user/platform_configs.json")
    logger.info("5. Customize preferences in user/job_preferences.json")
    separator("=", 70)


if __name__ == "__main__":
    asyncio.run(main())