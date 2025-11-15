"""
Use Case for scraping a single subject.

This use case coordinates the scraping process for a single subject,
handling all the business logic while delegating infrastructure concerns
to appropriate adapters.
It integrates PageScrapingService which uses concrete HTML processors
and an asset downloader adapter. All problems are saved to a single shared database.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.application.services.page_scraping_service import PageScrapingService

logger = logging.getLogger(__name__)

class ScrapeSubjectUseCase:
    """
    Use Case for scraping a single subject.

    Business Rules:
    - Handles both initial scraping and updates for a single subject
    - Manages resource cleanup properly (delegated to lower layers)
    - Provides progress reporting
    - Handles errors gracefully
    - Respects scraping configuration
    - Ensures data integrity in the shared database
    - Operates on a single, shared database for all subjects
    """

    def __init__(
        self,
        browser_service: IBrowserService,
        asset_downloader: IAssetDownloader,
        problem_repository: IProblemRepository,
        page_scraping_service: PageScrapingService,
    ):
        """
        Initialize use case with required dependencies.

        Args:
            browser_service: Service for browser management (implements IBrowserService)
            asset_downloader: Service for downloading assets (implements IAssetDownloader) - operates on SHARED DB
            problem_repository: Service for problem persistence (implements IProblemRepository) - operates on SHARED DB
            page_scraping_service: Service for page scraping logic and problem creation (uses concrete processors)
        """
        self.browser_service = browser_service
        self.asset_downloader = asset_downloader
        self.problem_repository = problem_repository
        self.page_scraping_service = page_scraping_service

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
        - Checks existing data before scraping (delegated to repository or service logic)
        - Initializes database if needed (delegated to repository or separate service, operates on SHARED DB)
        - Handles force restart option (affects scraping/re-saving logic, potentially passed to repository)
        - Provides detailed progress reporting
        - Ensures proper resource cleanup (delegated to services/adapters)
        - Saves all scraped problems to the SHARED database via IProblemRepository
        """
        logger.info(f"Starting scraping for subject: {subject_info.official_name}")
        start_time = datetime.now()
        page_results: List[Dict[str, Any]] = []
        errors: List[str] = []
        total_problems_found = 0
        total_problems_saved = 0

        try:
            base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}"

            init_url = f"{base_url}?page=init"
            try:
                init_problems = await self.page_scraping_service.scrape_page(
                    url=init_url,
                    subject_info=subject_info,
                    base_url=base_url,
                    timeout=config.timeout_seconds,
                )
                init_result = self._create_page_result("init", init_problems, subject_info)
                page_results.append(init_result)
                total_problems_found += len(init_problems)
                total_problems_saved += await self._save_problems(init_problems, force_update=config.force_restart)

            except Exception as e:
                logger.error(f"Error scraping init page for {subject_info.official_name}: {e}", exc_info=True)
                errors.append(f"Init page scraping failed: {e}")

            last_page_num = await self._determine_last_page(subject_info.proj_id)
            logger.info(f"Determined last page number for {subject_info.official_name}: {last_page_num}")

            if last_page_num is None:
                 logger.warning(f"Could not determine last page number for {subject_info.official_name}. Using fallback logic with max_pages.")
                 last_page_num = config.max_pages if config.max_pages is not None else 100

            page_num = 1
            empty_count = 0

            while True:
                if last_page_num is not None and page_num > last_page_num:
                    logger.info(f"Reached determined last page ({last_page_num}). Stopping scraping.")
                    break

                if config.max_pages is not None and page_num > config.max_pages:
                    logger.info(f"Reached configured max pages ({config.max_pages}). Stopping scraping.")
                    break

                page_url = f"{base_url}?page={page_num}"
                try:
                    page_problems = await self.page_scraping_service.scrape_page(
                        url=page_url,
                        subject_info=subject_info,
                        base_url=base_url,
                        timeout=config.timeout_seconds,
                    )
                    page_result = self._create_page_result(str(page_num), page_problems, subject_info)
                    page_results.append(page_result)

                    total_problems_found += len(page_problems)
                    total_problems_saved += await self._save_problems(page_problems, force_update=config.force_restart)

                    if len(page_problems) == 0:
                        empty_count += 1
                    else:
                        empty_count = 0

                    if empty_count >= config.max_empty_pages:
                        logger.info(f"Reached {config.max_empty_pages} consecutive empty pages. Stopping scraping.")
                        break

                except Exception as e:
                    logger.error(f"Error scraping page {page_num} for {subject_info.official_name}: {e}", exc_info=True)
                    errors.append(f"Page {page_num} scraping failed: {e}")
                    empty_count += 1
                    if empty_count >= config.max_empty_pages:
                         logger.info(f"Reached {config.max_empty_pages} consecutive problematic pages. Stopping scraping.")
                         break

                page_num += 1

            end_time = datetime.now()
            overall_success = len(errors) == 0

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
                    "subject_info": subject_info.__dict__,
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

    async def _save_problems(self, problems: List['Problem'], force_update: bool = False) -> int:
        saved_count = 0
        for problem in problems:
            try:
                await self.problem_repository.save(problem, force_update=force_update)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save problem {problem.problem_id} to shared DB: {e}")
        return saved_count

    def _create_page_result(self, page_number: str, problems: List['Problem'], subject_info: SubjectInfo) -> Dict[str, Any]:
        problems_found = len(problems)
        return {
            "page_number": page_number,
            "success": True,
            "problems_found": problems_found,
            "problems_saved": problems_found,
            "raw_html_path": f"raw_html/page_{page_number}.html",
            "metadata": {"subject_key": subject_info.alias, "proj_id": subject_info.proj_id}
        }

    async def _determine_last_page(self, proj_id: str) -> Optional[int]:
        logger.info("Last page determination not implemented in this version. Returning None to trigger fallback.")
        return None

