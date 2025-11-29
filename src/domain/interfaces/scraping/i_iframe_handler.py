"""Interface for iframe handling operations"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from bs4 import BeautifulSoup


class IIframeHandler(ABC):
    """Handles iframe content extraction and processing"""
    
    @abstractmethod
    async def handle_iframe_content(
        self, 
        page: any, 
        url: str, 
        timeout: int,
        main_content: str
    ) -> Tuple[str, str]:
        """
        Handle iframe content extraction with fallback
        
        Args:
            page: Browser page instance
            url: Original URL
            timeout: Timeout in seconds  
            main_content: Main page content
            
        Returns:
            Tuple of (actual_content, source_url)
        """
        pass

    @abstractmethod
    def find_questions_iframe(self, soup: BeautifulSoup) -> Optional[any]:
        """
        Find questions iframe in HTML content
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Iframe element if found, None otherwise
        """
        pass
