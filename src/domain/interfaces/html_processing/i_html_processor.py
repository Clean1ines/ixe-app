"""
Domain interface for HTML processing operations.
This interface defines the contract for processing a single HTML block pair
representing a problem, allowing the domain layer to remain independent of the
specific HTML parsing and extraction implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4.element import Tag


class IHTMLProcessor(ABC):
    """Domain interface for HTML processing operations."""
    
    @abstractmethod
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing structured data extracted from the block.
        """
        pass
