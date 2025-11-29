"""Interface for content fetching operations"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from pathlib import Path


class IContentFetcher(ABC):
    """Fetches HTML content from URLs with browser management"""
    
    @abstractmethod
    async def fetch_page_content(self, url: str, timeout: int) -> Tuple[str, str]:
        """
        Fetch HTML content from URL
        
        Args:
            url: URL to fetch
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (html_content, final_url)
        """
        pass

    @abstractmethod 
    async def setup_browser(self):
        """Setup browser instance for content fetching"""
        pass

    @abstractmethod
    async def cleanup_browser(self):
        """Cleanup browser resources"""
        pass
