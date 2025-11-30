"""
Adapter that adapts the existing PageScrapingService implementation to the domain interface.

This adapter bridges the gap between the existing implementation and the new domain interface,
allowing us to use the existing scraping logic while adhering to the new architecture.
"""
import logging
from pathlib import Path
from typing import Optional, List, Any

from src.domain.interfaces.services.i_page_scraping_service import IPageScrapingService
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.page_scraping_result import PageScrapingResult
from src.application.services.page_scraping_service import PageScrapingService

logger = logging.getLogger(__name__)


class PageScrapingAdapter(IPageScrapingService):
    """
    Adapter that makes the existing PageScrapingService compatible with the domain interface.
    
    This adapter handles the translation between the existing implementation's return type
    and the domain's PageScrapingResult value object.
    """

    def __init__(self, page_scraping_service: PageScrapingService):
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
        Adapt the existing PageScrapingService to return PageScrapingResult.
        
        The existing service now returns a tuple (problems, assets_count).
        """
        try:
            # 1. Вызов сервиса. Ожидаем кортеж (problems, assets_downloaded)
            result_tuple = await self._page_scraping_service.scrape_page(
                url=url,
                subject_info=subject_info,
                base_url=base_url,
                timeout=timeout,
                run_folder_page=run_folder_page,
                files_location_prefix=files_location_prefix
            )
            
            # Распаковываем кортеж (List[Any], int)
            # PageScrapingService ГАРАНТИРОВАННО возвращает кортеж из двух, даже при ошибке.
            problems_list, assets_downloaded = result_tuple
            
            problems_list = list(problems_list) if problems_list else []
            
            logger.debug(f"Adapter: {len(problems_list)} problems, {assets_downloaded} assets (FS count)")
            
            return PageScrapingResult(
                problems=problems_list,
                assets_downloaded=assets_downloaded
            )
            
        except Exception as e:
            logger.error(f"Error in page scraping adapter for {url}: {e}", exc_info=True)
            return PageScrapingResult(problems=[], assets_downloaded=0)
