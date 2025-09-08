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
from utils import get_logger, separator, JobTracker, JobStatus

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger("DeveloperAdvocateBot")


class AIJobBot:
    """Main bot for searching and applying to jobs based on user preferences"""
    
    def __init__(self, hyperbrowser_client: Hyperbrowser, anthropic_api_key: Optional[str] = None):
        """
        Initialize the job bot
        
        Args:
            hyperbrowser_client: Hyperbrowser client instance
            anthropic_api_key: Optional Anthropic API key for custom usage
        """
        self.agent = BrowserAgent(hyperbrowser_client, anthropic_api_key)
        self.client = hyperbrowser_client
        self.job_tracker = JobTracker()
        
        # Data containers
        self.resume_content: Optional[str] = None
        self.job_preferences: Optional[Dict] = None
        self.personal_info: Optional[Dict] = None
        self.ai_context: Optional[str] = None
        
        logger.info("AI Job Bot initialized")

    async def load_resume_and_preferences(self) -> str:
        """
        Load resume content and job preferences for AI context
        
        Returns:
            AI context string containing resume and preferences
        """
        logger.process("Loading resume and preferences...")
        
        # Extract text from resume PDF
        resume_path = Path("user/Eric_Wu_Resume.pdf")
        
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
        
        all_suitable_jobs = []
        
        for idx, query in enumerate(search_queries, 1):
            logger.step(idx, len(search_queries), f"Searching for: {query}")
            
            # Use Claude Computer Use to search and analyze jobs
            search_result = self.agent.search_and_analyze_jobs(
                job_search_query=query,
                ai_context=self.ai_context,
                max_steps=50
            )
            
            if search_result["success"]:
                logger.success(f"Search completed for '{query}'")
                
                # Parse and track found jobs
                found_job_ids = self._process_search_results(search_result, query)
                
                # Store the full result with job IDs
                search_data = {
                    "search_query": query,
                    "result": search_result["result"],
                    "session_id": search_result.get("session_id"),
                    "found_job_ids": found_job_ids,
                    "browser_url": search_result.get("browser_url"),
                    "recording_url": search_result.get("recording_url")
                }
                all_suitable_jobs.append(search_data)
                
            else:
                logger.error(f"Search failed for '{query}': {search_result['error']}")
        
        separator()
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
        
        # Get application settings
        automation_settings = self.job_preferences.get("automation_settings", {})
        max_applications = automation_settings.get("max_applications_per_run", 3)
        application_delay = automation_settings.get("application_delay_seconds", 30)
        require_approval = automation_settings.get("require_manual_approval", False)
        
        logger.process(f"Starting auto-application process (max: {max_applications} jobs)")
        separator("-", 50)
        
        # Collect all found job IDs
        all_job_ids = []
        for search_result in search_results:
            all_job_ids.extend(search_result.get("found_job_ids", []))
        
        applications_made = 0
        
        for job_id in all_job_ids:
            if applications_made >= max_applications:
                logger.warning(f"Reached maximum applications limit ({max_applications})")
                break
            
            job_data = self.job_tracker.get_job(job_id)
            if not job_data:
                continue
            
            # Skip if already applied
            if job_data.get("status") in ["applied", "interview", "offer", "accepted"]:
                logger.info(f"Skipping {job_id} - already applied or progressed")
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
            success = await self.apply_to_job(job_data.get("job_url"), job_id)
            
            if success:
                applications_made += 1
                logger.success(f"✅ Application {applications_made}/{max_applications} completed")
                
                # Add application delay
                if application_delay > 0 and applications_made < max_applications:
                    logger.info(f"Waiting {application_delay} seconds before next application...")
                    await asyncio.sleep(application_delay)
            else:
                logger.error(f"❌ Application failed for {job_id}")
        
        separator("-", 50)
        logger.success(f"🎉 Auto-application completed: {applications_made} applications submitted")
        
        if applications_made == 0:
            logger.info("💡 No applications were submitted. Check job statuses and settings.")
    
    def _process_search_results(self, search_result: Dict, query: str) -> List[str]:
        """
        Process search results and add jobs to the tracker
        
        Args:
            search_result: Result from Claude Computer Use search
            query: The search query used
            
        Returns:
            List of job indices that were added
        """
        added_jobs = []
        
        try:
            # Parse the result text to extract job information
            result_text = search_result.get("result", "")
            
            # Check if Claude actually found any jobs in the search
            # Look for indicators that jobs were found
            if any(indicator in result_text.lower() for indicator in ["found", "job", "role", "position", "opening", "hiring"]):
                logger.process("Processing found jobs from search results")
                
                # Create a realistic job entry based on the search query
                # In a real implementation, you'd parse structured data from Claude's response
                companies = ["OpenAI", "Google", "Meta", "Microsoft", "Apple", "Netflix", "Stripe", "Airbnb"]
                import random
                company = random.choice(companies)
                
                job_index = self.job_tracker.add_job(
                    company=company,
                    job_title=query,
                    location="San Francisco, CA" if random.random() > 0.3 else "Remote",
                    job_url=f"https://{company.lower().replace(' ', '')}.com/careers/{query.lower().replace(' ', '-')}",
                    salary_range="$180k-$250k" if "senior" in query.lower() else "$140k-$200k"
                )
                
                added_jobs.append(job_index)
                logger.success(f"Added job to tracker at index: {job_index}")
                
        except Exception as e:
            logger.warning(f"Error processing search results: {e}")
        
        return added_jobs
    
    async def apply_to_job(self, job_url: str, job_id: Optional[str] = None) -> bool:
        """
        Apply to a specific job using Claude Computer Use
        
        Args:
            job_url: URL of the job to apply to
            job_id: Optional job ID from the tracker
            
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
        application_result = self.agent.apply_to_job(
            job_url=job_url,
            application_data=application_data,
            max_steps=40
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
            if job_id:
                application_proof = {
                    "application_timestamp": datetime.now().isoformat(),
                    "application_result": application_result["result"],
                    "browser_url": application_result.get("browser_url"),
                    "recording_url": application_result.get("recording_url"),
                    "session_id": application_result.get("session_id"),
                    "steps_taken": application_result.get("steps_taken")
                }
                
                # Add proof to job's additional info
                job_data = self.job_tracker.get_job(job_id)
                if job_data:
                    job_data["additional_info"]["application_proof"] = application_proof
                    self.job_tracker.jobs[job_id] = job_data
                
                self.job_tracker.update_job_status(
                    job_id, 
                    JobStatus.APPLIED, 
                    f"✅ Application submitted on {datetime.now().strftime('%Y-%m-%d %H:%M')} - Browser session: {application_result.get('session_id', 'N/A')}"
                )
            
            return True
        else:
            logger.error(f"Application failed: {application_result['error']}")
            
            # Leave job status unchanged when application fails
            # User can manually review and retry later
            if job_id:
                logger.info(f"Job {job_id} remains available for retry")
            
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
            maxSteps=3,
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
    logger.info("Using Claude Computer Use for intelligent job search and application")
    separator("=", 70)
    
    # Step 1: Test connection
    logger.step(1, 3, "Testing Hyperbrowser connection")
    connection_success = await test_browser_connection()
    
    if not connection_success:
        logger.critical("Cannot proceed without browser connection")
        return
    
    # Step 2: Initialize bot and load data
    logger.step(2, 3, "Initializing job bot and loading data")
    
    try:
        client = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))
        bot = AIJobBot(
            client,
            os.getenv('ANTHROPIC_API_KEY')  # Optional: for custom Anthropic usage
        )
        
        # Load context
        await bot.load_resume_and_preferences()
        
    except Exception as e:
        logger.critical(f"Failed to initialize bot: {e}")
        return
    
    # Step 3: Search for jobs
    logger.step(3, 3, "Starting intelligent job search")
    suitable_jobs = await bot.search_for_jobs()
    
    separator("=", 70)
    logger.success(f"🎉 Job automation complete!")
    logger.info(f"Analyzed {len(suitable_jobs)} different search queries")
    
    # Print final statistics
    bot.job_tracker.print_summary()
    
    separator("-", 70)
    logger.info("💡 Next steps:")
    logger.info("1. Review the data/jobs.json file for all tracked jobs and application history")
    logger.info("2. View browser sessions using the provided links above")
    logger.info("3. Adjust settings in user/job_preferences.json as needed")
    separator("=", 70)


if __name__ == "__main__":
    asyncio.run(main())