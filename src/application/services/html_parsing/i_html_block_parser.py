"""
Application interface for parsing HTML blocks on a FIPI page.

This interface defines the contract for parsing the raw HTML content of a page
and extracting pairs of header_container and qblock elements that belong together.
It allows the application layer to remain independent of the specific parsing implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from bs4 import BeautifulSoup, Tag

class IHTMLBlockParser(ABC):
    """
    Interface for parsing HTML blocks.
    """

    @abstractmethod
    def parse_blocks(self, page_content: str) -> List[Tuple[Tag, Tag]]:
        """
        Parses the page content and returns a list of (header_container, qblock) pairs.

        Args:
            page_content: The raw HTML string of the page.

        Returns:
            A list of tuples, where each tuple contains a header_container Tag
            and its corresponding qblock Tag.
        """
        pass
