"""
Module for managing a single Playwright browser instance.
Creates a new page for each get_page_content request and closes it afterwards.
This allows one browser instance to handle multiple requests concurrently.

Updated to use centralized configuration for timeouts and browser settings.
"""
import logging
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Manages a single browser instance.
    Creates a new page for each get_page_content request and closes it afterwards.
    This allows one browser instance to handle multiple requests concurrently.
    This class is intended to be managed by a pool mechanism (e.g., BrowserPoolServiceAdapter)
    to satisfy the IBrowserService contract.

    Updated to use centralized configuration.
    """

    def __init__(self, base_url: str = None):
        """Initialize with centralized configuration support."""
        # Use provided base_url or get from centralized config
        if base_url is None:
            try:
                from src.core.config import config
                self.base_url = getattr(config.browser, 'base_url', 'https://ege.fipi.ru')
                self.default_headless = getattr(config.browser, 'headless', True)
                self.default_user_agent = getattr(config.browser, 'user_agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                self.default_viewport_width = getattr(config.browser, 'viewport_width', 1920)
                self.default_viewport_height = getattr(config.browser, 'viewport_height', 1080)
            except ImportError:
                # Fallback to hardcoded values if config is not available
                self.base_url = 'https://ege.fipi.ru'
                self.default_headless = True
                self.default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                self.default_viewport_width = 1920
                self.default_viewport_height = 1080
        else:
            self.base_url = base_url.rstrip("/")
            # Still try to get other settings from config
            try:
                from src.core.config import config
                self.default_headless = getattr(config.browser, 'headless', True)
                self.default_user_agent = getattr(config.browser, 'user_agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                self.default_viewport_width = getattr(config.browser, 'viewport_width', 1920)
                self.default_viewport_height = getattr(config.browser, 'viewport_height', 1080)
            except ImportError:
                self.default_headless = True
                self.default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                self.default_viewport_width = 1920
                self.default_viewport_height = 1080

        self._browser: Browser | None = None
        self._playwright_ctx = None
        self._initialized = False

    async def initialize(self):
        """Initialize the browser context with centralized configuration."""
        if self._initialized:
            return

        logger.info("Initializing BrowserManager and launching browser.")
        self._playwright_ctx = await async_playwright().start()
        self._browser = await self._playwright_ctx.chromium.launch(headless=self.default_headless)
        self._initialized = True
        logger.info("BrowserManager initialized successfully.")

    async def close(self):
        """Close the browser and playwright context."""
        logger.info("Closing BrowserManager and its resources.")
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            self._browser = None

        if self._playwright_ctx:
            try:
                await self._playwright_ctx.stop()
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
            self._playwright_ctx = None

        self._initialized = False
        logger.info("BrowserManager closed successfully.")

    async def is_healthy(self) -> bool:
        """Check if the browser resource is healthy."""
        if not self._browser:
            return False

        try:
            # Check if browser is still connected by trying to create a page
            test_page = await self._browser.new_page()
            await test_page.close()
            return True
        except Exception:
            return False

    async def get_page_content(self, url: str, timeout: int = None) -> str:
        """
        Navigate to a URL on a *new* page, get the HTML content, and close the page.

        Args:
            url: The URL to navigate to.
            timeout: The maximum time to wait for the page to load, in seconds.
                    Uses centralized configuration if not provided.

        Returns:
            The HTML content of the page as a string.
        """
        if not self._initialized or not self._browser:
            raise RuntimeError("BrowserManager is not initialized or browser is not available. Call initialize() first.")

        # Use provided timeout or get from centralized config
        if timeout is None:
            try:
                from src.core.config import config
                timeout = getattr(config.browser, 'timeout_seconds', 30)
            except ImportError:
                timeout = 30  # Fallback to hardcoded default

        page = None
        try:
            logger.debug(f"BrowserManager creating new page for {url} with timeout {timeout}s")
            page = await self._browser.new_page()
            
            # Set viewport and user agent from centralized configuration
            await page.set_viewport_size({
                "width": self.default_viewport_width,
                "height": self.default_viewport_height
            })
            await page.set_extra_http_headers({
                "User-Agent": self.default_user_agent
            })
            
            page.set_default_timeout(timeout * 1000)  # Convert timeout to milliseconds

            logger.debug(f"BrowserManager navigating page to {url}")
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = await page.content()
            logger.debug(f"Successfully fetched content from {url}")
            return content
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            # Re-raise to allow caller (e.g., BrowserPoolServiceAdapter) to handle
            raise
        finally:
            # Ensure the page is closed even if an error occurred during navigation/content retrieval
            if page:
                try:
                    await page.close()
                    logger.debug(f"Page for {url} closed.")
                except Exception as e:
                    logger.warning(f"Error closing page for {url}: {e}")
