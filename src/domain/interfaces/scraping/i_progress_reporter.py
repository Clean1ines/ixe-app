"""
Domain interface for scraping progress reporter.
"""
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.scraping_result import ScrapingResult


class IProgressReporter(ABC):
    """Interface for reporting scraping progress."""
    
    @abstractmethod
    def report_start(
        self, 
        subject_info: SubjectInfo, 
        start_page: str,
        max_pages: Optional[int],
        force_restart: bool
    ) -> None:
        """Report scraping start."""
        pass
    
    @abstractmethod
    def report_page_progress(
        self,
        page: int,
        total_pages: Optional[int],
        problems_found: int,
        problems_saved: int,
        assets_downloaded: int,
        duration_seconds: float
    ) -> None:
        """Report page scraping progress."""
        pass
        
    @abstractmethod
    def report_page_error(self, page: int, error: str) -> None:
        """Report page scraping error."""
        pass
        
    @abstractmethod
    def report_summary(self, result: ScrapingResult) -> None:
        """Report scraping summary."""
        pass
