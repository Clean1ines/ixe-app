"""
Startup configuration validation and initialization.
"""
import logging
import os
from pathlib import Path

try:
    from src.core.config import config, CENTRAL_CONFIG_AVAILABLE
except ImportError:
    CENTRAL_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

def validate_configuration_on_startup():
    """Validate configuration when application starts."""
    logger.info("Validating application configuration...")
    
    if not CENTRAL_CONFIG_AVAILABLE:
        logger.warning("Central configuration system not available. Using fallback configuration.")
        return
    
    # Log configuration summary
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Scraping base URL: {config.scraping.base_url}")
    logger.info(f"Browser timeout: {config.browser.timeout_seconds}s")
    logger.info(f"Retry attempts: {config.scraping.retry_attempts}")
    logger.info(f"Assets directory: {config.assets_directory}")
    
    # Validate critical directories
    critical_dirs = [
        config.assets_directory,
        os.path.dirname(config.database.url.replace('sqlite:///', '')) if config.database.url.startswith('sqlite:') else None
    ]
    
    for dir_path in critical_dirs:
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Could not create directory {dir_path}: {e}")
    
    logger.info("Configuration validation completed successfully.")

# Run validation on import
validate_configuration_on_startup()
