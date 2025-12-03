"""
Logging configuration for the application
"""

import logging
import sys
from app.config.settings import settings


def configure_logging():
    """Configure application logging"""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set levels for third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)