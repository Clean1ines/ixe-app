from typing import Any, Dict, Optional
"""
Centralized configuration management system with environment support.

Features:
- Environment-based configuration (dev/staging/prod)
- .env file support for local development
- Configuration validation on startup
- Graceful degradation for missing configuration
- Integration with existing ScrapingConfig
"""

import os
import logging
from enum import Enum
from pydantic import BaseSettings, validator, Field
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environments."""
    DEV = "dev"
    STAGING = "staging" 
    PROD = "prod"


class ScrapingMode(str, Enum):
    """Scraping operation modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    url: str = Field(default="sqlite:///./ege_problems.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")

    @validator("url")
    def validate_database_url(cls, v):
        """Validate database URL."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class BrowserConfig(BaseSettings):
    """Browser configuration."""
    timeout_seconds: int = Field(default=30, env="BROWSER_TIMEOUT")
    headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="BROWSER_USER_AGENT"
    )
    viewport_width: int = Field(default=1920, env="BROWSER_VIEWPORT_WIDTH")
    viewport_height: int = Field(default=1080, env="BROWSER_VIEWPORT_HEIGHT")
    base_url: str = Field(default="https://ege.fipi.ru", env="BROWSER_BASE_URL")

    @validator("timeout_seconds")
    def validate_timeout(cls, v):
        """Validate browser timeout."""
        if v <= 0:
            raise ValueError("Browser timeout must be positive")
        return v

    @validator("base_url")
    def validate_base_url(cls, v):
        """Validate base URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ScrapingConfig(BaseSettings):
    """Scraping process configuration."""
    base_url: str = Field(default="https://fipi.ru", env="SCRAPING_BASE_URL")
    mode: ScrapingMode = Field(default=ScrapingMode.SEQUENTIAL, env="SCRAPING_MODE")
    max_empty_pages: int = Field(default=2, env="SCRAPING_MAX_EMPTY_PAGES")
    max_pages: Optional[int] = Field(default=None, env="SCRAPING_MAX_PAGES")
    force_restart: bool = Field(default=False, env="SCRAPING_FORCE_RESTART")
    parallel_workers: int = Field(default=3, env="SCRAPING_PARALLEL_WORKERS")
    retry_attempts: int = Field(default=3, env="SCRAPING_RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=1, env="SCRAPING_RETRY_DELAY")
    asset_download_timeout: int = Field(default=60, env="ASSET_DOWNLOAD_TIMEOUT")

    @validator("base_url")
    def validate_base_url(cls, v):
        """Validate scraping base URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Scraping base URL must start with http:// or https://")
        return v

    @validator("parallel_workers", "retry_attempts", "max_empty_pages")
    def validate_positive_numbers(cls, v):
        """Validate positive integer fields."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @validator("retry_delay_seconds")
    def validate_non_negative(cls, v):
        """Validate non-negative fields."""
        if v < 0:
            raise ValueError("Value cannot be negative")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AppConfig(BaseSettings):
    """Main application configuration."""
    environment: Environment = Field(default=Environment.DEV, env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    assets_directory: str = Field(default="./assets", env="ASSETS_DIRECTORY")
    max_concurrent_downloads: int = Field(default=5, env="MAX_CONCURRENT_DOWNLOADS")

    # Graceful degradation defaults
    enable_graceful_degradation: bool = Field(default=True, env="ENABLE_GRACEFUL_DEGRADATION")
    default_timeout: int = Field(default=30, env="DEFAULT_TIMEOUT")
    default_retries: int = Field(default=2, env="DEFAULT_RETRIES")

    database: DatabaseConfig = DatabaseConfig()
    browser: BrowserConfig = BrowserConfig()
    scraping: ScrapingConfig = ScrapingConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize configuration with validation."""
        super().__init__(**kwargs)
        self.validate_config()

    def validate_config(self):
        """Validate entire configuration after initialization."""
        errors = []

        # Environment-specific validations
        if self.environment == Environment.PROD:
            if not self.scraping.base_url.startswith("https://"):
                errors.append("Production environment requires HTTPS for scraping")
            if not self.browser.base_url.startswith("https://"):
                errors.append("Production environment requires HTTPS for browser")
            if self.browser.headless is False:
                errors.append("Production environment should run browser in headless mode")

        # Directory validations
        if self.assets_directory:
            try:
                os.makedirs(self.assets_directory, exist_ok=True)
                # Test if directory is writable
                test_file = os.path.join(self.assets_directory, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                errors.append(f"Cannot write to assets directory '{self.assets_directory}': {e}")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_scraping_config_dict(self) -> Dict[str, Any]:
        """Convert to dictionary compatible with existing ScrapingConfig."""
        return {
            "mode": self.scraping.mode,
            "max_empty_pages": self.scraping.max_empty_pages,
            "start_page": "init",
            "max_pages": self.scraping.max_pages,
            "force_restart": self.scraping.force_restart,
            "parallel_workers": self.scraping.parallel_workers,
            "timeout_seconds": self.browser.timeout_seconds,
            "retry_attempts": self.scraping.retry_attempts,
            "retry_delay_seconds": self.scraping.retry_delay_seconds,
            "user_agent": self.browser.user_agent,
        }


# Global configuration instance with graceful degradation
try:
    config = AppConfig()
    logger.info(f"Configuration loaded successfully for {config.environment} environment")
except Exception as e:
    logger.warning(f"Configuration loading failed: {e}")
    logger.info("Falling back to default configuration with graceful degradation...")

    # Graceful degradation - create minimal config with safe defaults
    class FallbackConfig:
        environment = Environment.DEV
        enable_graceful_degradation = True
        log_level = "INFO"
        assets_directory = "./assets"
        scraping = type('Scraping', (), {
            'base_url': 'https://fipi.ru',
            'mode': ScrapingMode.SEQUENTIAL,
            'max_empty_pages': 2,
            'max_pages': None,
            'force_restart': False,
            'parallel_workers': 3,
            'retry_attempts': 3,
            'retry_delay_seconds': 1,
            'asset_download_timeout': 60
        })()
        browser = type('Browser', (), {
            'timeout_seconds': 30,
            'headless': True,
            'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            'base_url': 'https://ege.fipi.ru',
            'viewport_width': 1920,
            'viewport_height': 1080
        })()
        database = type('Database', (), {
            'url': 'sqlite:///./ege_problems.db',
            'echo': False,
            'pool_size': 20,
            'max_overflow': 30
        })()

    config = FallbackConfig()
