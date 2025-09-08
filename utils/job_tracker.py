"""
Job tracking system for managing job applications and their statuses
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from utils.logger import get_logger

logger = get_logger("JobTracker")


class JobStatus(Enum):
    """Enumeration of possible job application statuses"""
    FOUND = "found"                    # Job found but not yet reviewed
    REVIEWED = "reviewed"              # Job reviewed and marked for application
    APPLIED = "applied"                # Application submitted


class JobTracker:
    """Manages job tracking data in JSON format"""
    
    def __init__(self, data_file: str = "data/jobs.json", backup_enabled: bool = False):
        """
        Initialize the job tracker
        
        Args:
            data_file: Path to the JSON file for storing job data
            backup_enabled: Whether to create backups of the data file
        """
        self.data_file = Path(data_file)
        self.backup_enabled = backup_enabled
        self.jobs = self._load_data()
        logger.info(f"Job tracker initialized with {len(self.jobs)} existing jobs")
    
    def _load_data(self) -> List[Dict]:
        """Load existing job data from JSON file as a list"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle migration from old dict format to new list format
                    if isinstance(data, dict):
                        logger.info("Migrating from dict to list format...")
                        job_list = list(data.values())
                        self._save_data_list(job_list)
                        return job_list
                    elif isinstance(data, list):
                        logger.debug(f"Loaded {len(data)} jobs from {self.data_file}")
                        return data
                    else:
                        logger.warning("Invalid data format, starting with empty list")
                        return []
            except json.JSONDecodeError as e:
                logger.error(f"Error loading JSON data: {e}")
                self._create_backup()
                return []
            except Exception as e:
                logger.error(f"Error reading data file: {e}")
                return []
        return []
    
    def _save_data(self):
        """Save job data to JSON file"""
        self._save_data_list(self.jobs)
    
    def _save_data_list(self, job_list: List[Dict]):
        """Helper method to save job list to JSON file"""
        try:
            # Create backup before saving
            if self.backup_enabled and self.data_file.exists():
                self._create_backup()
            
            # Ensure parent directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save data with proper formatting
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(job_list, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Saved {len(job_list)} jobs to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def _create_backup(self):
        """Create a backup of the current data file"""
        if not self.data_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.data_file.parent / f"{self.data_file.stem}_backup_{timestamp}.json"
        
        try:
            with open(self.data_file, 'r') as source:
                with open(backup_file, 'w') as backup:
                    backup.write(source.read())
            logger.debug(f"Created backup: {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _generate_job_id(self, company: str, job_title: str) -> str:
        """Generate a unique job ID"""
        # Create a readable ID from company and job title
        company_clean = company.lower().replace(' ', '_').replace('.', '')[:20]
        title_clean = job_title.lower().replace(' ', '_')[:30]
        timestamp = datetime.now().strftime("%Y%m%d")
        
        base_id = f"{company_clean}_{title_clean}_{timestamp}"
        
        # Ensure uniqueness
        if base_id not in self.jobs:
            return base_id
        
        # Add counter if needed
        counter = 1
        while f"{base_id}_{counter}" in self.jobs:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    def add_job(self, 
                company: str,
                job_title: str,
                location: str = "",
                job_url: str = "",
                salary_range: str = "",
                # Legacy parameters for backward compatibility
                description: str = "",
                requirements: List[str] = None,
                remote: bool = False,
                job_board: str = "",
                additional_info: Dict = None) -> str:
        """
        Add a new job to the tracker with simplified data format
        Only stores: company, job_title, location, job_url, salary_range, status, last_updated
        
        Returns:
            The index of the newly added job in the list
        """
        # Check for duplicates
        for i, existing_job in enumerate(self.jobs):
            if (existing_job.get("company", "").lower() == company.lower() and 
                existing_job.get("job_title", "").lower() == job_title.lower()):
                logger.info(f"Job already exists at index {i}: {job_title} at {company}")
                return i
        
        # Simplified job data structure
        job_data = {
            "company": company,
            "job_title": job_title,
            "location": location,
            "job_url": job_url,
            "salary_range": salary_range,
            "status": JobStatus.FOUND.value,
            "last_updated": datetime.now().isoformat()
        }
        
        # Add to list
        self.jobs.append(job_data)
        job_index = len(self.jobs) - 1
        self._save_data()
        
        logger.job_found(job_title, company, location)
        logger.data(f"Job added at index: {job_index}", {"status": JobStatus.FOUND.value})
        
        return job_index
    
    def update_job_status(self, job_index: int, status: JobStatus, note: str = "") -> bool:
        """
        Update the status of a job
        
        Args:
            job_index: The index of the job to update in the list
            status: The new status
            note: Optional note about the status change
        
        Returns:
            True if successful, False otherwise
        """
        if job_index < 0 or job_index >= len(self.jobs):
            logger.error(f"Job index out of range: {job_index}")
            return False
        
        old_status = self.jobs[job_index]["status"]
        self.jobs[job_index]["status"] = status.value
        self.jobs[job_index]["last_updated"] = datetime.now().isoformat()
        
        # Log job applied status
        if status == JobStatus.APPLIED:
            logger.job_applied(self.jobs[job_index]["job_title"], self.jobs[job_index]["company"])
        
        self._save_data()
        
        logger.process(f"Updated job at index {job_index}: {old_status} → {status.value}")
        
        # Log note if provided (simplified - just in logs, not stored in JSON)
        if note:
            logger.info(f"Note for job {job_index}: {note}")
        
        return True
    
    def add_note(self, job_id: str, note: str) -> bool:
        """Add a note to a job"""
        if job_id not in self.jobs:
            logger.error(f"Job ID not found: {job_id}")
            return False
        
        note_entry = {
            "timestamp": datetime.now().isoformat(),
            "note": note
        }
        
        if "notes" not in self.jobs[job_id]:
            self.jobs[job_id]["notes"] = []
        
        self.jobs[job_id]["notes"].append(note_entry)
        self.jobs[job_id]["last_updated"] = datetime.now().isoformat()
        self._save_data()
        
        logger.debug(f"Added note to job {job_id}")
        
        return True
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a specific job by ID"""
        return self.jobs.get(job_id)
    
    def get_jobs_by_status(self, status: JobStatus) -> List[Dict]:
        """Get all jobs with a specific status"""
        return [
            job for job in self.jobs.values()
            if job["status"] == status.value
        ]
    
    def get_jobs_by_company(self, company: str) -> List[Dict]:
        """Get all jobs from a specific company"""
        return [
            job for job in self.jobs.values()
            if company.lower() in job["company"].lower()
        ]
    
    def search_jobs(self, query: str) -> List[Dict]:
        """Search jobs by title, company, or description"""
        query_lower = query.lower()
        results = []
        
        for job in self.jobs.values():
            if (query_lower in job.get("job_title", "").lower() or
                query_lower in job.get("company", "").lower() or
                query_lower in job.get("description", "").lower()):
                results.append(job)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked jobs"""
        stats = {
            "total_jobs": len(self.jobs),
            "by_status": {},
            "by_company": {},
            "by_job_board": {},
            "applied_count": 0
        }
        
        for job in self.jobs.values():
            # Count by status
            status = job.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by company
            company = job.get("company", "unknown")
            stats["by_company"][company] = stats["by_company"].get(company, 0) + 1
            
            # Count by job board
            job_board = job.get("job_board", "unknown")
            stats["by_job_board"][job_board] = stats["by_job_board"].get(job_board, 0) + 1
            
            # Count specific statuses
            if status == JobStatus.APPLIED.value:
                stats["applied_count"] += 1
        
        return stats
    
    def check_duplicate(self, company: str, job_title: str) -> Optional[str]:
        """
        Check if a job already exists
        
        Returns:
            Job ID if duplicate found, None otherwise
        """
        for job_id, job in self.jobs.items():
            if (job["company"].lower() == company.lower() and
                job["job_title"].lower() == job_title.lower()):
                return job_id
        return None
    
    def get_all_jobs_data(self):
        """Get all jobs data with metadata for viewing/export"""
        return {
            "jobs": list(self.jobs.values()),
            "last_updated": datetime.now().isoformat(),
            "total_jobs": len(self.jobs),
            "statistics": self.get_statistics()
        }
    
    def print_summary(self):
        """Print a summary of all tracked jobs"""
        stats = self.get_statistics()
        
        logger.separator()
        logger.info("📊 JOB TRACKER SUMMARY")
        logger.separator()
        
        logger.data(f"Total Jobs Tracked: {stats['total_jobs']}")
        
        if stats['by_status']:
            logger.info("\n📈 Jobs by Status:")
            for status, count in sorted(stats['by_status'].items()):
                logger.info(f"  • {status.title()}: {count}")
        
        if stats['applied_count'] > 0:
            logger.success(f"\n✅ Applications Submitted: {stats['applied_count']}")
        
        # Simplified workflow - only tracking applications
        
        logger.separator()