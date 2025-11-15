"""
Application service for page scraping operations.
This service coordinates the scraping of individual pages, handling the interaction
between browser management (via IBrowserService) and converting results into
domain entities (via IProblemFactory).
It now integrates HTMLBlockProcessingService to handle the processing of individual blocks,
which in turn applies the chain of IHTMLProcessor implementations.
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем интерфейс
from src.application.interfaces.factories.i_problem_factory import IProblemFactory # Используем интерфейс фабрики
from src.domain.models.problem import Problem # Импортируем доменную сущность
from src.application.value_objects.scraping.subject_info import SubjectInfo # Импортируем VO
# Импортируем HTMLBlockProcessingService
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
# Импортируем адаптер
from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter
logger = logging.getLogger(__name__)
class PageScrapingService:
    """
    Application service for page scraping operations.
    Business Rules:
    - Coordinates the scraping of a single page
    - Handles browser management for page navigation via IBrowserService
    - Processes HTML content by delegating block processing to HTMLBlockProcessingService
    - HTMLBlockProcessingService applies a chain of IHTMLProcessor implementations
    - Adapts new IAssetDownloader to old processor interface expectations via AssetDownloaderAdapter
    - Converts processed data into domain entities using IProblemFactory
    - Manages file storage for downloaded assets via the shared IAssetDownloader (through the adapter)
    - Provides progress reporting
    - Handles errors gracefully
    - Respects scraping configuration
    - Ensures data integrity in the shared database
    """
    def __init__(
        self,
        browser_service: IBrowserService, # Using IBrowserService interface
        asset_downloader_impl: IAssetDownloader, # NEW DEPENDENCY: Concrete IAssetDownloader implementation
        problem_factory: IProblemFactory, # Using IProblemFactory interface
        html_block_processing_service: HTMLBlockProcessingService, # NEW DEPENDENCY: Service for block processing
    ):
        """
        Initialize page scraping service with required dependencies.
        Args:
            browser_service: Service for browser management (implements IBrowserService)
            asset_downloader_impl: Concrete implementation of IAssetDownloader (e.g., HTTPXAssetDownloaderAdapter)
                                   This will be used by the AssetDownloaderAdapterForProcessors.
            problem_factory: Factory for creating domain problems (implements IProblemFactory)
            html_block_processing_service: Service for processing individual HTML blocks (implements the processor chain)
        """
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl # Сохраняем IAssetDownloader impl
        self.problem_factory = problem_factory
        self.html_block_processing_service = html_block_processing_service # Сохраняем сервис обработки блоков
    async def scrape_page(
        self,
        url: str,
        subject_info: SubjectInfo,
        base_url: str,
        timeout: int = 30,
        run_folder_page: Optional[Path] = None, # Folder for assets of *this* page run (passed from UseCase)
        files_location_prefix: str = ""
    ) -> List[Problem]:
        """
        Scrape a single page and return Problem entities.
        Args:
            url: The URL of the page to scrape.
            subject_info: The SubjectInfo object containing subject details.
            base_url: The base URL of the scraped site (e.g., https://ege.fipi.ru/bank/{proj_id}).
            timeout: Timeout for browser operations.
            run_folder_page: Optional path to the run folder for this page's assets.
                             Processors will use this via the adapter if they save files.
            files_location_prefix: Prefix for file paths in the output (used by processors via adapter).
        Returns:
            A list of Problem entities extracted from the page.
        """
        logger.info(f"Scraping page: {url} for subject: {subject_info.official_name}")
        if run_folder_page is None:
            # If no specific folder is provided, PageScrapingService might decide on a default
            # based on subject and page number, or rely on the AssetDownloaderAdapterForProcessors's default.
            # For now, let's assume PageScrapingService receives the correct run_folder_page from ScrapeSubjectUseCase
            logger.warning(f"No run_folder_page provided for {url}. Asset saving might not be organized per page if processors rely on it.")
            run_folder_page = Path(".")
        # --- CREATE ADAPTER INSTANCE FOR OLD PROCESSORS ---
        # This adapter instance bridges the NEW IAssetDownloader impl and the OLD interface expected by processors.
        # It's created per page run (or per block run within a page) to potentially use a specific run_folder_page for asset storage.
        # Creating a new adapter instance per call ensures isolation of context (like run_folder_page) for that specific scraping task.
        asset_downloader_adapter_instance = AssetDownloaderAdapter(
            asset_downloader_impl=self.asset_downloader_impl, # Pass the IAssetDownloader implementation we injected
            default_assets_dir=run_folder_page / "assets" # Use assets subfolder within the page's run folder
        )
        # --- END ADAPTER CREATION ---
        # 1. Get page content using IBrowserService
        try:
            page_content = await self.browser_service.get_page_content(url, timeout)
        except Exception as e:
            logger.error(f"Failed to get page content from {url}: {e}", exc_info=True)
            # Decide how to handle the error - re-raise, return empty list, or return list with error marker
            # For now, re-raise to let the caller (ScrapeSubjectUseCase) handle it
            raise
        # 2. Parse HTML content to find problem blocks (header_container and qblock pairs)
        soup = BeautifulSoup(page_content, 'html.parser')
        # Find all header containers (panels) - adjust selectors based on actual HTML structure
        header_containers = soup.find_all('div', class_='task-header-panel') # Example selector
        # Find all question blocks (qblocks) - adjust selectors based on actual HTML structure
        qblocks = soup.find_all('div', class_='qblock') # Example selector
        if len(header_containers) != len(qblocks):
            logger.warning(f"Mismatch between header panels ({len(header_containers)}) and qblocks ({len(qblocks)}) on page {url}. Attempting pairing by index.")
            # Handle mismatch - maybe log, pair by index up to min(len), or skip malformed pairs
            # For now, pair by index up to the shorter list
            pairs_to_process = min(len(header_containers), len(qblocks))
        else:
            pairs_to_process = len(header_containers)
        problems = []
        # 3. Process each block pair using HTMLBlockProcessingService
        for i in range(pairs_to_process):
            header_container = header_containers[i]
            qblock = qblocks[i]
            try:
                # Prepare common context for HTMLBlockProcessingService
                # This includes the adapter instance, run folder, base URL, etc.
                processing_context = {
                    'run_folder_page': run_folder_page, # Pass the specific run folder for this page's assets (if processors use it)
                    'downloader': asset_downloader_adapter_instance, # <-- KEY INTEGRATION POINT: Pass the ADAPTER INSTANCE
                    'base_url': base_url,
                    'files_location_prefix': files_location_prefix,
                    'subject_info': subject_info, # Pass SubjectInfo VO
                    'source_url': url, # Pass the source URL for the block
                    # Add other common context if needed by processors
                }
                # Delegate the processing of this single block pair to HTMLBlockProcessingService
                # It will handle applying the processor chain and creating the Problem entity
                problem = await self.html_block_processing_service.process_block(
                    header_container=header_container,
                    qblock=qblock,
                    block_index=i,
                    context=processing_context
                )
                if problem is not None: # Only add if processing was successful
                    problems.append(problem)
            except Exception as e:
                logger.error(f"Error processing block {i} on page {url} using HTMLBlockProcessingService: {e}", exc_info=True)
                # Decide how to handle block-level errors - continue with other blocks, or fail the whole page
                # For now, log and continue processing other blocks
                continue # Skip this block and move to the next one
        logger.info(f"Scraped {len(problems)} problems from page: {url}")
        return problems
    # Optional: Method to determine last page number from pager element on the page
    # This could also be a separate service or handled by ScrapeSubjectUseCase
    # async def determine_last_page(self, proj_id: str) -> Optional[int]:
    #     # Logic to scrape the initial page and parse the pager
    #     # Similar to how it was done in ScrapeSubjectUseCase before
    #     pass
