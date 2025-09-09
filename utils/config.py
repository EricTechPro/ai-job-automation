"""
Environment-based configuration management
Centralizes all configuration values from environment variables
"""

import os
from typing import Dict, Any, Union
from utils.logger import get_logger

logger = get_logger("Config")

class Config:
    """Central configuration manager using environment variables"""
    
    @staticmethod
    def get_int(key: str, default: int) -> int:
        """Get integer value from environment with default"""
        try:
            value = os.getenv(key)
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid value for {key}, using default: {default}")
            return default
    
    @staticmethod
    def get_bool(key: str, default: bool) -> bool:
        """Get boolean value from environment with default"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_str(key: str, default: str) -> str:
        """Get string value from environment with default"""
        return os.getenv(key, default)
    
    # Job Search Limits
    @property
    def MAX_JOBS_TO_FIND(self) -> int:
        return self.get_int("MAX_JOBS_TO_FIND", 50)
    
    @property  
    def MAX_JOBS_PER_PLATFORM(self) -> int:
        return self.get_int("MAX_JOBS_PER_PLATFORM", 10)
    
    @property
    def MAX_CONCURRENT_BROWSERS(self) -> int:
        return self.get_int("MAX_CONCURRENT_BROWSERS", 5)
    
    @property
    def MAX_APPLICATIONS_PER_RUN(self) -> int:
        return self.get_int("MAX_APPLICATIONS_PER_RUN", 10)
    
    @property
    def MAX_APPLICATIONS_PER_PLATFORM(self) -> int:
        return self.get_int("MAX_APPLICATIONS_PER_PLATFORM", 3)
    
    # Browser Automation Settings
    @property
    def SEARCH_MAX_STEPS(self) -> int:
        return self.get_int("SEARCH_MAX_STEPS", 30)
    
    @property
    def APPLICATION_MAX_STEPS(self) -> int:
        return self.get_int("APPLICATION_MAX_STEPS", 40)
    
    @property
    def TEST_MAX_STEPS(self) -> int:
        return self.get_int("TEST_MAX_STEPS", 10)
    
    # Timing Controls
    @property
    def APPLICATION_DELAY_SECONDS(self) -> int:
        return self.get_int("APPLICATION_DELAY_SECONDS", 30)
    
    @property
    def RATE_LIMIT_DELAY_MIN(self) -> int:
        return self.get_int("RATE_LIMIT_DELAY_MIN", 1)
    
    @property  
    def RATE_LIMIT_DELAY_MAX(self) -> int:
        return self.get_int("RATE_LIMIT_DELAY_MAX", 3)
    
    @property
    def SESSION_TIMEOUT_SECONDS(self) -> int:
        return self.get_int("SESSION_TIMEOUT_SECONDS", 1200)
    
    # Quality Controls
    @property
    def DUPLICATE_DETECTION_ENABLED(self) -> bool:
        return self.get_bool("DUPLICATE_DETECTION_ENABLED", True)
    
    @property
    def ENABLE_SCREENSHOTS(self) -> bool:
        return self.get_bool("ENABLE_SCREENSHOTS", True)
    
    @property
    def ENABLE_SESSION_RECORDINGS(self) -> bool:
        return self.get_bool("ENABLE_SESSION_RECORDINGS", True)
    
    # Job Generation Controls
    @property
    def JOBS_PER_SEARCH_MIN(self) -> int:
        return self.get_int("JOBS_PER_SEARCH_MIN", 1)
    
    @property
    def JOBS_PER_SEARCH_MAX(self) -> int:
        return self.get_int("JOBS_PER_SEARCH_MAX", 3)
    
    def get_rate_limit_delay_range(self) -> str:
        """Get rate limit delay as range string"""
        return f"{self.RATE_LIMIT_DELAY_MIN}-{self.RATE_LIMIT_DELAY_MAX}"

# Global config instance
config = Config()