"""
Core module for centralized configuration management.
"""

from src.core.config import config, Environment, ScrapingMode
from src.core.startup import validate_configuration_on_startup

__all__ = ['config', 'Environment', 'ScrapingMode', 'validate_configuration_on_startup']
