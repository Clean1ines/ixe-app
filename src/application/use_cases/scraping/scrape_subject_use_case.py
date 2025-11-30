from typing import Optional
import logging
from pathlib import Path
from datetime import datetime

from src.domain.interfaces.services.i_page_scraping_service import IPageScrapingService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.domain.interfaces.scraping.i_progress_service import IProgressService
from src.domain.interfaces.scraping.i_progress_reporter import IProgressReporter

from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.scraping_result import ScrapingResult

from src.application.use_cases.scraping.components import PageProcessor, ScrapingLoopController, ResultComposer

logger = logging.getLogger(__name__)


class _NoopProgressService(IProgressService):
    async def get_next_page_to_scrape(
        self, 
        subject_info: SubjectInfo, 
        start_page: str,
        force_restart: bool
    ) -> int:
        return int(start_page) if start_page != "init" else 1


class _NoopProgressReporter(IProgressReporter):
    def report_start(
        self, 
        subject_info: SubjectInfo, 
        start_page: str,
        max_pages: Optional[int],
        force_restart: bool
    ) -> None:
        pass

    def report_page_progress(self, page: int, total_pages: Optional[int], 
                             problems_found: int, problems_saved: int, 
                             assets_downloaded: int, duration_seconds: float) -> None:
        pass

    def report_page_error(self, page: int, error: str) -> None:
        pass

    def report_summary(self, result: ScrapingResult) -> None:
        pass


class ScrapeSubjectUseCase:
    def __init__(
        self,
        page_scraping_service: IPageScrapingService,
        problem_repository: IProblemRepository,
        problem_factory: IProblemFactory,
        browser_service: IBrowserService,
        asset_downloader_impl: IAssetDownloader,
        progress_service: Optional[IProgressService] = None,
        progress_reporter: Optional[IProgressReporter] = None
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

        # Разворачиваем параметры конфига в примитивы для вызова Domain Interface
        self.progress_reporter.report_start(
            subject_info, 
            config.start_page, 
            config.max_pages, 
            config.force_restart
        )

        logger.info(f"Starting scraping for subject: {subject_info.official_name}")

        if config.force_restart:
            await self._clear_existing_problems(subject_info)

        try:
            # Передаем примитивы в ProgressService
            start_page = await self.progress_service.get_next_page_to_scrape(
                subject_info, 
                config.start_page, 
                config.force_restart
            )

            base_run_folder = Path("data") / subject_info.alias

            # Компоненты Application Layer продолжают получать полный config
            page_processor = PageProcessor(
                self.page_scraping_service,
                self.problem_repository,
                self.progress_reporter
            )

            loop_result = await ScrapingLoopController().run_loop(
                start_page, subject_info, config, base_run_folder, page_processor
            )

            final_result = ResultComposer().compose_final_result(
                subject_info, loop_result, start_time, datetime.now()
            )

            self.progress_reporter.report_summary(final_result)
            logger.info(f"Scraping completed: {final_result.total_problems_saved} problems saved")
            return final_result

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.progress_reporter.report_page_error(0, error_msg)

            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=0,
                total_problems_found=0,
                total_problems_saved=0,
                page_results=[],
                errors=[error_msg],
                start_time=start_time,
                end_time=datetime.now()
            )

    async def _clear_existing_problems(self, subject_info: SubjectInfo) -> None:
        """Clear existing problems for the subject before scraping."""
        logger.info(f"Clearing existing problems for subject: {subject_info.official_name}")
        problems = await self.problem_repository.get_by_subject(subject_info.official_name)
        # TODO: Реализовать фактическое удаление через репозиторий, если потребуется
        logger.warning(f"Force restart requested. Found {len(problems)} existing problems (deletion not implemented).")
