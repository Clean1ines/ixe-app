"""
Use Case for scraping a single subject.

This use case coordinates the scraping process for a single subject,
handling all the business logic while delegating infrastructure concerns
to appropriate adapters.
"""
import logging
# Удаляем import shutil и pathlib, так как больше не удаляем директории
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.application.services.page_scraping_service import PageScrapingService # Импортируем обновлённый сервис

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
        page_scraping_service: PageScrapingService, # Добавляем зависимость
    ):
        """
        Initialize use case with required dependencies.

        Args:
            browser_service: Service for browser management
            problem_repository: Service for problem persistence
            page_scraping_service: Service for page scraping logic and problem creation
        """
        self.browser_service = browser_service
        self.problem_repository = problem_repository
        self.page_scraping_service = page_scraping_service # Сохраняем

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
        - Handles force restart option (affects scraping/re-saving logic, not DB deletion)
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
            # --- LOGIC: Handle raw HTML directory (if needed for caching, separate concern) ---
            # We no longer manage a subject-specific data directory like 'data/{alias}/{year}' here.
            # Raw HTML saving/caching logic (if any) should be handled by PageScrapingService or BrowserService if necessary.
            # The primary persistence (Problems) is handled by IProblemRepository.

            # Initialize database (example logic - delegate to repository or separate service)
            # await self.problem_repository.initialize_database() # Если репозиторий сам может

            # Determine the base URL for the subject's project
            # This might come from SubjectInfo or be constructed based on a template and proj_id
            base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}" # Example base URL construction

            # Scrape initial page (using real PageScrapingService)
            init_url = f"{base_url}?page=init" # Construct URL for init page
            try:
                init_problems = await self.page_scraping_service.scrape_page(
                    url=init_url,
                    subject_info=subject_info,
                    base_url=base_url,
                    timeout=config.timeout_seconds
                )
                # Save the problems found on the init page
                init_result = await self._create_page_result_and_save_problems(
                    page_number="init",
                    problems=init_problems,
                    subject_info=subject_info,
                    config=config # Передаём config
                )
                page_results.append(init_result)
                total_problems_found += len(init_problems)
                total_problems_saved += init_result.get("problems_saved", 0)

            except Exception as e:
                logger.error(f"Error scraping init page for {subject_info.official_name}: {e}", exc_info=True)
                errors.append(f"Init page scraping failed: {e}")

            # Determine the last page number from the pager (stub implementation - needs real logic)
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

                # Construct URL for current page
                page_url = f"{base_url}?page={page_num}"
                try:
                    page_problems = await self.page_scraping_service.scrape_page(
                        url=page_url,
                        subject_info=subject_info,
                        base_url=base_url,
                        timeout=config.timeout_seconds
                    )
                    page_result = await self._create_page_result_and_save_problems(
                        page_number=str(page_num),
                        problems=page_problems,
                        subject_info=subject_info,
                        config=config # Передаём config
                    )
                    page_results.append(page_result)

                    total_problems_found += len(page_problems)
                    total_problems_saved += page_result.get("problems_saved", 0)

                    # Update empty page counter (example logic)
                    if len(page_problems) == 0:
                        empty_count += 1
                    else:
                        empty_count = 0

                    # Check for consecutive empty pages (fallback)
                    if empty_count >= config.max_empty_pages:
                        logger.info(f"Reached {config.max_empty_pages} consecutive empty pages. Stopping scraping.")
                        break

                except Exception as e:
                    logger.error(f"Error scraping page {page_num} for {subject_info.official_name}: {e}", exc_info=True)
                    errors.append(f"Page {page_num} scraping failed: {e}")
                    # Depending on business rules, decide whether to continue or stop
                    # For now, we continue to the next page
                    empty_count += 1 # Treat failed page like an empty one for fallback logic?
                    if empty_count >= config.max_empty_pages:
                         logger.info(f"Reached {config.max_empty_pages} consecutive problematic pages. Stopping scraping.")
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

    async def _create_page_result_and_save_problems(
        self,
        page_number: str,
        problems: List['Problem'], # Предполагаем, что PageScrapingService возвращает List[Problem]
        subject_info: SubjectInfo,
        config: ScrapingConfig # Принимаем config
    ) -> Dict[str, Any]:
        """
        Create a page result dictionary and save the found problems to the repository.

        Args:
            page_number: The number/identifier of the page scraped.
            problems: List of Problem entities found on the page.
            subject_info: SubjectInfo for metadata.
            config: ScrapingConfig for options like force_restart.

        Returns:
            Dictionary representing the page result, including counts of found and saved problems.
        """
        problems_found = len(problems)
        problems_saved = 0
        save_errors = []

        for problem in problems:
            try:
                # Save the problem entity using the repository
                # Pass the config.force_restart flag if the repository needs to know about it for update logic
                await self.problem_repository.save(problem, force_update=config.force_restart) # Теперь config доступна
                problems_saved += 1
            except Exception as e:
                logger.error(f"Failed to save problem {problem.problem_id} from page {page_number}: {e}")
                save_errors.append(str(e))

        return {
            "page_number": page_number,
            "success": len(save_errors) == 0, # Success based on save errors for this page
            "problems_found": problems_found,
            "problems_saved": problems_saved,
            "save_errors": save_errors,
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
        # TODO: Implement actual logic to navigate and parse the pager using browser_service
        # This would require browser interaction to check the pager
        # Example (replace with real logic):
        # browser = await self.browser_service.get_browser()
        # page = await browser.new_page()
        # await page.goto(f"{BASE_URL}?proj={proj_id}&page=1")
        # pager_element = await page.query_selector(".pager") # Example selector
        # if pager_element:
        #     # Parse the pager to find the last page number
        #     last_page_num = ...
        #     await page.close()
        # await self.browser_service.release_browser(browser)
        logger.info("Last page determination not implemented in this version. Returning None to trigger fallback.")
        return None # Placeholder - replace with actual implementation

