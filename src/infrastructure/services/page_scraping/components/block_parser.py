"""BlockParser implementation for HTML block parsing"""
import logging
from typing import List, Tuple
from bs4 import BeautifulSoup, Tag

from src.domain.interfaces.html_processing.i_block_parser import IBlockParser
from src.domain.html_processing.pure_html_transforms import extract_block_pairs

logger = logging.getLogger(__name__)


class BlockParser(IBlockParser):
    """Coordinates HTML block parsing with multiple strategies"""
    
    def __init__(self, primary_parser=None):
        self.primary_parser = primary_parser

    def parse_html_blocks(self, html_content: str) -> List[List[Tag]]:
        """
        Parse HTML content into grouped blocks
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        if not html_content:
            return []

        try:
            # Try primary parser first if available
            if self.primary_parser:
                return self.parse_with_primary_parser(html_content)
            else:
                return self.parse_with_fallback(html_content)
        except Exception as e:
            logger.error(f"BlockParser failed to parse HTML blocks: {e}")
            return []

    def parse_with_primary_parser(self, html_content: str) -> List[List[Tag]]:
        """
        Parse using primary parser strategy
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        return self.primary_parser.parse_blocks(html_content)

    def parse_with_fallback(self, html_content: str) -> List[List[Tag]]:
        """
        Parse using fallback strategy
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        block_pairs = extract_block_pairs(html_content)
        grouped_blocks = []
        
        for header_html, body_html in block_pairs:
            header_dom = BeautifulSoup(header_html or "", "html.parser").find()
            body_dom = BeautifulSoup(body_html or "", "html.parser").find() if body_html else None
            elements = [el for el in (header_dom, body_dom) if el is not None]
            grouped_blocks.append(elements)
            
        return grouped_blocks
