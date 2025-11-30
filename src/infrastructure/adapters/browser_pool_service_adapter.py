from typing import Deque
"""
Infrastructure adapter implementing IBrowserService using a pool of BrowserManager instances.

This adapter provides browser instances for scraping operations via a queue-based pool,
fulfilling the IBrowserService contract required by the domain layer.
"""
import asyncio
import logging
from collections import deque
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.infrastructure.browser_management.browser_manager import BrowserManager

logger = logging.getLogger(__name__)


class BrowserPoolServiceAdapter(IBrowserService):
    """
    Implements IBrowserService using a pool of BrowserManager instances managed via asyncio.Queue.
    This allows concurrent access to multiple browser instances for parallel scraping.
    """

    def __init__(self, pool_size: int = 3, base_url: str = "https://ege.fipi.ru"):
        """
        Initialize the browser pool service adapter.

        Args:
            pool_size: The number of BrowserManager instances to maintain in the pool.
            base_url: The base URL for FIPI site.
        """
        self.pool_size = pool_size
        self.base_url = base_url
        self._pool: asyncio.Queue[BrowserManager] = asyncio.Queue()
        self._all_managers: Deque[BrowserManager] = deque()  # Keep references for closing
        self._initialized = False

    async def initialize(self):
        """Initialize the browser pool by creating and initializing BrowserManager instances."""
        if self._initialized:
            return

        logger.info(f"Initializing BrowserPoolServiceAdapter with pool size {self.pool_size}.")
        for i in range(self.pool_size):
            manager = BrowserManager(base_url=self.base_url)
            await manager.initialize()  # Initialize each manager
            await self._pool.put(manager)
            self._all_managers.append(manager)

        self._initialized = True
        logger.info("BrowserPoolServiceAdapter initialized successfully.")

    async def get_browser(self) -> BrowserManager:
        """
        Get a BrowserManager instance from the pool.
        This method waits if no browser is available.
        The returned BrowserManager can be used to call get_page_content directly.

        Returns:
            A BrowserManager instance from the pool.
        """
        if not self._initialized:
            await self.initialize()

        logger.debug("Waiting for available browser from pool.")
        manager = await self._pool.get()  # This waits if queue is empty
        logger.debug(f"BrowserManager retrieved from pool. Pool size now: {self._pool.qsize()}")
        return manager

    async def release_browser(self, browser_manager: BrowserManager) -> None:
        """
        Release a BrowserManager instance back to the pool.

        Args:
            browser_manager: The BrowserManager instance to release.
        """
        if not self._initialized:
            logger.warning("Tried to release browser, but pool is not initialized.")
            return

        logger.debug(f"Releasing BrowserManager back to pool. Pool size before: {self._pool.qsize()}")
        await self._pool.put(browser_manager)  # Put it back in the queue
        logger.debug(f"BrowserManager released to pool. Pool size now: {self._pool.qsize()}")

    async def close(self):
        """Close all BrowserManager instances in the pool."""
        if not self._initialized:
            return

        logger.info("Closing all BrowserManager instances in the pool.")
        while not self._pool.empty():
            try:
                manager = self._pool.get_nowait()
                await manager.close()
            except asyncio.QueueEmpty:
                break

        # Also close any managers we kept references to (should be the same ones)
        for manager in self._all_managers:
            await manager.close()
        self._all_managers.clear()

        self._initialized = False
        logger.info("All BrowserManager instances in the pool closed.")

    async def get_page_content(self, url: str, timeout: int = 30) -> str:
        """
        Convenience method to get page content using a browser from the pool.
        This method gets a browser, uses it, and releases it back automatically.

        Args:
            url: The URL to navigate to.
            timeout: The maximum time to wait for the page to load, in seconds.

        Returns:
            The HTML content of the page as a string.
        """
        if not self._initialized:
            await self.initialize()

        manager = await self.get_browser()
        try:
            content = await manager.get_page_content(url, timeout)
            return content
        finally:
            await self.release_browser(manager)  # Ensure browser is returned to pool even if an error occurs
