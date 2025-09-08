"""
Custom logging module with colored output for different log levels
"""

import logging
import sys
from typing import Optional
from datetime import datetime

# Import colorama for cross-platform color support
try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)  # Auto-reset colors after each print
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Log level colors
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta
    
    # Additional colors for specific log types
    SUCCESS = '\033[92m'    # Bright Green
    PROCESS = '\033[94m'    # Bright Blue
    DATA = '\033[96m'       # Bright Cyan
    STEP = '\033[95m'       # Bright Magenta


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages"""
    
    # Color mapping for different log levels
    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
        logging.CRITICAL: Colors.CRITICAL,
    }
    
    # Icons for different log levels
    LEVEL_ICONS = {
        logging.DEBUG: '🔍',
        logging.INFO: 'ℹ️ ',
        logging.WARNING: '⚠️ ',
        logging.ERROR: '❌',
        logging.CRITICAL: '🚨',
    }
    
    def __init__(self, use_colors: bool = True, include_icons: bool = True):
        """
        Initialize the colored formatter
        
        Args:
            use_colors: Whether to use colors in output
            include_icons: Whether to include emoji icons
        """
        self.use_colors = use_colors
        self.include_icons = include_icons
        
        # Define the log format
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        super().__init__(log_format, datefmt=date_format)
    
    def format(self, record):
        """Format the log record with colors and icons"""
        # Get the original formatted message
        formatted = super().format(record)
        
        if not self.use_colors:
            return formatted
        
        # Get color for this log level
        color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        
        # Get icon for this log level
        icon = self.LEVEL_ICONS.get(record.levelno, '') if self.include_icons else ''
        
        # Apply color and icon
        if icon:
            formatted = f"{color}{icon} {formatted}{Colors.RESET}"
        else:
            formatted = f"{color}{formatted}{Colors.RESET}"
        
        return formatted


class JobBotLogger:
    """Custom logger for the Job Bot application with specialized log methods"""
    
    def __init__(self, name: str = "JobBot", level: int = logging.INFO, 
                 log_to_file: bool = True, log_file: str = "job_bot.log"):
        """
        Initialize the JobBot logger
        
        Args:
            name: Logger name
            level: Logging level
            log_to_file: Whether to also log to a file
            log_file: Path to the log file
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(use_colors=True, include_icons=True))
        self.logger.addHandler(console_handler)
        
        # File handler without colors
        if log_to_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def success(self, message: str):
        """Log success message with special formatting"""
        formatted_message = f"{Colors.SUCCESS}✅ {message}{Colors.RESET}"
        self.logger.info(formatted_message)
    
    def process(self, message: str):
        """Log process/workflow message"""
        formatted_message = f"{Colors.PROCESS}🔄 {message}{Colors.RESET}"
        self.logger.info(formatted_message)
    
    def step(self, step_number: int, total_steps: int, message: str):
        """Log a step in a multi-step process"""
        formatted_message = f"{Colors.STEP}[Step {step_number}/{total_steps}] {message}{Colors.RESET}"
        self.logger.info(formatted_message)
    
    def data(self, message: str, data: Optional[dict] = None):
        """Log data-related message"""
        formatted_message = f"{Colors.DATA}📊 {message}{Colors.RESET}"
        if data:
            formatted_message += f"\n{Colors.DATA}{data}{Colors.RESET}"
        self.logger.info(formatted_message)
    
    def job_found(self, job_title: str, company: str, location: str = ""):
        """Log when a new job is found"""
        location_str = f" - {location}" if location else ""
        message = f"🎯 Found Job: {job_title} at {company}{location_str}"
        self.success(message)
    
    def job_applied(self, job_title: str, company: str):
        """Log when a job application is submitted"""
        message = f"📨 Applied to: {job_title} at {company}"
        self.success(message)
    
    def separator(self, char: str = "=", length: int = 60):
        """Log a separator line"""
        self.logger.info(char * length)


# Create a singleton logger instance
logger = JobBotLogger()

# Convenience functions for quick access
def get_logger(name: Optional[str] = None) -> JobBotLogger:
    """Get a logger instance"""
    if name:
        return JobBotLogger(name)
    return logger


# Export commonly used functions
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
success = logger.success
process = logger.process
step = logger.step
data = logger.data
job_found = logger.job_found
job_applied = logger.job_applied
separator = logger.separator