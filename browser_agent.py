"""
Browser automation agent using Claude Computer Use through Hyperbrowser
Handles job searching, analysis, and application automation
"""

from typing import Dict, Optional, Any
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartClaudeComputerUseTaskParams

from utils import get_logger

logger = get_logger("BrowserAgent")


class BrowserAgent:
    """
    Browser automation agent that uses Claude Computer Use for intelligent web interactions
    """
    
    def __init__(self, hyperbrowser_client: Hyperbrowser, anthropic_api_key: Optional[str] = None):
        """
        Initialize the browser agent
        
        Args:
            hyperbrowser_client: Hyperbrowser client instance
            anthropic_api_key: Optional Anthropic API key for custom usage
        """
        if not hyperbrowser_client:
            raise ValueError("Hyperbrowser client is required for Browser Agent")
        
        self.hyperbrowser_client = hyperbrowser_client
        self.anthropic_api_key = anthropic_api_key
        self.current_session_id: Optional[str] = None
        
        logger.info("Browser Agent initialized")
        if anthropic_api_key:
            logger.debug("Using custom Anthropic API key")
        else:
            logger.debug("Using Hyperbrowser's built-in Claude access")

    def execute_computer_use_task(self, 
                                  task: str, 
                                  max_steps: int = 50, 
                                  session_id: Optional[str] = None,
                                  keep_browser_open: bool = True) -> Dict[str, Any]:
        """
        Execute a task using Claude Computer Use through Hyperbrowser
        
        Args:
            task: The task description for Claude to execute
            max_steps: Maximum number of steps Claude can take
            session_id: Optional session ID to reuse an existing browser session
            keep_browser_open: Whether to keep the browser open after task completion
            
        Returns:
            Dictionary with success status, result, and session information
        """
        logger.process(f"Executing Computer Use task (max steps: {max_steps})")
        logger.debug(f"Task preview: {task[:100]}...")
        
        # Build parameters for Claude Computer Use
        params = StartClaudeComputerUseTaskParams(
            task=task,
            maxSteps=max_steps,
            keepBrowserOpen=keep_browser_open,
        )
        
        # Reuse existing session if provided
        if session_id:
            params.sessionId = session_id
            logger.debug(f"Reusing session: {session_id}")
        
        # Use custom Anthropic API key if provided
        if self.anthropic_api_key:
            params.useCustomApiKeys = True
            logger.debug("Using custom API keys")
        
        try:
            logger.info("Starting Claude Computer Use task...")
            response = self.hyperbrowser_client.agents.claude_computer_use.start_and_wait(params)
            
            # Store session ID for potential reuse (handle missing attribute gracefully)
            session_id = getattr(response.data, 'session_id', None)
            if session_id:
                self.current_session_id = session_id
            
            result = {
                "success": True,
                "result": response.data.final_result,
                "session_id": session_id,
                "steps_taken": getattr(response.data, 'steps_taken', None),
                "browser_url": getattr(response.data, 'browser_url', None),
                "recording_url": getattr(response.data, 'recording_url', None)
            }
            
            logger.success("Computer Use task completed successfully")
            if result.get("steps_taken"):
                logger.data(f"Steps taken: {result['steps_taken']}")
            
            # Display browser viewing links if available
            if result.get("browser_url"):
                logger.success(f"🌐 Live Browser View: {result['browser_url']}")
            if result.get("recording_url"):
                logger.success(f"📹 Recording Playback: {result['recording_url']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Computer Use task failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id or self.current_session_id
            }

    def search_and_analyze_jobs(self, 
                                job_search_query: str, 
                                ai_context: str, 
                                max_steps: int = 50,
                                platform: str = "linkedin") -> Dict[str, Any]:
        """
        Search for jobs on specific platforms using Claude Computer Use
        
        Args:
            job_search_query: The job search query (e.g., "Developer Advocate")
            ai_context: AI context containing resume and preferences
            max_steps: Maximum steps for Claude to take
            platform: Job platform to search (remoteok, weworkremotely, glassdoor, etc.)
            
        Returns:
            Dictionary with search results, platform info, and found jobs
        """
        platform_urls = {
            "remoteok": "https://remoteok.io/remote-jobs",
            "weworkremotely": "https://weworkremotely.com/categories/remote-programming-jobs",
            "glassdoor": "https://www.glassdoor.com/Job/jobs.htm"
        }
        
        platform_url = platform_urls.get(platform, platform_urls["remoteok"])
        logger.info(f"🔍 {platform.title()}: {job_search_query}")
        
        # Construct the search task for Claude
        task = f"""
        Go to {platform_url} and search for: "{job_search_query}"
        
        Context for job evaluation:
        {ai_context}
        
        Tasks:
        1. Navigate to {platform_url}
        2. Search for "{job_search_query}"
        3. Review first 5-10 job listings
        4. For each relevant job, extract:
           - Job title
           - Company name
           - Location (remote/hybrid/onsite and city if applicable)
           - Key requirements (top 3-5 bullet points)
           - Why it's a good match based on the candidate's profile
           - Application link or how to apply
           - Salary range (if available)
        5. Return the results in a structured format
        
        Focus on roles matching the user's preferences and experience.
        """
        
        # Execute the search
        result = self.execute_computer_use_task(
            task=task, 
            max_steps=max_steps,
            session_id=self.current_session_id
        )
        
        # Add platform information to result
        if result.get("success"):
            result["platform"] = platform
            result["platform_url"] = platform_url
        
        return result

    def apply_to_job(self, 
                    job_url: str, 
                    application_data: Dict[str, str], 
                    session_id: Optional[str] = None, 
                    max_steps: int = 40,
                    additional_instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Use Claude Computer Use to apply to a specific job
        
        Args:
            job_url: URL of the job application
            application_data: Dictionary containing application information
            session_id: Optional session ID to reuse
            max_steps: Maximum steps for Claude to take
            additional_instructions: Optional additional instructions for the application
            
        Returns:
            Dictionary with application result and session information
        """
        logger.process(f"Applying to job at: {job_url}")
        
        # Extract application data
        name = application_data.get('name', '')
        email = application_data.get('email', '')
        phone = application_data.get('phone', '')
        linkedin = application_data.get('linkedin', '')
        github = application_data.get('github', '')
        
        logger.data("Using application data", {
            "name": name,
            "email": email,
            "has_linkedin": bool(linkedin),
            "has_github": bool(github)
        })
        
        # Build the application task
        task = f"""
        Apply to the job at this URL: {job_url}
        
        Use this information to fill out the application:
        Name: {name}
        Email: {email}
        Phone: {phone}
        LinkedIn: {linkedin}
        GitHub: {github}
        
        Please:
        1. Navigate to the job application page
        2. Fill out all required fields with the provided information
        3. If there's a resume upload option, mention that a resume upload is needed (but don't actually upload)
        4. For cover letters or additional questions:
           - Mention the candidate is a YouTube creator (@EricWTech with 20K+ subscribers)
           - Highlight experience in AI automation and full-stack development
           - Express genuine enthusiasm for developer advocacy
           - Keep responses professional but personable
        5. Review the application before submitting
        6. Only submit if everything looks correct
        7. Take a screenshot of the confirmation page if successful
        8. If the application requires creating an account, do so with the provided email
        
        {additional_instructions if additional_instructions else ''}
        
        Be careful and thorough - this is a real job application.
        If you encounter any errors or the application cannot be completed, please explain why.
        """
        
        return self.execute_computer_use_task(
            task=task, 
            max_steps=max_steps, 
            session_id=session_id or self.current_session_id
        )
    
    def close_session(self):
        """Close the current browser session if one exists"""
        if self.current_session_id:
            logger.info(f"Closing browser session: {self.current_session_id}")
            # Note: Actual session closing would depend on Hyperbrowser API
            # This is a placeholder for proper session management
            self.current_session_id = None
            logger.debug("Session closed")