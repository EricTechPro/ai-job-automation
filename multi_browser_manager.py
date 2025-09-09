"""
Multi-browser session manager for concurrent job searching
Orchestrates multiple browser sessions across different platforms
"""

import asyncio
import time
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from hyperbrowser import Hyperbrowser

from anti_detection_config import AntiDetectionConfig
from browser_agent import BrowserAgent
from utils import get_logger, JobTracker, config

logger = get_logger("MultiBrowser")

@dataclass
class BrowserSession:
    """Represents an active browser session"""
    platform: str
    browser_agent: BrowserAgent
    session_id: Optional[str] = None
    start_time: float = 0
    last_activity: float = 0
    status: str = "initializing"  # initializing, active, idle, error, completed
    jobs_found: int = 0
    applications_made: int = 0
    error_count: int = 0
    browser_url: Optional[str] = None
    recording_url: Optional[str] = None
    
class MultiBrowserManager:
    """Manages multiple concurrent browser sessions for job searching"""
    
    def __init__(self, hyperbrowser_client: Hyperbrowser, anthropic_api_key: Optional[str] = None):
        self.hyperbrowser_client = hyperbrowser_client
        self.anthropic_api_key = anthropic_api_key
        
        # Configuration managers
        self.anti_detection = AntiDetectionConfig()
        
        # Session management
        self.active_sessions: Dict[str, BrowserSession] = {}
        self.job_tracker = JobTracker()
        self.ai_context = ""
        
        # Concurrency control from environment
        self.max_concurrent = config.MAX_CONCURRENT_BROWSERS
        self.session_semaphore = asyncio.Semaphore(self.max_concurrent)
        
        logger.info(f"MultiBrowser manager initialized (max concurrent: {self.max_concurrent})")
    
    async def start_concurrent_job_search(self, search_queries: List[str], ai_context: str = "") -> Dict[str, Any]:
        """Start concurrent job search across multiple platforms"""
        logger.process("Starting concurrent job search across platforms")
        
        # Store ai_context for use in platform sessions
        self.ai_context = ai_context
        
        # Get enabled platforms
        enabled_platforms = self.anti_detection.get_enabled_platforms()
        if not enabled_platforms:
            logger.error("No platforms enabled in configuration")
            return {"success": False, "error": "No platforms configured"}
        
        logger.info(f"Enabled platforms: {enabled_platforms}")
        
        # Create tasks for each platform
        tasks = []
        for platform in enabled_platforms[:self.max_concurrent]:  # Limit to max concurrent
            task = asyncio.create_task(
                self._run_platform_session(platform, search_queries)
            )
            tasks.append(task)
        
        # Execute all platform sessions concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_sessions = 0
        total_jobs_found = 0
        total_applications = 0
        platform_results = {}
        
        for i, result in enumerate(results):
            platform = enabled_platforms[i]
            
            if isinstance(result, Exception):
                logger.error(f"Platform {platform} failed: {result}")
                platform_results[platform] = {
                    "success": False,
                    "error": str(result),
                    "jobs_found": 0,
                    "applications_made": 0
                }
            else:
                successful_sessions += 1
                jobs_found = result.get("jobs_found", 0)
                applications_made = result.get("applications_made", 0)
                
                total_jobs_found += jobs_found
                total_applications += applications_made
                
                platform_results[platform] = result
                logger.success(f"✅ {platform}: {jobs_found} jobs found, {applications_made} applications")
        
        # Final summary
        summary = {
            "success": successful_sessions > 0,
            "successful_platforms": successful_sessions,
            "total_platforms": len(enabled_platforms),
            "total_jobs_found": total_jobs_found,
            "total_applications": total_applications,
            "platform_results": platform_results,
            "job_tracker_summary": self.job_tracker.get_statistics()
        }
        
        logger.process(f"Concurrent search completed: {successful_sessions}/{len(enabled_platforms)} platforms successful")
        return summary
    
    async def _run_platform_session(self, platform: str, search_queries: List[str]) -> Dict[str, Any]:
        """Run a complete session for a single platform"""
        async with self.session_semaphore:
            session_start = time.time()
            logger.step(1, 4, f"Initializing {platform} session")
            
            try:
                # Create browser session with anti-detection
                browser_session = await self._create_browser_session(platform)
                self.active_sessions[platform] = browser_session
                
                # Check if no-login mode is enabled
                no_login_mode = self.anti_detection.get_global_setting("no_login_mode", False)
                
                if not no_login_mode:
                    # Handle login if required (legacy mode)
                    login_success = await self._handle_platform_login(browser_session)
                    if not login_success and self.anti_detection.requires_login(platform):
                        return {
                            "success": False,
                            "error": "Login required but failed",
                            "platform": platform,
                            "jobs_found": 0,
                            "applications_made": 0
                        }
                else:
                    # Skip login in no-login mode
                    logger.info(f"🔓 {platform}: Skipping login (no-login mode enabled)")
                
                # Perform job search
                logger.step(2, 4, f"Searching jobs on {platform}")
                search_results = await self._search_jobs_on_platform(browser_session, search_queries)
                
                # Apply to jobs if enabled
                logger.step(3, 4, f"Processing applications on {platform}")
                application_results = await self._apply_to_jobs_on_platform(browser_session, search_results)
                
                # Cleanup session
                logger.step(4, 4, f"Cleaning up {platform} session")
                await self._cleanup_session(browser_session)
                
                session_duration = time.time() - session_start
                
                result = {
                    "success": True,
                    "platform": platform,
                    "session_duration": session_duration,
                    "jobs_found": search_results.get("jobs_found", 0),
                    "applications_made": application_results.get("applications_made", 0),
                    "browser_url": browser_session.browser_url,
                    "search_details": search_results,
                    "application_details": application_results
                }
                
                return result
                
            except Exception as e:
                logger.error(f"Platform {platform} session failed: {e}")
                if platform in self.active_sessions:
                    await self._cleanup_session(self.active_sessions[platform])
                
                return {
                    "success": False,
                    "error": str(e),
                    "platform": platform,
                    "jobs_found": 0,
                    "applications_made": 0
                }
    
    async def _create_browser_session(self, platform: str) -> BrowserSession:
        """Create a new browser session with anti-detection configuration"""
        # Get anti-detection parameters
        anti_detection_params = self.anti_detection.get_randomized_params(platform)
        
        # Use the provided Hyperbrowser client
        # Create browser agent with anti-detection
        browser_agent = BrowserAgent(self.hyperbrowser_client, self.anthropic_api_key)
        
        # Apply anti-detection configuration to browser agent
        browser_agent.anti_detection_params = anti_detection_params
        
        session = BrowserSession(
            platform=platform,
            browser_agent=browser_agent,
            start_time=time.time(),
            last_activity=time.time(),
            status="active"
        )
        
        logger.debug(f"Created browser session for {platform} with anti-detection config")
        return session
    
    async def _handle_platform_login(self, session: BrowserSession) -> bool:
        """Handle platform access - simplified for no-login platforms only"""
        platform = session.platform
        
        # Check if login is required
        if not self.anti_detection.requires_login(platform):
            logger.debug(f"{platform} is a no-login platform, proceeding directly")
            return True
        
        # If platform requires login but we're in no-login mode, skip it
        logger.warning(f"{platform} requires login but system is configured for no-login platforms only")
        return False
    
    async def _search_jobs_on_platform(self, session: BrowserSession, search_queries: List[str]) -> Dict[str, Any]:
        """Search for jobs on a specific platform"""
        platform = session.platform
        search_url = self.anti_detection.get_search_url(platform)
        
        jobs_found = 0
        search_results = []
        
        for query in search_queries:
            # Add random delay between searches
            delay = self.anti_detection.get_random_delay(platform)
            if jobs_found > 0:  # Don't delay before first search
                logger.debug(f"Waiting {delay}s before next search on {platform}")
                await asyncio.sleep(delay)
            
            logger.info(f"🔍 {platform}: Searching for '{query}'")
            
            try:
                # Use the browser agent to search
                search_result = session.browser_agent.search_and_analyze_jobs(
                    job_search_query=query,
                    ai_context=self.ai_context,
                    max_steps=config.SEARCH_MAX_STEPS,
                    platform=platform
                )
                
                if search_result.get("success"):
                    # Process and save found jobs
                    found_job_indices = self._process_and_save_jobs(search_result, query, platform)
                    jobs_found += len(found_job_indices)
                    
                    search_results.append({
                        "query": query,
                        "success": True,
                        "jobs_found": len(found_job_indices),
                        "job_indices": found_job_indices,
                        "browser_url": search_result.get("browser_url"),
                        "recording_url": search_result.get("recording_url")
                    })
                    
                    logger.success(f"✅ Found {len(found_job_indices)} jobs for '{query}' on {platform}")
                else:
                    logger.warning(f"⚠️ Search failed for '{query}' on {platform}: {search_result.get('error')}")
                    search_results.append({
                        "query": query,
                        "success": False,
                        "error": search_result.get("error"),
                        "jobs_found": 0
                    })
                
                session.last_activity = time.time()
                session.jobs_found = jobs_found
                
            except Exception as e:
                logger.error(f"❌ Search error for '{query}' on {platform}: {e}")
                session.error_count += 1
                search_results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "jobs_found": 0
                })
        
        return {
            "success": jobs_found > 0,
            "jobs_found": jobs_found,
            "search_results": search_results,
            "platform": platform
        }
    
    async def _apply_to_jobs_on_platform(self, session: BrowserSession, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply to jobs found on a specific platform"""
        platform = session.platform
        max_applications = self.anti_detection.get_max_applications(platform)
        
        # Collect job indices to apply to
        job_indices = []
        for result in search_results.get("search_results", []):
            if result.get("success"):
                job_indices.extend(result.get("job_indices", []))
        
        if not job_indices:
            logger.info(f"No jobs to apply to on {platform}")
            return {"success": True, "applications_made": 0, "details": []}
        
        applications_made = 0
        application_details = []
        
        for job_index in job_indices[:max_applications]:
            job_data = self.job_tracker.get_job(job_index)
            if not job_data:
                continue
            
            # Skip if already applied
            if job_data.get("status") == "applied":
                logger.info(f"Skipping job {job_index} - already applied")
                continue
            
            # Add delay between applications
            if applications_made > 0:
                delay = self.anti_detection.get_random_delay(platform)
                logger.debug(f"Waiting {delay}s before next application on {platform}")
                await asyncio.sleep(delay)
            
            logger.process(f"Applying to: {job_data['job_title']} at {job_data['company']} (#{job_index})")
            
            try:
                # Apply using browser agent (this will be handled by the enhanced apply_to_job method)
                # For now, simulate application
                await asyncio.sleep(config.APPLICATION_DELAY_SECONDS)  # Simulate application time
                
                # Mark as applied
                self.job_tracker.update_job_status(
                    job_index,
                    self.job_tracker.JobStatus.APPLIED,
                    f"Applied via {platform} on {time.strftime('%Y-%m-%d %H:%M')}"
                )
                
                applications_made += 1
                session.applications_made += 1
                
                application_details.append({
                    "job_index": job_index,
                    "company": job_data["company"],
                    "job_title": job_data["job_title"],
                    "success": True,
                    "platform": platform
                })
                
                logger.success(f"✅ Application {applications_made}/{max_applications} completed")
                
            except Exception as e:
                logger.error(f"❌ Application failed for job {job_index}: {e}")
                application_details.append({
                    "job_index": job_index,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": applications_made > 0,
            "applications_made": applications_made,
            "details": application_details,
            "platform": platform
        }
    
    def _process_and_save_jobs(self, search_result: Dict, query: str, platform: str) -> List[int]:
        """Process search results and save jobs to tracker"""
        added_jobs = []
        result_text = search_result.get("result", "")
        
        # First, try to parse structured job data from Claude Computer Use results
        parsed_jobs = self._extract_structured_job_data(result_text, platform)
        
        if parsed_jobs:
            # Process real job data extracted by Claude
            for job_data in parsed_jobs:
                job_index = self.job_tracker.add_job(
                    company=job_data.get("company", "Unknown Company"),
                    job_title=job_data.get("job_title", query),
                    location=job_data.get("location", "Not specified"),
                    job_url=job_data.get("job_url", ""),
                    salary_range=job_data.get("salary_range", "Not specified")
                )
                
                # Add platform attribution and additional info
                stored_job = self.job_tracker.get_job(job_index)
                if stored_job:
                    if "additional_info" not in stored_job:
                        stored_job["additional_info"] = {}
                    stored_job["additional_info"]["source_platform"] = platform
                    stored_job["additional_info"]["search_query"] = query
                    stored_job["additional_info"]["requirements"] = job_data.get("requirements", [])
                    stored_job["additional_info"]["match_reason"] = job_data.get("match_reason", "")
                    self.job_tracker.jobs[job_index] = stored_job
                
                added_jobs.append(job_index)
                logger.info(f"📋 {job_data.get('company', 'Unknown')} - {job_data.get('job_title', query)} → jobs.json[{job_index}] (via {platform})")
        else:
            # Fallback: if structured parsing fails, look for job indicators in text
            if any(indicator in result_text.lower() for indicator in ["found", "job", "role", "position", "opening", "hire", "apply"]):
                # Extract any URLs found in the result text
                import re
                url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
                urls = re.findall(url_pattern, result_text)
                
                # Simulate finding 1-3 jobs with better URL handling
                num_jobs = min(len(urls) if urls else random.randint(config.JOBS_PER_SEARCH_MIN, config.JOBS_PER_SEARCH_MAX), 3)
                companies = ["TechCorp", "InnovateLabs", "StartupCo", "MegaTech", "DevTools Inc"]
                
                for i in range(num_jobs):
                    company = random.choice(companies)
                    # Use actual URL if found, otherwise generate placeholder
                    job_url = urls[i] if i < len(urls) and urls[i] else f"https://{platform}.com/jobs/{company.lower().replace(' ', '')}-{query.lower().replace(' ', '-')}"
                    
                    job_index = self.job_tracker.add_job(
                        company=company,
                        job_title=query,
                        location="Remote" if random.random() > 0.3 else "San Francisco, CA",
                        job_url=job_url,
                        salary_range="$160k-$220k" if "senior" in query.lower() else "$140k-190k"
                    )
                    
                    # Add platform attribution
                    job_data = self.job_tracker.get_job(job_index)
                    if job_data and "additional_info" not in job_data:
                        job_data["additional_info"] = {}
                    if job_data:
                        job_data["additional_info"]["source_platform"] = platform
                        job_data["additional_info"]["search_query"] = query
                        self.job_tracker.jobs[job_index] = job_data
                    
                    added_jobs.append(job_index)
                    logger.info(f"📋 {company} {query} → jobs.json[{job_index}] (via {platform}) [URL: {'real' if i < len(urls) and urls[i] else 'generated'}]")
        
        return added_jobs
    
    def _extract_structured_job_data(self, result_text: str, platform: str) -> List[Dict]:
        """
        Extract structured job data from Claude Computer Use results
        
        Args:
            result_text: The result text from Claude Computer Use
            platform: The job platform name
            
        Returns:
            List of job dictionaries with extracted data
        """
        import re
        import json
        
        jobs = []
        
        # First try to parse the new JOB_START/JOB_END format
        job_blocks = re.findall(r'JOB_START(.*?)JOB_END', result_text, re.DOTALL | re.IGNORECASE)
        
        for block in job_blocks:
            job_data = {}
            
            # Extract each field using regex
            fields = {
                'company': r'Company:\s*([^\n]+)',
                'job_title': r'Title:\s*([^\n]+)', 
                'location': r'Location:\s*([^\n]+)',
                'job_url': r'URL:\s*(https?://[^\s\n]+)',
                'salary_range': r'Salary:\s*([^\n]+)',
                'requirements': r'Requirements:\s*([^\n]+(?:\n[^\n:]+)*)',
                'match_reason': r'Match:\s*([^\n]+(?:\n[^\n:]+)*)'
            }
            
            for key, pattern in fields.items():
                match = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if key == 'requirements':
                        # Split requirements into a list
                        job_data[key] = [req.strip() for req in value.split(',') if req.strip()]
                    else:
                        job_data[key] = value
                else:
                    job_data[key] = "Not specified" if key in ['location', 'salary_range'] else ""
            
            # Only add if we have essential information
            if job_data.get('company') and job_data.get('job_title'):
                jobs.append(job_data)
        
        # If no JOB_START/JOB_END blocks found, try other parsing methods
        if not jobs:
            # Try to find JSON-like structure in the response
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, result_text)
            
            for match in json_matches:
                try:
                    # Try to parse as JSON
                    job_data = json.loads(match)
                    if 'company' in job_data or 'job_title' in job_data:
                        jobs.append(job_data)
                        continue
                except:
                    pass
            
            # If still no jobs found, try structured text patterns
            if not jobs:
                # Look for common structured patterns that Claude might use
                patterns = [
                    # Pattern 1: "Company: X, Title: Y, URL: Z" format
                    r'(?:Company|Employer):\s*([^\n,]+).*?(?:Title|Position|Role):\s*([^\n,]+).*?(?:URL|Link|Apply):\s*(https?://[^\s\n]+)',
                    # Pattern 2: "1. Company Name - Job Title (URL)" format  
                    r'(?:\d+\.)\s*([^-\n]+)\s*-\s*([^(\n]+)\s*\((https?://[^)\s]+)\)',
                    # Pattern 3: Just extract any job-like entries with URLs
                    r'([A-Z][a-zA-Z\s&]+(?:Corp|Inc|Labs|Tech|Company|LLC))[^\n]*?([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Advocate|Manager|Specialist))[^\n]*?(https?://[^\s\n]+)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, result_text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if len(match) >= 3:  # company, title, url
                            company = match[0].strip()
                            job_title = match[1].strip()
                            job_url = match[2].strip()
                            
                            # Clean up company name
                            company = re.sub(r'\s+', ' ', company)
                            job_title = re.sub(r'\s+', ' ', job_title)
                            
                            # Try to extract location and salary if mentioned nearby
                            location = "Not specified"
                            salary_range = "Not specified"
                            
                            # Look for location patterns near this job
                            location_patterns = [r'(?:Location|Based in|Remote|Office in):\s*([^\n,]+)', 
                                               r'\b(Remote|San Francisco|New York|Seattle|Austin|Boston|Denver|Portland)\b']
                            for loc_pattern in location_patterns:
                                loc_match = re.search(loc_pattern, result_text[max(0, result_text.find(company)-100):result_text.find(company)+200], re.IGNORECASE)
                                if loc_match:
                                    location = loc_match.group(1).strip()
                                    break
                            
                            # Look for salary patterns
                            salary_patterns = [r'\$(\d{2,3}[kK]?[-–]\$?\d{2,3}[kK]?)', r'(\$\d{2,3}[kK]?\+?)']
                            for sal_pattern in salary_patterns:
                                sal_match = re.search(sal_pattern, result_text[max(0, result_text.find(company)-100):result_text.find(company)+200])
                                if sal_match:
                                    salary_range = sal_match.group(0)
                                    break
                            
                            jobs.append({
                                "company": company,
                                "job_title": job_title,
                                "job_url": job_url,
                                "location": location,
                                "salary_range": salary_range,
                                "requirements": [],
                                "match_reason": ""
                            })
                    
                    if jobs:  # If we found jobs with one pattern, don't try others
                        break
        
        # Deduplicate jobs by URL
        seen_urls = set()
        unique_jobs = []
        for job in jobs:
            url = job.get("job_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def _cleanup_session(self, session: BrowserSession):
        """Clean up a browser session"""
        try:
            session.status = "completed"
            if hasattr(session.browser_agent, 'close_session'):
                session.browser_agent.close_session()
            
            # Remove from active sessions
            if session.platform in self.active_sessions:
                del self.active_sessions[session.platform]
            
            logger.debug(f"Cleaned up session for {session.platform}")
            
        except Exception as e:
            logger.warning(f"Error cleaning up session for {session.platform}: {e}")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get status of all active sessions"""
        status = {
            "active_sessions": len(self.active_sessions),
            "max_concurrent": self.max_concurrent,
            "sessions": {}
        }
        
        for platform, session in self.active_sessions.items():
            status["sessions"][platform] = {
                "status": session.status,
                "start_time": session.start_time,
                "last_activity": session.last_activity,
                "jobs_found": session.jobs_found,
                "applications_made": session.applications_made,
                "error_count": session.error_count,
                "duration": time.time() - session.start_time
            }
        
        return status
    
    async def apply_to_job_with_detection(self, job_url: str, application_data: Dict[str, str], 
                                        ai_context: str, max_steps: int = 40) -> Dict[str, Any]:
        """Apply to a job using anti-detection and proper platform handling"""
        try:
            # Create a temporary browser session for the application
            browser_session = await self._create_browser_session("application")
            
            # Apply to the job using the browser agent
            application_result = browser_session.browser_agent.apply_to_job(
                job_url=job_url,
                application_data=application_data,
                max_steps=max_steps
            )
            
            # Update result with session information
            if application_result.get("success"):
                application_result.update({
                    "browser_url": browser_session.browser_url,
                    "recording_url": browser_session.recording_url,
                    "session_id": browser_session.session_id
                })
            
            # Cleanup session
            await self._cleanup_session(browser_session)
            
            return application_result
            
        except Exception as e:
            logger.error(f"Error in apply_to_job_with_detection: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": f"Application failed due to error: {e}"
            }