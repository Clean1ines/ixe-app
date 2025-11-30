from typing import Optional
"""
Value Object representing configuration parameters for the scraping process.

Updated to integrate with centralized configuration system.
"""
from dataclasses import dataclass
from enum import Enum


class ScrapingMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass(frozen=True)
class ScrapingConfig:
    """
    Value Object for scraping process configuration.
    Integrated with centralized configuration system.
    """
    mode: ScrapingMode = ScrapingMode.SEQUENTIAL
    # max_empty_pages might still be a fallback, but not primary stop condition
    max_empty_pages: int = 2  # Stop after N consecutive empty pages (fallback)
    start_page: str = "init"  # Page number to start scraping from
    max_pages: Optional[int] = None  # Max pages to scrape, None for unlimited (fallback if pager fails)
    force_restart: bool = False  # Delete existing data before scraping
    parallel_workers: int = 3  # Number of concurrent workers (if mode is PARALLEL)
    timeout_seconds: int = 30  # Timeout for browser operations
    retry_attempts: int = 3  # Number of retry attempts for failed requests
    retry_delay_seconds: int = 1  # Delay between retries
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # Default user agent

    def __post_init__(self):
        """Validate the configuration after initialization."""
        if self.max_empty_pages <= 0:
            raise ValueError("max_empty_pages must be positive")
        if self.parallel_workers <= 0:
            raise ValueError("parallel_workers must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        if self.max_pages is not None and self.max_pages <= 0:
            raise ValueError("max_pages must be positive if specified")

    @classmethod
    def from_central_config(cls) -> 'ScrapingConfig':
        """
        Create ScrapingConfig from centralized configuration.

        Supports graceful degradation if central config is not available.
        """
        try:
            from src.core.config import config, ScrapingMode as CoreScrapingMode

            # Handle both proper AppConfig and fallback config
            if hasattr(config, 'get_scraping_config_dict'):
                # Proper configuration loaded
                config_dict = config.get_scraping_config_dict()
            else:
                # Fallback configuration - use safe defaults
                config_dict = {
                    "mode": CoreScrapingMode.SEQUENTIAL,
                    "max_empty_pages": getattr(config.scraping, 'max_empty_pages', 2),
                    "start_page": "init",
                    "max_pages": getattr(config.scraping, 'max_pages', None),
                    "force_restart": getattr(config.scraping, 'force_restart', False),
                    "parallel_workers": getattr(config.scraping, 'parallel_workers', 3),
                    "timeout_seconds": getattr(config.browser, 'timeout_seconds', 30),
                    "retry_attempts": getattr(config.scraping, 'retry_attempts', 3),
                    "retry_delay_seconds": getattr(config.scraping, 'retry_delay_seconds', 1),
                    "user_agent": getattr(config.browser, 'user_agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
                }

            return cls(**config_dict)

        except ImportError as e:
            # Central config not available, fall back to defaults
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Central configuration not available: {e}. Using default ScrapingConfig.")
            return cls()
        except Exception as e:
            # Any other error, fall back to defaults
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error loading central configuration: {e}. Using default ScrapingConfig.")
            return cls()
