from typing import Optional
"""
Application interface for Page Scraping Service operations.

This interface defines the contract for scraping a single page and converting
its content into a list of Problem entities, allowing the application layer
to remain independent of the specific implementation details (e.g., which
HTML processors are used, how assets are downloaded).
This interface sits in the Application layer as it defines a specific application-level
operation (scraping a page and returning domain entities) rather than a core domain concept.
"""
import abc
from pathlib import Path
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.page_scraping_result import PageScrapingResult


class IPageScrapingService(abc.ABC):
    """
    Application interface for page scraping operations.
    Defines the operation of scraping a single page into Problem entities.
    """

    @abc.abstractmethod
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
        Scrape a single page and return PageScrapingResult with Problem entities and assets count.

        Args:
            url: The URL of the page to scrape.
            subject_info: The SubjectInfo object containing subject details.
            base_url: The base URL of the scraped site.
            timeout: Timeout for browser operations.
            run_folder_page: Optional path to the run folder for this page's assets.
                             Processors will use this via the adapter if they save files.
            files_location_prefix: Prefix for file paths in the output (used by processors via adapter).

        Returns:
            A PageScrapingResult containing Problem entities and assets count.
        """
