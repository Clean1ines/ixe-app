"""
Fake implementation of IHTMLBlockParser for testing.

This is a working implementation that returns predefined block groups
rather than parsing real HTML. It's designed for tests where we need
to verify behavior without dealing with actual HTML parsing complexity.
"""
from typing import List
from bs4 import BeautifulSoup, Tag
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser

class FakeHTMLBlockParser(IHTMLBlockParser):
    """
    Fake implementation of IHTMLBlockParser for testing.
    
    This class returns predefined block groups without actually parsing HTML.
    It's useful for isolating tests from the complexities of real HTML parsing.
    """
    
    def __init__(self, predefined_blocks=None):
        """
        Initialize the fake parser with predefined block groups.
        
        Args:
            predefined_blocks: List of block groups to return, where each block group
                              is a list of BeautifulSoup Tag objects
        """
        self._blocks = predefined_blocks or []
    
    def parse_blocks(self, page_content: str) -> List[List[Tag]]:
        """
        Return predefined block groups without actual parsing.
        
        This method completely ignores the page_content parameter and returns
        the predefined blocks that were set up during initialization.
        
        Args:
            page_content: HTML content (ignored in this fake implementation)
            
        Returns:
            List of block groups, where each block group contains related HTML elements
        """
        return self._blocks
