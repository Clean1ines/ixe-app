"""
Centralized configuration management for the application.
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"

class ScrapingMode(Enum):
    FULL = "full"
    UPDATE = "update"
    RANGE = "range"

@dataclass(frozen=True)
class ScrapingConfig:
    """Configuration for scraping operations"""
    mode: ScrapingMode = ScrapingMode.FULL
    max_pages: Optional[int] = None
    max_empty_pages: int = 3
    parallel_workers: int = 1
    timeout_seconds: int = 30
    force_restart: bool = False

    def __post_init__(self):
        """Validate the configuration after initialization."""
        if self.max_empty_pages <= 0:
            raise ValueError("max_empty_pages must be positive")
        if self.parallel_workers <= 0:
            raise ValueError("parallel_workers must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

class FeatureFlags:
    """Feature flags for gradual rollout of refactored components"""
    
    def __init__(self):
        self.enable_refactored_file_link_processor = False
    
    @property
    def use_refactored_file_link_processor(self):
        return getattr(self, 'enable_refactored_file_link_processor', False)

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", Environment.DEVELOPMENT.value)
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./fipi_data.db")
        self.assets_directory = os.getenv("ASSETS_DIRECTORY", "./assets")
        
        # Browser configuration
        self.browser = type('BrowserConfig', (), {
            'timeout_seconds': int(os.getenv("BROWSER_TIMEOUT", "30")),
            'headless': os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
        })()
        
        # Scraping configuration
        self.scraping = type('ScrapingConfig', (), {
            'base_url': os.getenv("SCRAPING_BASE_URL", "https://fipi.ru"),
            'max_concurrent_downloads': int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "6"))
        })()
        
        # Feature flags
        self.feature_flags = FeatureFlags()

# Global configuration instance
config = Config()
