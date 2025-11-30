from typing import Optional
"""
Infrastructure adapter implementing IAssetDownloader using Playwright's APIRequestContext.

This adapter provides a concrete implementation for downloading assets
from the web using Playwright's request API, which is independent of a specific browser page.
It fulfills the contract defined by IAssetDownloader.
"""
import logging
from pathlib import Path
from playwright.async_api import async_playwright, APIRequestContext, Error as PlaywrightError

logger = logging.getLogger(__name__)


class PlaywrightAssetDownloaderAdapter:
    """
    Infrastructure adapter implementing IAssetDownloader using Playwright's APIRequestContext.

    This implementation uses Playwright's request API for downloading assets,
    providing independence from browser page instances for pure download operations.
    It manages its own Playwright context lifecycle.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the adapter.

        Args:
            timeout: Default timeout for download requests in seconds.
        """
        self.timeout_ms = timeout * 1000
        self._request_context: APIRequestContext | None = None
        self._playwright_ctx = None
        self._browser = None  # Store the browser instance
        self._initialized = False
        self.timeout = timeout  # FIX: Add the timeout attribute

    async def initialize(self):
        """Initialize the Playwright context and API request context."""
        if self._initialized:
            return

        logger.info("Initializing PlaywrightAssetDownloaderAdapter.")
        self._playwright_ctx = await async_playwright().start()
        # Launch a browser instance just to get the request context
        # We don't need a full browser/page for downloads, just the API context
        self._browser = await self._playwright_ctx.chromium.launch(headless=True)
        # FIX: Await the coroutine and then get the request context
        context = await self._browser.new_context()
        self._request_context = context.request
        self._initialized = True
        logger.info("PlaywrightAssetDownloaderAdapter initialized successfully.")

    async def close(self):
        """Close the Playwright context and API request context."""
        logger.info("Closing PlaywrightAssetDownloaderAdapter.")
        if self._request_context:
            try:
                await self._request_context.dispose()  # Dispose the request context
            except Exception as e:
                logger.error(f"Error disposing API request context: {e}")
            self._request_context = None

        # FIX: Access self._browser which is now correctly stored as an attribute
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.error(f"Error closing browser used for request context: {e}")
            self._browser = None

        if self._playwright_ctx:
            try:
                await self._playwright_ctx.stop()
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
            self._playwright_ctx = None

        self._initialized = False
        logger.info("PlaywrightAssetDownloaderAdapter closed successfully.")

    async def download(self, asset_url: str, destination_path: Path) -> bool:
        """
        Download an asset from the web and save it to a local destination.

        Args:
            asset_url: The full URL of the asset to download.
            destination_path: The local path where the asset should be saved.

        Returns:
            True if the download was successful, False otherwise.
        """
        if not self._initialized:
            await self.initialize()

        logger.debug(f"Downloading asset from {asset_url} to {destination_path}")
        try:
            response = await self._request_context.get(asset_url, timeout=self.timeout_ms)
            if response.ok:
                content = await response.body()
                destination_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directory exists
                with open(destination_path, 'wb') as f:
                    f.write(content)
                logger.debug(f"Successfully downloaded asset to {destination_path}")
                return True
            else:
                logger.warning(f"Failed to download asset from {asset_url}. Status: {response.status}")
                return False
        except PlaywrightError as e:
            if "certificate" in str(e).lower():
                # Suppress SSL certificate error logs by using debug level instead of warning
                logger.debug(f"SSL certificate error for {asset_url}, trying alternative method (aiohttp).")
                return await self._download_with_aiohttp(asset_url, destination_path)
            else:
                logger.error(f"Playwright error downloading asset {asset_url}: {e}", exc_info=True)
                return False
        except OSError as e:
            logger.error(f"OS error (e.g., disk full, permission denied) while saving to {destination_path} during download: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download from {asset_url} or saving to {destination_path}: {e}")
            return False

    async def download_bytes(self, asset_url: str) -> Optional[bytes]:
        """
        Download an asset from the web and return its content as bytes.

        Args:
            asset_url: The full URL of the asset to download.

        Returns:
            The content of the asset as bytes if successful, otherwise None.
        """
        if not self._initialized:
            await self.initialize()

        logger.debug(f"Downloading asset bytes from {asset_url}")
        try:
            response = await self._request_context.get(asset_url, timeout=self.timeout_ms)
            if response.ok:
                content_bytes = await response.body()
                logger.debug(f"Successfully downloaded bytes from {asset_url}, size: {len(content_bytes)}")
                return content_bytes
            else:
                logger.warning(f"Failed to download bytes from {asset_url}. Status: {response.status}")
                return None
        except PlaywrightError as e:
            if "certificate" in str(e).lower():
                # Suppress SSL certificate error logs by using debug level instead of warning
                logger.debug(f"SSL certificate error for bytes download {asset_url}, trying alternative method (aiohttp).")
                return await self._download_bytes_with_aiohttp(asset_url)
            else:
                logger.error(f"Playwright error downloading bytes from {asset_url}: {e}", exc_info=True)
                return None
        except Exception as e:
            logger.error(f"Unexpected error during bytes download from {asset_url}: {e}")
            return None

    # --- Alternative implementations using aiohttp for SSL issues ---
    async def _download_with_aiohttp(self, asset_url: str, destination_path: Path) -> bool:
        """Alternative download method using aiohttp in case of Playwright SSL issues."""
        try:
            import aiohttp
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(asset_url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:  # Используем self.timeout
                    if response.status == 200:
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                        content = await response.read()
                        with open(destination_path, 'wb') as f:
                            f.write(content)
                        logger.debug(f"Successfully downloaded asset using aiohttp: {asset_url}")
                        return True
                    else:
                        logger.warning(f"aiohttp failed to download asset from {asset_url}. Status: {response.status}")
                        return False
        except ImportError:
            logger.error("aiohttp not installed, cannot use alternative download method.")
            return False
        except Exception as e:
            logger.error(f"Error in alternative download method (aiohttp) for {asset_url}: {e}")
            return False

    async def _download_bytes_with_aiohttp(self, asset_url: str) -> Optional[bytes]:
        """Alternative bytes download method using aiohttp in case of Playwright SSL issues."""
        try:
            import aiohttp
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(asset_url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:  # Используем self.timeout
                    if response.status == 200:
                        content = await response.read()
                        logger.debug(f"Successfully downloaded bytes using aiohttp: {asset_url}")
                        return content
                    else:
                        logger.warning(f"aiohttp failed to download bytes from {asset_url}. Status: {response.status}")
                        return None
        except ImportError:
            logger.error("aiohttp not installed, cannot use alternative bytes download method.")
            return None
        except Exception as e:
            logger.error(f"Error in alternative bytes download method (aiohttp) for {asset_url}: {e}")
            return None
