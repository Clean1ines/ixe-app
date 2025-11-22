"""
Value Object representing configuration parameters for the scraping process.
"""
from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Tuple
from enum import Enum

class ScrapingMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

@dataclass(frozen=True)
class ScrapingConfig:
    """
    Value Object for scraping process configuration.
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
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" # Default user agent

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
