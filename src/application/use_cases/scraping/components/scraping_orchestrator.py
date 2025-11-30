from datetime import datetime
from pathlib import Path
from typing import Optional

from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.domain.value_objects.scraping.scraping_result import ScrapingResult
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.interfaces.i_page_scraping_service import IPageScrapingService
from src.domain.interfaces.scraping.i_progress_service import IProgressService
from src.domain.interfaces.scraping.i_progress_reporter import IProgressReporter

from .page_processor import PageProcessor
from .scraping_loop_controller import ScrapingLoopController
from .result_composer import ResultComposer


class ScrapingOrchestrator:
    def __init__(
        self,
        page_scraping_service: IPageScrapingService,
        problem_repository: IProblemRepository,
        problem_factory: IProblemFactory,
        progress_service: IProgressService,
        progress_reporter: IProgressReporter
    ):
        self._page_scraping_service = page_scraping_service
        self._problem_repository = problem_repository
        self._problem_factory = problem_factory
        self._progress_service = progress_service
        self._progress_reporter = progress_reporter

    async def orchestrate_scraping(
        self, 
        subject_info: SubjectInfo, 
        config: ScrapingConfig
    ) -> ScrapingResult:
        start_time = datetime.now()
        self._progress_reporter.report_start(subject_info, config)

        try:
            start_page = await self._progress_service.get_next_page_to_scrape(subject_info, config)
            base_run_folder = Path("data") / subject_info.alias
            
            page_processor = PageProcessor(
                self._page_scraping_service,
                self._problem_repository,
                self._problem_factory,
                self._progress_reporter
            )
            
            loop_result = await ScrapingLoopController().run_loop(
                start_page, subject_info, config, base_run_folder, page_processor
            )
            
            final_result = ResultComposer().compose_final_result(
                subject_info, loop_result, start_time, datetime.now()
            )
            
            self._progress_reporter.report_summary(final_result)
            return final_result

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            self._progress_reporter.report_page_error(0, error_msg)
            return self._create_error_result(subject_info, start_time, error_msg)

    def _create_error_result(
        self, 
        subject_info: SubjectInfo, 
        start_time: datetime, 
        error_msg: str
    ) -> ScrapingResult:
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
