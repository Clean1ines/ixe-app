"""
Domain interface for scraping progress service.
"""
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.value_objects.scraping.subject_info import SubjectInfo


class IProgressService(ABC):
    """Interface for determining scraping progress and next page."""
    
    @abstractmethod
    async def get_next_page_to_scrape(
        self, 
        subject_info: SubjectInfo, 
        start_page: str,
        force_restart: bool
    ) -> int:
        """
        Get the next page number to scrape based on progress.
        
        Args:
            subject_info: Information about the subject
            start_page: The starting page configuration ("init" or number string)
            force_restart: Whether to ignore previous progress
            
        Returns:
            Next page number to scrape
        """
        pass
