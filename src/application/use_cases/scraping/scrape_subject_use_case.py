import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.application.services.page_scraping_service import PageScrapingService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.domain.models.problem import Problem

logger = logging.getLogger(__name__)

class _NoopProgressService:
    async def get_next_page_to_scrape(self, subject_info, config):
        return 1

class _NoopProgressReporter:
    def report_start(self, *a, **k): pass
    def report_page_progress(self, *a, **k): pass
    def report_page_error(self, *a, **k): pass
    def report_summary(self, *a, **k): pass

class ScrapeSubjectUseCase:
    def __init__(
        self,
        page_scraping_service: PageScrapingService,
        problem_repository: IProblemRepository,
        problem_factory: IProblemFactory,
        browser_service: IBrowserService,
        asset_downloader_impl: IAssetDownloader,
        progress_service: Optional[Any] = None,
        progress_reporter: Optional[Any] = None
    ):
        self.page_scraping_service = page_scraping_service
        self.problem_repository = problem_repository
        self.problem_factory = problem_factory
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl
        self.progress_service = progress_service or _NoopProgressService()
        self.progress_reporter = progress_reporter or _NoopProgressReporter()

    async def execute(self, subject_info: SubjectInfo, config: ScrapingConfig) -> ScrapingResult:
        start_time = datetime.now()
        self.progress_reporter.report_start(subject_info, config)
        logger.info(f"Starting scraping for subject: {subject_info.official_name} with config: {config}")

        if config.force_restart:
            logger.info(f"Force restart enabled for {subject_info.official_name}. Clearing existing problems...")
            if hasattr(self.problem_repository, "clear_subject_problems"):
                try:
                    clear_method = getattr(self.problem_repository, "clear_subject_problems")
                    if asyncio.iscoroutinefunction(clear_method):
                        await clear_method(subject_info.official_name)
                    else:
                        clear_method(subject_info.official_name)
                except Exception as e:
                    logger.error(f"Failed to clear existing problems: {e}", exc_info=True)

        try:
            start_page_num = await self.progress_service.get_next_page_to_scrape(subject_info, config)
            
            base_run_folder = Path("data") / subject_info.alias
            base_run_folder.mkdir(parents=True, exist_ok=True)

            total_scraped_problems = 0
            total_found = 0
            all_page_results = []
            errors = []

            current_page = start_page_num
            has_more_pages = True
            empty_pages_count = 0

            while has_more_pages and empty_pages_count < 3:
                if config.max_pages and current_page >= start_page_num + config.max_pages:
                    break

                page_result = await self._process_single_page(
                    current_page=current_page,
                    subject_info=subject_info,
                    base_run_folder=base_run_folder,
                    config=config
                )
                
                problems_found = page_result.get("problems_found", 0)
                total_found += problems_found
                total_scraped_problems += page_result.get("problems_saved", 0)
                all_page_results.append(page_result)
                
                if problems_found == 0:
                    empty_pages_count += 1
                else:
                    empty_pages_count = 0
                
                if page_result.get("error"):
                    errors.append(page_result["error"])
                    has_more_pages = False
                elif problems_found == 0:
                    has_more_pages = False
                else:
                    current_page += 1

            duration = datetime.now() - start_time
            success = total_scraped_problems > 0

            result = ScrapingResult(
                subject_name=subject_info.official_name,
                success=success,
                total_pages=len(all_page_results),
                total_problems_found=total_found,
                total_problems_saved=total_scraped_problems,
                page_results=all_page_results,
                errors=errors,
                start_time=start_time,
                end_time=datetime.now()
            )

            self.progress_reporter.report_summary(result)
            logger.info(f"Completed scraping for subject {subject_info.official_name}. Total problems saved: {total_scraped_problems}. Duration: {duration.total_seconds():.2f}s")
            return result

        except Exception as e:
            duration = datetime.now() - start_time
            logger.error(f"Critical error during scraping for subject {subject_info.official_name}: {e}", exc_info=True)
            self.progress_reporter.report_page_error(0, f"Critical error: {str(e)}")
            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=0,
                total_problems_found=0,
                total_problems_saved=0,
                page_results=[],
                errors=[str(e)],
                start_time=start_time,
                end_time=datetime.now()
            )

    async def _process_single_page(
        self,
        current_page: int,
        subject_info: SubjectInfo,
        base_run_folder: Path,
        config: ScrapingConfig
    ) -> Dict[str, any]:
        page_start_time = datetime.now()
        page_result = {
            "page_number": current_page,
            "problems_found": 0,
            "problems_saved": 0,
            "assets_downloaded": 0,
            "page_duration_seconds": 0.0,
            "error": None
        }

        try:
            page_run_folder = base_run_folder / f"page_{current_page}"
            page_run_folder.mkdir(parents=True, exist_ok=True)
            page_assets_dir = page_run_folder / "assets"
            page_assets_dir.mkdir(parents=True, exist_ok=True)

            # Исправляем base_url для правильного формирования URL изображений
            base_url = "https://ege.fipi.ru/bank/"
            page_url = f"https://ege.fipi.ru/bank/questions.php?proj={subject_info.proj_id}&page={current_page-1}&pagesize=10"

            problems = await self.page_scraping_service.scrape_page(
                url=page_url,
                subject_info=subject_info,
                base_url=base_url,
                timeout=config.timeout_seconds,
                run_folder_page=page_run_folder,
                files_location_prefix="assets/"
            )

            assets_count = sum(1 for _ in page_assets_dir.iterdir() if _.is_file()) if page_assets_dir.exists() else 0
            saved_count = await self._save_problems(problems, config.force_restart)

            page_duration = datetime.now() - page_start_time

            page_result.update({
                "problems_found": len(problems),
                "problems_saved": saved_count,
                "assets_downloaded": assets_count,
                "page_duration_seconds": page_duration.total_seconds()
            })

            self.progress_reporter.report_page_progress(
                page_num=current_page,
                total_pages=0,
                problems_found=len(problems),
                problems_saved=saved_count,
                assets_downloaded=assets_count,
                duration_seconds=page_duration.total_seconds()
            )

        except Exception as e:
            error_msg = f"Error processing page {current_page}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            page_result["error"] = error_msg
            self.progress_reporter.report_page_error(current_page, str(e))

        return page_result

    async def _save_problems(self, problems: List[Problem], force_restart: bool) -> int:
        saved_count = 0
        for problem in problems:
            try:
                await self.problem_repository.save(problem, force_update=force_restart)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save problem {getattr(problem, 'problem_id', '<unknown>')}: {e}", exc_info=True)
        return saved_count
