"""
Application service that orchestrates page scraping using domain services.

This service coordinates the domain page scraping service with other application
concerns like logging, error handling, and progress reporting.
"""
import logging
from pathlib import Path
from typing import Optional

from src.domain.interfaces.services.i_page_scraping_service import IPageScrapingService
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.page_scraping_result import PageScrapingResult

logger = logging.getLogger(__name__)


class PageScrapingOrchestrator:
    """
    Application service for orchestrating page scraping operations.
    
    This service doesn't contain scraping logic itself but coordinates
    between domain services and application concerns.
    """

    def __init__(self, page_scraping_service: IPageScrapingService):
        self._page_scraping_service = page_scraping_service

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
        Orchestrate page scraping with application-level concerns.
        
        Args:
            url: The URL of the page to scrape.
            subject_info: Subject information value object.
            base_url: The base URL for constructing relative links.
            timeout: Timeout for operations in seconds.
            run_folder_page: Optional path for storing page assets.
            files_location_prefix: Prefix for file paths in problem entities.

        Returns:
            PageScrapingResult from domain service.
        """
        logger.info(f"Starting page scraping for URL: {url}")
        
        try:
            result = await self._page_scraping_service.scrape_page(
                url=url,
                subject_info=subject_info,
                base_url=base_url,
                timeout=timeout,
                run_folder_page=run_folder_page,
                files_location_prefix=files_location_prefix
            )
            
            logger.info(f"Page scraping completed: {len(result.problems)} problems, "
                       f"{result.assets_downloaded} assets downloaded")
            return result
            
        except Exception as e:
            logger.error(f"Page scraping failed for {url}: {e}")
            # Return empty result rather than raising to allow continuation
            return PageScrapingResult(problems=[], assets_downloaded=0)
