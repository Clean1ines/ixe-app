from typing import Optional, Tuple
"""IframeHandler implementation for page scraping"""
import logging
import urllib.parse
from bs4 import BeautifulSoup

from src.domain.interfaces.scraping.i_iframe_handler import IIframeHandler

logger = logging.getLogger(__name__)


class IframeHandler(IIframeHandler):
    """Handles iframe content extraction and processing"""

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
        actual_page_content = main_content
        actual_source_url = url

        page_soup = BeautifulSoup(main_content, "html.parser")
        questions_iframe = self.find_questions_iframe(page_soup)

        if not questions_iframe:
            logger.debug(f"No questions iframe found on {url}.")
            return actual_page_content, actual_source_url

        iframe_src = questions_iframe.get('src')
        if not iframe_src:
            logger.warning(f"Iframe found on {url} without 'src'; using main page content.")
            return actual_page_content, actual_source_url

        full_iframe_url = urllib.parse.urljoin(url, iframe_src)
        actual_source_url = full_iframe_url

        try:
            await page.goto(full_iframe_url, wait_until="networkidle", timeout=timeout * 1000)
            actual_page_content = await page.content()
            logger.debug(f"Fetched iframe content ({len(actual_page_content)} chars) from {full_iframe_url}")
        except Exception as e_iframe:
            logger.error(f"Failed to get iframe content {full_iframe_url}: {e_iframe}", exc_info=True)
            logger.warning("Falling back to main page content.")
            # В случае ошибки используем исходный контент, не пытаясь вернуться
            # Это исправляет проблему с двойным исключением в тестах
            actual_page_content = main_content
            actual_source_url = url

        return actual_page_content, actual_source_url

    def find_questions_iframe(self, soup: BeautifulSoup) -> Optional[any]:
        """
        Find questions iframe in HTML content

        Args:
            soup: BeautifulSoup object

        Returns:
            Iframe element if found, None otherwise
        """
        return soup.find('iframe', id='questions_container')
