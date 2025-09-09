"""
Job tracking system for managing job applications and their statuses
"""

import json
import os
import fcntl
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
import threading

from utils.logger import get_logger

logger = get_logger("JobTracker")


class JobStatus(Enum):
    """Enumeration of possible job application statuses"""
    FOUND = "found"                    # Job found but not yet reviewed
    REVIEWED = "reviewed"              # Job reviewed and marked for application
    APPLIED = "applied"                # Application submitted


class JobTracker:
    """Manages job tracking data in JSON format with concurrent access support"""
    
    def __init__(self, data_file: str = "data/jobs.json", backup_enabled: bool = False):
        """
        Initialize the job tracker
        
        Args:
            data_file: Path to the JSON file for storing job data
            backup_enabled: Whether to create backups of the data file
        """
        self.data_file = Path(data_file)
        self.backup_enabled = backup_enabled
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.jobs = self._load_data()
        logger.info(f"Job tracker initialized with {len(self.jobs)} existing jobs")
    
    def _with_file_lock(self, file_path: Path, operation: str, func, *args, **kwargs):
        """Execute a function with file locking for concurrent access safety"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with open(file_path, 'r+' if operation == 'read' else 'w', encoding='utf-8') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    try:
                        return func(f, *args, **kwargs)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (BlockingIOError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.debug(f"File locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.warning(f"Failed to acquire file lock after {max_retries} attempts")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error in file operation: {e}")
                raise

    def _load_data(self) -> List[Dict]:
        """Load existing job data from JSON file as a list with concurrent access safety"""
        with self.lock:
            if not self.data_file.exists():
                return []
            
            def _load_json(f):
                f.seek(0)
                data = json.load(f)
                # Handle migration from old dict format to new list format
                if isinstance(data, dict):
                    logger.info("Migrating from dict to list format...")
                    job_list = list(data.values())
                    # Save the migrated data
                    self._save_data_list_locked(job_list)
                    return job_list
                elif isinstance(data, list):
                    logger.debug(f"Loaded {len(data)} jobs from {self.data_file}")
                    return data
                else:
                    logger.warning("Invalid data format, starting with empty list")
                    return []
            
            try:
                return self._with_file_lock(self.data_file, 'read', _load_json)
            except json.JSONDecodeError as e:
                logger.error(f"Error loading JSON data: {e}")
                self._create_backup()
                return []
            except Exception as e:
                logger.error(f"Error reading data file: {e}")
                return []
    
    def _save_data(self):
        """Save job data to JSON file with concurrent access safety"""
        with self.lock:
            self._save_data_list_locked(self.jobs)
    
    def _save_data_list(self, job_list: List[Dict]):
        """Helper method to save job list to JSON file (for backward compatibility)"""
        with self.lock:
            self._save_data_list_locked(job_list)
    
    def _save_data_list_locked(self, job_list: List[Dict]):
        """Internal method to save job list with file locking"""
        def _write_json(f, job_list):
            f.seek(0)
            f.truncate()
            json.dump(job_list, f, indent=2, ensure_ascii=False, default=str)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        try:
            # Create backup before saving
            if self.backup_enabled and self.data_file.exists():
                self._create_backup()
            
            # Ensure parent directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file if it doesn't exist
            if not self.data_file.exists():
                self.data_file.touch()
            
            # Save data with file locking
            self._with_file_lock(self.data_file, 'write', _write_json, job_list)
            
            logger.debug(f"Saved {len(job_list)} jobs to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise
    
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
                additional_info: Dict = None) -> int:
        """
        Add a new job to the tracker with simplified data format
        Only stores: company, job_title, location, job_url, salary_range, status, last_updated
        
        Returns:
            The index of the newly added job in the list
        """
        with self.lock:
            # Reload data to get latest state from disk (for concurrent access)
            self._reload_data()
            
            # Check for duplicates using the enhanced method
            duplicate_idx = self.check_duplicate(company, job_title, job_url)
            if duplicate_idx is not None:
                logger.info(f"Job already exists at index {duplicate_idx}: {job_title} at {company}")
                return duplicate_idx
            
            # Simplified job data structure
            job_data = {
                "company": company,
                "job_title": job_title,
                "location": location,
                "job_url": job_url,
                "salary_range": salary_range,
                "status": JobStatus.FOUND.value,
                "last_updated": datetime.now().isoformat(),
                "job_board": job_board  # Store job board for tracking
            }
            
            # Add additional info if provided
            if additional_info:
                job_data["additional_info"] = additional_info
            
            # Add to list
            self.jobs.append(job_data)
            job_index = len(self.jobs) - 1
            self._save_data()
            
            logger.job_found(job_title, company, location)
            logger.data(f"Job added at index: {job_index}", {"status": JobStatus.FOUND.value})
            
            return job_index
    
    def _reload_data(self):
        """Reload data from disk to get the latest state"""
        try:
            fresh_data = self._load_data()
            self.jobs = fresh_data
        except Exception as e:
            logger.warning(f"Failed to reload data: {e}")
            # Continue with current data
    
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
    
    def add_note(self, job_index: int, note: str) -> bool:
        """Add a note to a job"""
        if not (0 <= job_index < len(self.jobs)):
            logger.error(f"Job index out of range: {job_index}")
            return False
        
        note_entry = {
            "timestamp": datetime.now().isoformat(),
            "note": note
        }
        
        if "notes" not in self.jobs[job_index]:
            self.jobs[job_index]["notes"] = []
        
        self.jobs[job_index]["notes"].append(note_entry)
        self.jobs[job_index]["last_updated"] = datetime.now().isoformat()
        self._save_data()
        
        logger.debug(f"Added note to job {job_index}")
        
        return True
    
    def get_job(self, job_index: int) -> Optional[Dict]:
        """Get a specific job by index"""
        if 0 <= job_index < len(self.jobs):
            return self.jobs[job_index]
        return None
    
    def get_jobs_by_status(self, status: JobStatus) -> List[Dict]:
        """Get all jobs with a specific status"""
        return [
            job for job in self.jobs
            if job["status"] == status.value
        ]
    
    def get_jobs_by_company(self, company: str) -> List[Dict]:
        """Get all jobs from a specific company"""
        return [
            job for job in self.jobs
            if company.lower() in job["company"].lower()
        ]
    
    def search_jobs(self, query: str) -> List[Dict]:
        """Search jobs by title, company, or description"""
        query_lower = query.lower()
        results = []
        
        for job in self.jobs:
            if (query_lower in job.get("job_title", "").lower() or
                query_lower in job.get("company", "").lower() or
                query_lower in job.get("description", "").lower()):
                results.append(job)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked jobs"""
        # Defensive check to ensure jobs is a list
        if not isinstance(self.jobs, list):
            logger.warning(f"Jobs data is not a list (type: {type(self.jobs)}), converting...")
            if isinstance(self.jobs, dict):
                self.jobs = list(self.jobs.values())
            else:
                self.jobs = []
        
        stats = {
            "total_jobs": len(self.jobs),
            "by_status": {},
            "by_company": {},
            "by_job_board": {},
            "applied_count": 0
        }
        
        for job in self.jobs:
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
    
    def check_duplicate(self, company: str, job_title: str, job_url: str = "") -> Optional[int]:
        """
        Check if a job already exists by URL first, then by company + title
        
        Args:
            company: Company name
            job_title: Job title
            job_url: Job URL (primary deduplication method)
        
        Returns:
            Job index if duplicate found, None otherwise
        """
        # First check by URL (most reliable method)
        if job_url:
            for job_idx, job in enumerate(self.jobs):
                existing_url = job.get("job_url", "")
                if existing_url and existing_url.strip().lower() == job_url.strip().lower():
                    return job_idx
        
        # Fallback to company + title matching
        for job_idx, job in enumerate(self.jobs):
            if (job["company"].lower() == company.lower() and
                job["job_title"].lower() == job_title.lower()):
                return job_idx
        
        return None
    
    def get_all_jobs_data(self):
        """Get all jobs data with metadata for viewing/export"""
        return {
            "jobs": self.jobs,
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
        
        # Show proof summaries for applied jobs
        applied_jobs = self.get_jobs_by_status(JobStatus.APPLIED)
        if applied_jobs:
            logger.info("\n📋 Application Proof Summary:")
            for i, job in enumerate(applied_jobs):
                proof = job.get("additional_info", {}).get("application_proof", {})
                if proof:
                    company = job.get("company", "Unknown")
                    title = job.get("job_title", "Unknown")
                    timestamp = proof.get("application_timestamp", "Unknown")
                    proof_type = proof.get("proof_type", "Unknown")
                    screenshot = "✅" if proof.get("screenshot_taken") else "❌"
                    recording_url = proof.get("recording_url")
                    
                    logger.info(f"  • {company} - {title}")
                    logger.info(f"    Applied: {timestamp}")
                    logger.info(f"    Screenshot: {screenshot}")
                    logger.info(f"    Proof Type: {proof_type}")
                    if recording_url:
                        logger.info(f"    📹 Video Proof: {recording_url}")
        
        logger.separator()
