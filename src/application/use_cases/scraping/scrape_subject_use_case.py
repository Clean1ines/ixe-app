"""
Use Case for scraping a single subject.
This use case coordinates the scraping process for a single subject,
handling the overall flow, configuration, and interaction with repositories.
It now integrates PageScrapingService which uses HTMLBlockProcessingService
to handle individual blocks, applying a chain of IHTMLProcessor implementations.
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from src.application.services.page_scraping_service import PageScrapingService
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover

logger = logging.getLogger(__name__)

class ScrapeSubjectUseCase:
    """
    Use Case for scraping a single subject.
    Business Rules:
    - Handles both initial scraping and updates for a subject
    - Manages the shared database repository for all subjects
    - Coordinates the scraping of multiple pages using PageScrapingService
    - Uses HTMLBlockProcessingService (via PageScrapingService) to process individual blocks
    - Applies a chain of IHTMLProcessor implementations via HTMLBlockProcessingService
    - Respects scraping configuration (e.g., mode, page limits)
    - Provides detailed results and statistics
    - Handles errors gracefully
    - Manages file storage for downloaded assets via the shared IAssetDownloader
    """
    def __init__(
        self,
        page_scraping_service: PageScrapingService, # PageScrapingService теперь принимает HTMLBlockProcessingService
        problem_repository: IProblemRepository, # Using IProblemRepository interface
        problem_factory: IProblemFactory, # Using IProblemFactory interface
        browser_service: IBrowserService, # Using IBrowserService interface
        asset_downloader_impl: IAssetDownloader, # NEW: Concrete IAssetDownloader implementation
    ):
        """
        Initialize use case with required dependencies.
        Args:
            page_scraping_service: Service for scraping individual pages (implements the processor chain via HTMLBlockProcessingService)
            problem_repository: Repository for saving problems (implements IProblemRepository)
            problem_factory: Factory for creating domain problems (implements IProblemFactory)
            browser_service: Service for browser management (implements IBrowserService)
            asset_downloader_impl: Concrete implementation of IAssetDownloader (e.g., HTTPXAssetDownloaderAdapter)
        """
        self.page_scraping_service = page_scraping_service
        self.problem_repository = problem_repository
        self.problem_factory = problem_factory
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl # Сохраняем IAssetDownloader impl

    async def execute(self, subject_info: SubjectInfo, config: ScrapingConfig) -> ScrapingResult:
        """
        Execute the scraping use case.
        Args:
            subject_info: Subject information for scraping
            config: Scraping configuration parameters
        Returns:
            ScrapingResult containing statistics and outcome.
        """
        logger.info(f"Starting scraping for subject: {subject_info.official_name} with config: {config}")
        start_time = datetime.now()

        try:
            # 1. Determine the range of pages to scrape based on config
            # This might involve calling a method on PageScrapingService or a separate service
            # For now, assume we get this from config or determine it here
            # Обновляем логику для ScrapingMode.SEQUENTIAL и других
            if config.mode == ScrapingMode.SEQUENTIAL:
                # For SEQUENTIAL mode, start from start_page and scrape until max_pages or max_empty_pages
                start_page_num = config.start_page
                last_page = config.max_pages # Interpret max_pages as the last page to scrape
                if start_page_num == "init":
                    page_range = ["init"]
                    if last_page is not None:
                        page_range.extend(list(range(1, last_page + 1)))
                    else:
                        # Если last_page None, используем генератор с остановкой по max_empty_pages
                        # Для тестов и предотвращения зависания, установим разумный лимит
                        page_range = ["init"] + list(range(1, 101)) # Лимит 100 страниц, если max_pages None
                else:
                    # start_page_num - число
                    if last_page is not None:
                        page_range = list(range(start_page_num, last_page + 1))
                    else:
                        # Используем генератор с остановкой по max_empty_pages
                        page_range = list(range(start_page_num, start_page_num + 100)) # Лимит 100 страниц, если max_pages None
            elif config.mode == ScrapingMode.PARALLEL:
                 start_page_num = config.start_page
                 last_page = config.max_pages
                 if start_page_num == "init":
                     page_range = ["init"]
                     if last_page is not None:
                        page_range.extend(list(range(1, last_page + 1)))
                 else:
                     if last_page is not None:
                         page_range = list(range(start_page_num, last_page + 1))
                     else:
                         page_range = list(range(start_page_num, start_page_num + 100)) # Лимит 100 страниц, если max_pages None
            else:
                logger.error(f"Unknown scraping mode: {config.mode}")
                return ScrapingResult(
                    subject_name=subject_info.official_name,
                    success=False,
                    total_pages=0,
                    total_problems_found=0,
                    total_problems_saved=0,
                    page_results=[],
                    errors=[f"Unknown mode: {config.mode}"],
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # 2. Prepare common assets directory for the subject run (if not per page)
            # This is the *shared* assets folder for the entire subject scraping run
            # Individual pages might use subfolders within this
            # Используем базовую директорию из config или дефолтную, если не указана
            # ScrapingConfig не имеет base_run_folder. Нужно передавать его или определить здесь.
            # Пусть base_run_folder передается в execute или определяется здесь.
            # Для совместимости с PageScrapingService, который ожидает Path, определим здесь.
            base_run_folder = Path("data") / subject_info.alias # Временный путь
            subject_run_assets_dir = base_run_folder / "assets"
            subject_run_assets_dir.mkdir(parents=True, exist_ok=True)

            total_scraped_problems = 0
            total_found = 0
            all_page_results = []
            errors = []

            # Counter for consecutive empty pages
            empty_page_count = 0
            max_empty_pages = config.max_empty_pages

            # 3. Scrape each page in the determined range or until max_empty_pages is reached
            for current_page in page_range:
                # Check if max pages limit is reached (if max_pages is set and is not None)
                # Убираем проверку, так как page_range уже ограничен
                # if config.max_pages and isinstance(current_page, int) and current_page > config.max_pages:
                #     logger.info(f"Reached max_pages limit ({config.max_pages}). Stopping.")
                #     break

                # Construct page-specific run folder and URL
                page_run_folder = base_run_folder / f"page_{current_page}"
                page_run_folder.mkdir(parents=True, exist_ok=True)

                # Page-specific assets folder (within the page run folder)
                # Processors will save assets here via the AssetDownloaderAdapterForProcessors
                page_assets_dir = page_run_folder / "assets"
                page_assets_dir.mkdir(parents=True, exist_ok=True)

                # Construct URL based on page_num (or "init")
                # FIX: Use the base URL from subject_info, which should be constructed here
                base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}" # Construct base URL from subject_info
                if current_page == "init":
                    # Init page might be the base URL or base_url + "?page=init", depending on FIPI structure
                    # Let's assume init is just the base URL
                    page_url = base_url
                else:
                    page_url = f"{base_url}?page={current_page}" # Construct page URL based on base_url and page_num

                try:
                    # Scrape the page using PageScrapingService
                    # It will use HTMLBlockProcessingService internally to process blocks
                    # The HTMLBlockProcessingService applies the chain of IHTMLProcessor implementations
                    problems = await self.page_scraping_service.scrape_page(
                        url=page_url,
                        subject_info=subject_info,
                        base_url=base_url, # Pass the constructed base_url
                        timeout=config.timeout_seconds,
                        run_folder_page=page_run_folder, # Pass the page-specific run folder for asset storage
                        files_location_prefix=f"assets/" # Prefix for file paths generated by processors
                    )
                    found_count = len(problems)
                    total_found += found_count

                    if found_count == 0:
                        empty_page_count += 1
                        logger.info(f"Page {current_page} is empty. Empty page count: {empty_page_count}/{max_empty_pages}")
                        if empty_page_count >= max_empty_pages:
                            logger.info(f"Reached {max_empty_pages} consecutive empty pages. Stopping.")
                            break # Stop scraping if max consecutive empty pages reached
                    else:
                        empty_page_count = 0 # Reset counter if page is not empty

                    # Save problems from this page to the SHARED repository
                    saved_count = self._save_problems(problems, config.force_restart)
                    total_scraped_problems += saved_count

                    # Create page result object
                    page_result = {
                        "page_number": current_page,
                        "problems_found": found_count,
                        "problems_saved": saved_count,
                        "error": None
                    }
                    all_page_results.append(page_result)

                    logger.info(f"Scraped and saved {saved_count}/{found_count} problems from page {current_page} for {subject_info.official_name}")

                except Exception as e_page:
                    logger.error(f"Error scraping page {current_page} for subject {subject_info.official_name}: {e_page}", exc_info=True)
                    # Depending on requirements, decide whether to stop or continue
                    # For now, continue with other pages
                    page_result = {
                        "page_number": current_page,
                        "problems_found": 0,
                        "problems_saved": 0,
                        "error": str(e_page)
                    }
                    all_page_results.append(page_result)
                    errors.append(f"Page {current_page}: {e_page}")
                    # Optionally, increment empty page counter on error, or treat as non-empty
                    # For now, treat errors as non-empty to avoid stopping due to errors on one page
                    # empty_page_count = 0 # This would reset on any non-empty or error page
                    # Or, treat errors as potential empty pages if scraping is failing
                    # Let's treat errors as non-empty for now to continue scraping other pages
                    continue

            duration = datetime.now() - start_time
            success = total_scraped_problems > 0 # Consider successful if at least one problem was saved

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
            logger.info(f"Completed scraping for subject {subject_info.official_name}. Total problems saved: {total_scraped_problems}. Duration: {duration.total_seconds():.2f}s")
            return result

        except Exception as e:
            duration = datetime.now() - start_time
            logger.error(f"Critical error during scraping for subject {subject_info.official_name}: {e}", exc_info=True)
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

    def _save_problems(self, problems: List['Problem'], force_restart: bool) -> int:
        """
        Save a list of problems to the SHARED repository and return the count of successfully saved ones.
        Args:
            problems: List of Problem entities to save.
            force_restart: If True, existing problems with the same ID are updated.
        Returns:
            The number of problems successfully saved/updated.
        """
        saved_count = 0
        for problem in problems:
            try:
                # Use the repository's save method which handles upsert logic based on force_restart
                self.problem_repository.save(problem, force_restart=force_restart)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save problem {problem.problem_id}: {e}", exc_info=True)
                # Continue with other problems
        return saved_count

    def _create_page_result(self, page_number: int, scraped_count: int, saved_count: int, error: Optional[str] = None) -> Dict[str, any]:
        """
        Create a page result dictionary from scraped problems.
        Args:
            page_number: The number/identifier of the page.
            scraped_count: Number of problems scraped from the page.
            saved_count: Number of problems saved to the repository.
            error: Optional error message if scraping failed.
        Returns:
            A dictionary summarizing the results for the page.
        """
        return {
            "page_number": page_number,
            "problems_found": scraped_count,
            "problems_saved": saved_count,
            "error": error
        }

    async def _determine_last_page(self, proj_id: str) -> Optional[int]:
        """
        Determine the last page number from the pager element on the FIPI site.
        Args:
            proj_id: The FIPI project ID for the subject.
        Returns:
            The last page number as an integer, or None if it could not be determined.
        """
        # This logic might be moved to PageScrapingService or a dedicated service
        # For now, let's assume PageScrapingService has a method for this
        # or it's handled by calling scrape_page with a special flag/URL
        # Example placeholder logic:
        # initial_url = f"{base_url}/?page=1" # Get the first page
        # Use browser_service to get content and parse for pager
        # This is complex and might require its own service or method in PageScrapingService
        # For now, return a dummy value or implement the logic here
        # Let's assume we have a way to get the last page, perhaps by scraping the first page
        # and parsing the pagination element.
        # This is a placeholder - actual implementation depends on FIPI site structure.
        logger.warning("Determining last page is not fully implemented in UseCase. Delegating to PageScrapingService or external logic.")
        # Example: Scrape first page and parse pager (requires PageScrapingService modification)
        # first_page_content = await self.browser_service.get_page_content(f"{base_url}/?page=1")
        # soup = BeautifulSoup(first_page_content, 'html.parser')
        # pager = soup.find('div', class_='pager') # Adjust selector
        # if pager:
        #     links = pager.find_all('a', href=True)
        #     last_link = links[-1] if links else None
        #     if last_link:
        #         # Extract page number from href
        #         import re
        #         match = re.search(r'page=(\d+)', last_link['href'])
        #         if match:
        #             return int(match.group(1))
        # For now, return None to indicate it needs implementation
        return None # Placeholder - needs real implementation
