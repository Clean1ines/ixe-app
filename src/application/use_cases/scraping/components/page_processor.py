import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import logging

from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.interfaces.services.i_page_scraping_service import IPageScrapingService
from src.domain.interfaces.scraping.i_progress_reporter import IProgressReporter

from .data_structures import PageResult

logger = logging.getLogger(__name__)


class PageProcessor:
    def __init__(
        self,
        page_scraping_service: IPageScrapingService,
        problem_repository: IProblemRepository,
        progress_reporter: IProgressReporter
    ):
        self._page_scraping_service = page_scraping_service
        self._problem_repository = problem_repository
        self._progress_reporter = progress_reporter

    async def process_page(
        self,
        page_num: int,
        subject_info: SubjectInfo,
        config: ScrapingConfig,
        base_run_folder: Path
    ) -> PageResult:
        start_time = datetime.now()
        
        try:
            page_url = self._build_page_url(subject_info.base_url, page_num)
            
            # Используем доменный сервис для скрапинга страницы
            scraping_result = await self._page_scraping_service.scrape_page(
                url=page_url,
                subject_info=subject_info,
                base_url=subject_info.base_url,
                timeout=getattr(config, 'timeout', 30),
                run_folder_page=base_run_folder / f"page_{page_num}",
                files_location_prefix=f"data/{subject_info.alias}/page_{page_num}"
            )

            problems_list = scraping_result.problems
            assets_downloaded = scraping_result.assets_downloaded
            
            logger.info(f"Page {page_num}: получено {len(problems_list)} проблем, ассетов: {assets_downloaded}")
            
            if not problems_list:
                return PageResult(
                    page_number=page_num,
                    problems_found=0,
                    problems_saved=0,
                    assets_downloaded=0,
                    page_duration_seconds=(datetime.now() - start_time).total_seconds()
                )

            # Сохраняем готовые Problem объекты
            saved_count = await self._save_problems(problems_list, page_num)
            
            logger.info(f"Page {page_num}: сохранено {saved_count} проблем")

            # Вычисляем длительность выполнения страницы
            page_duration = (datetime.now() - start_time).total_seconds()
            
            self._progress_reporter.report_page_progress(
                page_num, 
                None,  # total_pages
                len(problems_list), 
                saved_count, 
                assets_downloaded,
                page_duration
            )

            return PageResult(
                page_number=page_num,
                problems_found=len(problems_list),
                problems_saved=saved_count,
                assets_downloaded=assets_downloaded,
                page_duration_seconds=page_duration
            )

        except Exception as e:
            error_msg = f"Page {page_num} error: {str(e)}"
            logger.error(error_msg)
            self._progress_reporter.report_page_error(page_num, error_msg)
            return PageResult(
                page_number=page_num,
                problems_found=0,
                problems_saved=0,
                assets_downloaded=0,
                page_duration_seconds=(datetime.now() - start_time).total_seconds(),
                error=error_msg
            )

    def _build_page_url(self, base_url: str, page_num: int) -> str:
        return f"{base_url}?page={page_num}" if page_num > 1 else base_url

    async def _save_problems(self, problems: List, page_num: int) -> int:
        saved_count = 0
        for problem in problems:
            try:
                await self._problem_repository.save(problem)
                saved_count += 1
                logger.debug(f"Page {page_num}: сохранена проблема {getattr(problem, 'problem_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Page {page_num}: ошибка сохранения проблемы: {e}")
        return saved_count
