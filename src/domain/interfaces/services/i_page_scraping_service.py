"""
Domain interface for page scraping service.

This interface defines the core domain operation of scraping educational content
and converting it into domain entities (Problem), making it a domain service.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.page_scraping_result import PageScrapingResult


class IPageScrapingService(ABC):
    """
    Domain service interface for page scraping operations.
    Defines the core domain operation of scraping a page into Problem entities.
    """

    @abstractmethod
    async def scrape_page(
        self,
        url: str,
        subject_info: SubjectInfo,
        base_url: str,
        timeout: int = 30,
        run_folder_page: Optional[Path] = None,
        files_location_prefix: str = ""
    ) -> PageScrapingResult:
        """
        Scrape a single page and return PageScrapingResult with domain entities.

        Args:
            url: The URL of the page to scrape.
            subject_info: Subject information value object.
            base_url: The base URL for constructing relative links.
            timeout: Timeout for operations in seconds.
            run_folder_page: Optional path for storing page assets.
            files_location_prefix: Prefix for file paths in problem entities.

        Returns:
            PageScrapingResult containing Problem entities and assets count.
        """
        pass
