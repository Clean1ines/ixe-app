"""
Use Case for scraping a single subject.

This use case coordinates the scraping process for a single subject,
handling all the business logic while delegating infrastructure concerns
to appropriate adapters.
"""
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.scraping_result import ScrapingResult
# from src.application.services.page_scraping_service import PageScrapingService # Пока не создаём
# from src.application.factories.problem_factory import ProblemFactory # Пока не создаём

logger = logging.getLogger(__name__)

class ScrapeSubjectUseCase:
    """
    Use Case for scraping a single subject.

    Business Rules:
    - Handles both initial scraping and updates
    - Manages resource cleanup properly
    - Provides progress reporting
    - Handles errors gracefully
    - Respects scraping configuration
    - Ensures data integrity
    """

    def __init__(
        self,
        browser_service: IBrowserService,
        problem_repository: IProblemRepository,
        # page_scraping_service: PageScrapingService, # Зависимость, которую добавим позже
        # problem_factory: ProblemFactory, # Зависимость, которую добавим позже
    ):
        """
        Initialize use case with required dependencies.

        Args:
            browser_service: Service for browser management
            problem_repository: Service for problem persistence
            # page_scraping_service: Service for page scraping logic
            # problem_factory: Factory for creating domain problems
        """
        self.browser_service = browser_service
        self.problem_repository = problem_repository
        # self.page_scraping_service = page_scraping_service
        # self.problem_factory = problem_factory

    async def execute(
        self,
        subject_info: SubjectInfo,
        config: ScrapingConfig
    ) -> ScrapingResult:
        """
        Execute the scraping use case.

        Args:
            subject_info: Subject information for scraping
            config: Scraping configuration

        Returns:
            ScrapingResult containing detailed results

        Business Rules:
        - Checks existing data before scraping
        - Initializes database if needed
        - Handles force restart option
        - Provides detailed progress reporting
        - Ensures proper resource cleanup
        """
        logger.info(f"Starting scraping for subject: {subject_info.official_name}")
        start_time = datetime.now()
        page_results: List[Dict[str, Any]] = []
        errors: List[str] = []
        total_problems_found = 0
        total_problems_saved = 0

        try:
            # Setup directories (example logic - now based on alias/year if needed, but centralized)
            # For now, let's assume raw HTML goes to a central location based on subject alias
            output_dir = Path(f"data/{subject_info.alias}/{subject_info.exam_year}")
            raw_html_dir = output_dir / "raw_html"
            if config.force_restart and output_dir.exists():
                logger.info(f"Force restart enabled. Deleting existing data for {subject_info.official_name}")
                shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            raw_html_dir.mkdir(parents=True, exist_ok=True)

            # Initialize database (example logic - delegate to repository or separate service)
            # await self.problem_repository.initialize_database() # Если репозиторий сам может

            # Scrape initial page (example stub)
            init_result = await self._scrape_page_stub(
                subject_info=subject_info,
                config=config,
                page_number="init"
            )
            page_results.append(init_result)
            total_problems_found += init_result.get("problems_found", 0)
            total_problems_saved += init_result.get("problems_saved", 0)

            # Determine the last page number from the pager (stub implementation)
            last_page_num = await self._determine_last_page(subject_info.proj_id)
            logger.info(f"Determined last page number for {subject_info.official_name}: {last_page_num}")

            if last_page_num is None:
                 logger.warning(f"Could not determine last page number for {subject_info.official_name}. Using fallback logic with max_pages.")
                 # Use config.max_pages as fallback if pager fails
                 last_page_num = config.max_pages if config.max_pages is not None else 100 # Arbitrary large number as fallback

            # Scrape numbered pages (example logic - now based on determined last page)
            page_num = 1
            empty_count = 0

            while True:
                # Check if we've reached the determined last page
                if last_page_num is not None and page_num > last_page_num:
                    logger.info(f"Reached determined last page ({last_page_num}). Stopping scraping.")
                    break

                # Check if we've hit max pages config (fallback)
                if config.max_pages is not None and page_num > config.max_pages:
                    logger.info(f"Reached configured max pages ({config.max_pages}). Stopping scraping.")
                    break

                page_result = await self._scrape_page_stub(
                    subject_info=subject_info,
                    config=config,
                    page_number=str(page_num)
                )
                page_results.append(page_result)
                total_problems_found += page_result.get("problems_found", 0)
                total_problems_saved += page_result.get("problems_saved", 0)

                # Update empty page counter (example logic)
                if page_result.get("problems_found", 0) == 0:
                    empty_count += 1
                else:
                    empty_count = 0

                # Check for consecutive empty pages (fallback)
                if empty_count >= config.max_empty_pages:
                    logger.info(f"Reached {config.max_empty_pages} consecutive empty pages. Stopping scraping.")
                    break

                page_num += 1

            # Create final result
            end_time = datetime.now()
            overall_success = len(errors) == 0 # Simplified success logic

            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=overall_success,
                total_pages=len(page_results),
                total_problems_found=total_problems_found,
                total_problems_saved=total_problems_saved,
                page_results=page_results,
                errors=errors,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "subject_info": subject_info.__dict__, # Simplified metadata
                    "config": config.__dict__,
                }
            )

        except Exception as e:
            logger.error(f"Scraping failed for {subject_info.official_name}: {e}", exc_info=True)
            errors.append(str(e))
            end_time = datetime.now()

            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=len(page_results),
                total_problems_found=total_problems_found,
                total_problems_saved=total_problems_saved,
                page_results=page_results,
                errors=errors,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "subject_info": subject_info.__dict__,
                    "config": config.__dict__,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )

    async def _scrape_page_stub(
        self,
        subject_info: SubjectInfo,
        config: ScrapingConfig,
        page_number: str
    ) -> Dict[str, Any]:
        """
        Stub for scraping a single page. This will be replaced by actual page scraping logic.

        Args:
            subject_info: Subject information
            config: Scraping configuration
            page_number: Page number to scrape

        Returns:
            Dict containing stub result data.
        """
        logger.debug(f"Stub scraping page '{page_number}' for subject {subject_info.official_name}")
        # Simulate scraping result
        problems_found = 1 if page_number == "init" else 0  # Example: init page has 1 problem, others might have 0
        problems_saved = problems_found  # Example: all found are saved
        return {
            "page_number": page_number,
            "success": True,
            "problems_found": problems_found,
            "problems_saved": problems_saved,
            "raw_html_path": f"raw_html/page_{page_number}.html", # Example path
            "metadata": {"subject_key": subject_info.alias, "proj_id": subject_info.proj_id} # Using alias
        }

    async def _determine_last_page(self, proj_id: str) -> Optional[int]:
        """
        Determine the last page number from the pager element on the FIPI site.

        Args:
            proj_id: The FIPI project ID for the subject.

        Returns:
            The last page number if found, otherwise None.
        """
        # TODO: Implement actual logic to navigate and parse the pager
        # This would require browser interaction to check the pager
        # Example (replace with real logic):
        # browser = await self.browser_service.get_browser()
        # page = await browser.new_page()
        # await page.goto(f"{BASE_URL}?proj={proj_id}&page=1")
        # pager_element = await page.query_selector(".pager") # Example selector
        # if pager_element:
        #     # Parse the pager to find the last page number
        #     last_page_num = ...
        #     return last_page_num
        # await page.close()
        # await self.browser_service.release_browser(browser)
        logger.info("Last page determination not implemented in this version. Returning None to trigger fallback.")
        return None # Placeholder - replace with actual implementation

