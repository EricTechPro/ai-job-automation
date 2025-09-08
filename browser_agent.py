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
                                job_boards: Optional[list] = None) -> Dict[str, Any]:
        """
        Use Claude Computer Use to search for jobs and analyze them
        
        Args:
            job_search_query: The job search query (e.g., "Developer Advocate")
            ai_context: AI context containing resume and preferences
            max_steps: Maximum steps for Claude to take
            job_boards: List of job boards to search (defaults to major platforms)
            
        Returns:
            Dictionary with search results and session information
        """
        logger.process(f"Searching for jobs: '{job_search_query}'")
        
        # Default job boards if not specified
        if not job_boards:
            job_boards = ["LinkedIn", "Indeed", "or similar major job board"]
            
        job_boards_str = ", ".join(job_boards)
        
        # Construct the search task for Claude
        task = f"""
        Search for jobs matching this query: "{job_search_query}"
        
        Use this context to evaluate if jobs are a good match:
        {ai_context}
        
        Please:
        1. Go to a major job board ({job_boards_str})
        2. Search for the specified jobs: "{job_search_query}"
        3. Look through the first 10-15 job listings
        4. For each job that seems like a good match, extract:
           - Job title
           - Company name
           - Location (remote/hybrid/onsite and city if applicable)
           - Key requirements (top 3-5 bullet points)
           - Why it's a good match based on the candidate's profile
           - Application link or how to apply
           - Salary range (if available)
        5. Return the results in a structured format
        
        Focus on Developer Advocate, Developer Relations, Technical Evangelist, or similar roles at technology companies.
        Prioritize roles that match the candidate's experience with YouTube content creation and technical expertise.
        """
        
        logger.debug(f"Searching on: {job_boards_str}")
        
        return self.execute_computer_use_task(
            task=task, 
            max_steps=max_steps,
            session_id=self.current_session_id
        )

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
    
    def analyze_job_page(self, 
                        job_url: str, 
                        max_steps: int = 20) -> Dict[str, Any]:
        """
        Analyze a specific job posting page to extract detailed information
        
        Args:
            job_url: URL of the job posting
            max_steps: Maximum steps for Claude to take
            
        Returns:
            Dictionary with job details and analysis
        """
        logger.process(f"Analyzing job page: {job_url}")
        
        task = f"""
        Navigate to this job posting: {job_url}
        
        Please extract and analyze:
        1. Job title and company name
        2. Location and work arrangement (remote/hybrid/onsite)
        3. Salary range (if available)
        4. Required qualifications
        5. Preferred qualifications
        6. Job responsibilities
        7. Company culture and values
        8. Application deadline (if mentioned)
        9. Any unique benefits or perks
        10. Application process details
        
        Also assess:
        - How well this matches a Developer Advocate role
        - Company's focus on developer community
        - Opportunities for content creation and education
        
        Return a structured summary of all this information.
        """
        
        return self.execute_computer_use_task(
            task=task,
            max_steps=max_steps,
            session_id=self.current_session_id
        )
    
    def check_application_status(self, 
                                 company_portal_url: str,
                                 login_credentials: Dict[str, str],
                                 max_steps: int = 30) -> Dict[str, Any]:
        """
        Check the status of a job application through a company portal
        
        Args:
            company_portal_url: URL of the company's application portal
            login_credentials: Dictionary with 'email' and 'password' (if required)
            max_steps: Maximum steps for Claude to take
            
        Returns:
            Dictionary with application status information
        """
        logger.process(f"Checking application status at: {company_portal_url}")
        
        email = login_credentials.get('email', '')
        password = login_credentials.get('password', '')
        
        task = f"""
        Check job application status at: {company_portal_url}
        
        Login credentials (if needed):
        Email: {email}
        Password: {password}
        
        Please:
        1. Navigate to the application portal
        2. Log in if required (using provided credentials)
        3. Find the applications or candidate dashboard
        4. Look for any submitted applications
        5. For each application found, note:
           - Job title and company
           - Application date
           - Current status (submitted, reviewing, rejected, etc.)
           - Any messages or updates
           - Next steps if mentioned
        6. Take a screenshot of the status page
        
        If login fails or no applications are found, please explain what you observed.
        """
        
        return self.execute_computer_use_task(
            task=task,
            max_steps=max_steps,
            session_id=self.current_session_id
        )
    
    def close_session(self):
        """Close the current browser session if one exists"""
        if self.current_session_id:
            logger.info(f"Closing browser session: {self.current_session_id}")
            # Note: Actual session closing would depend on Hyperbrowser API
            # This is a placeholder for proper session management
            self.current_session_id = None
            logger.debug("Session closed")