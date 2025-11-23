"""Structured logging utilities"""

import logging
import json
from typing import Dict, Any
from datetime import datetime


class StructuredLogger:
    """
    Structured logger that outputs JSON logs.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create handler
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """Log a structured message"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **kwargs,
        }
        
        self.logger.log(level, json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_structured(logging.DEBUG, message, **kwargs)


def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """Get or create a structured logger"""
    return StructuredLogger(name, level)
