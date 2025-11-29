"""Interface for HTML block parsing operations"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from bs4 import Tag


class IBlockParser(ABC):
    """Coordinates HTML block parsing with multiple strategies"""
    
    @abstractmethod
    def parse_html_blocks(self, html_content: str) -> List[List[Tag]]:
        """
        Parse HTML content into grouped blocks
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        pass

    @abstractmethod
    def parse_with_primary_parser(self, html_content: str) -> List[List[Tag]]:
        """
        Parse using primary parser strategy
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        pass

    @abstractmethod
    def parse_with_fallback(self, html_content: str) -> List[List[Tag]]:
        """
        Parse using fallback strategy
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of grouped block elements
        """
        pass
