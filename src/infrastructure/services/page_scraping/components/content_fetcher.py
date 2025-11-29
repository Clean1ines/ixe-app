"""ContentFetcher implementation for page content fetching"""
import logging
from typing import Tuple

from src.domain.interfaces.scraping.i_content_fetcher import IContentFetcher

logger = logging.getLogger(__name__)


class ContentFetcher(IContentFetcher):
    """Fetches HTML content from URLs with browser management"""
    
    def __init__(self, browser_service):
        self.browser_service = browser_service
        self._browser_manager = None
        self._page = None

    async def setup_browser(self):
        """Setup browser instance for content fetching"""
        self._browser_manager = await self.browser_service.get_browser()
        return self._browser_manager

    async def fetch_page_content(self, url: str, timeout: int) -> Tuple[str, str]:
        """
        Fetch HTML content from URL
        
        Args:
            url: URL to fetch
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (html_content, final_url)
        """
        if not self._browser_manager:
            await self.setup_browser()

        try:
            # Create new page and configure it
            self._page = await self._browser_manager._browser.new_page()
            await self._page.set_viewport_size({
                "width": self._browser_manager.default_viewport_width,
                "height": self._browser_manager.default_viewport_height
            })
            await self._page.set_extra_http_headers({
                "User-Agent": self._browser_manager.default_user_agent
            })
            self._page.set_default_timeout(timeout * 1000)

            # Navigate to URL and get content
            logger.debug(f"ContentFetcher navigating to {url} with timeout {timeout}s")
            await self._page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            
            content = await self._page.content()
            final_url = url
            
            return content, final_url
            
        except Exception as e:
            logger.error(f"ContentFetcher failed to fetch {url}: {e}")
            await self.cleanup_browser()
            raise

    async def cleanup_browser(self):
        """Cleanup browser resources"""
        if self._page:
            await self._page.close()
            self._page = None
        if self._browser_manager:
            await self.browser_service.release_browser(self._browser_manager)
            self._browser_manager = None

    async def get_page(self):
        """Get the current page instance for additional operations"""
        return self._page
