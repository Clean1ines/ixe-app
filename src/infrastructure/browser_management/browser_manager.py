"""
Module for managing a single Playwright browser instance and a general-purpose page.
Used as a resource within a browser pool for the IBrowserService implementation.
"""
import logging
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Manages a single browser instance and a general-purpose page for fetching content.
    This class is intended to be managed by a pool mechanism (e.g., BrowserPoolServiceAdapter)
    to satisfy the IBrowserService contract.
    """

    def __init__(self, base_url: str = "https://ege.fipi.ru"):
        self.base_url = base_url.rstrip("/")
        self._browser: Browser | None = None
        self._page: Page | None = None  # Single general-purpose page per manager instance
        self._playwright_ctx = None
        self._initialized = False

    async def initialize(self):
        """Initialize the browser context and create a general-purpose page."""
        if self._initialized:
            return

        logger.info("Initializing BrowserManager and launching browser.")
        self._playwright_ctx = await async_playwright().start()
        self._browser = await self._playwright_ctx.chromium.launch(headless=True)

        # Create a single general-purpose page for this manager instance
        self._page = await self._browser.new_page()
        self._page.set_default_timeout(30000)  # 30 seconds
        self._initialized = True
        logger.info("BrowserManager initialized successfully.")

    async def close(self):
        """Close the managed page and the browser."""
        logger.info("Closing BrowserManager and its resources.")
        if self._page:
            try:
                await self._page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            self._page = None

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
        """Check if the browser and page are healthy."""
        if not self._browser or not self._page:
            return False

        try:
            # Check if page is still connected by trying to execute a simple script
            await self._page.evaluate("1")
            return True
        except Exception:
            return False

    async def get_page_content(self, url: str, timeout: int = 30) -> str:
        """
        Navigate to a URL and get the page's HTML content using the managed page.

        Args:
            url: The URL to navigate to.
            timeout: The maximum time to wait for the page to load, in seconds.

        Returns:
            The HTML content of the page as a string.
        """
        if not self._initialized or not self._page:
            raise RuntimeError("BrowserManager is not initialized or page is not available. Call initialize() first.")

        try:
            logger.debug(f"BrowserManager navigating to {url} with timeout {timeout}s")
            # Use the single managed page
            await self._page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = await self._page.content()
            logger.debug(f"Successfully fetched content from {url}")
            return content
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            # Optionally, mark this manager as unhealthy or recreate page
            # For now, just re-raise
            raise
