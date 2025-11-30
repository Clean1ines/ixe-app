from typing import List
from pathlib import Path

from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig

from .page_processor import PageProcessor
from .data_structures import PageResult, LoopResult


class ScrapingLoopController:
    def __init__(self, max_empty_pages: int = 3):
        self._max_empty_pages = max_empty_pages

    async def run_loop(
        self,
        start_page: int,
        subject_info: SubjectInfo,
        config: ScrapingConfig,
        base_run_folder: Path,
        page_processor: PageProcessor
    ) -> LoopResult:
        page_results: List[PageResult] = []
        errors: List[str] = []
        empty_pages_count = 0
        current_page = start_page
        total_problems_found = 0
        total_problems_saved = 0
        total_assets_downloaded = 0

        # Исправляем условие: учитываем, что config.max_pages может быть None
        while (empty_pages_count < self._max_empty_pages and 
               (config.max_pages is None or current_page <= config.max_pages)):
            
            page_result = await page_processor.process_page(
                current_page, subject_info, config, base_run_folder
            )
            
            page_results.append(page_result)
            total_problems_found += page_result.problems_found
            total_problems_saved += page_result.problems_saved
            total_assets_downloaded += page_result.assets_downloaded

            if page_result.error:
                errors.append(page_result.error)
                # При ошибке прерываем цикл
                break

            if page_result.problems_found == 0:
                empty_pages_count += 1
            else:
                empty_pages_count = 0

            current_page += 1

        return LoopResult(
            page_results=page_results,
            total_problems_found=total_problems_found,
            total_problems_saved=total_problems_saved,
            total_assets_downloaded=total_assets_downloaded,
            errors=errors,
            last_processed_page=current_page - 1
        )
