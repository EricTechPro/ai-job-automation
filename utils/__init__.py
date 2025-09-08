"""
Utility modules for the AI Browser Automation job application system
"""

from .logger import (
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
    success,
    process,
    step,
    data,
    job_found,
    job_applied,
    separator
)

from .job_tracker import (
    JobTracker,
    JobStatus
)

__all__ = [
    # Logger exports
    'get_logger',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'success',
    'process',
    'step',
    'data',
    'job_found',
    'job_applied',
    'separator',
    # Job tracker exports
    'JobTracker',
    'JobStatus'
]