from typing import Any
"""
Domain interface for Browser service operations.

This interface defines the contract for interacting with a web browser,
allowing the domain layer to remain independent of the specific browser
automation implementation (e.g., Playwright, Selenium).
"""
from abc import abstractmethod


class IBrowserService:
    """
    Interface for operations related to browser management and interaction.
    """

    @abstractmethod
    async def get_browser(self) -> Any:
        """
        Get a browser instance.

        Returns:
            A browser instance from the pool or a new one.
            The concrete type depends on the infrastructure implementation (e.g., playwright.async_api.Browser).
        """
        raise NotImplementedError

    @abstractmethod
    async def release_browser(self, browser: Any) -> None:
        """
        Release a browser instance back to the pool.

        Args:
            browser: The browser instance to release.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close all managed browser resources.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_page_content(self, url: str, timeout: int = 30) -> str:
        """
        Navigate to a URL and get the page's HTML content.

        Args:
            url: The URL to navigate to.
            timeout: The maximum time to wait for the page to load, in seconds.

        Returns:
            The HTML content of the page as a string.
        """
        raise NotImplementedError
