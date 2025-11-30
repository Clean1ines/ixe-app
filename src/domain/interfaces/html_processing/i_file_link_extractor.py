from typing import List, Tuple
"""Interface for file link extraction"""
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class IFileLinkExtractor(ABC):
    """Extracts file links from HTML content"""

    @abstractmethod
    def extract_file_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """
        Extract file links from BeautifulSoup object

        Args:
            soup: BeautifulSoup object of the HTML

        Returns:
            List of tuples (link_element, href)
        """
