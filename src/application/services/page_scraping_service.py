"""
Application service for page scraping operations.

This service coordinates the scraping of individual pages, handling the interaction
between browser management (via IBrowserService), HTML processing (via IHTMLProcessor),
and data preparation for the domain layer (via IProblemFactory).
It now integrates IAssetDownloader for handling assets found during HTML processing.
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем обновлённый интерфейс
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем новый интерфейс
from src.application.interfaces.factories.i_problem_factory import IProblemFactory # Импортируем интерфейс фабрики
from src.domain.models.problem import Problem # Импортируем доменную сущность
from src.application.value_objects.scraping.subject_info import SubjectInfo # Импортируем VO

logger = logging.getLogger(__name__)

class PageScrapingService:
    """
    Application service for page scraping operations.
    
    Business Rules:
    - Coordinates the scraping of a single page
    - Handles browser management for page navigation via IBrowserService
    - Processes HTML content using IHTMLProcessor
    - Downloads assets using IAssetDownloader (coordinated by IHTMLProcessor)
    - Prepares data for domain entity creation using IProblemFactory
    - Manages file storage for downloaded assets
    - Provides progress reporting
    - Handles errors gracefully
    - Respects scraping configuration
    - Ensures data integrity
    """
    
    def __init__(
        self,
        browser_service: IBrowserService, # Using IBrowserService interface
        html_processor: IHTMLProcessor,  # Using IHTMLProcessor interface (e.g., BlockProcessorAdapter)
        asset_downloader: IAssetDownloader, # Adding IAssetDownloader dependency
        problem_factory: IProblemFactory, # Using IProblemFactory interface
    ):
        """
        Initialize page scraping service with required dependencies.
        
        Args:
            browser_service: Service for browser management (implements IBrowserService)
            html_processor: Service for processing HTML blocks (implements IHTMLProcessor)
            asset_downloader: Service for downloading assets (implements IAssetDownloader)
            problem_factory: Factory for creating domain problems (implements IProblemFactory)
        """
        self.browser_service = browser_service
        self.html_processor = html_processor
        self.asset_downloader = asset_downloader # Сохраняем
        self.problem_factory = problem_factory

    async def scrape_page(
        self,
        url: str,
        subject_info: SubjectInfo,
        base_url: str,
        timeout: int = 30,
        run_folder_page: Optional[Path] = None, # Folder for assets of *this* page
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
            files_location_prefix: Prefix for file paths in the output.

        Returns:
            A list of Problem entities extracted from the page.
        """
        logger.info(f"Scraping page: {url} for subject: {subject_info.official_name}")

        if run_folder_page is None:
            # If no specific folder is provided, use a default based on subject and URL hash or page number
            # For now, let's assume PageScrapingService receives the correct run_folder_page from ScrapeSubjectUseCase
            logger.warning(f"No run_folder_page provided for {url}. Assets might not be saved correctly.")
            run_folder_page = Path(".") # Fallback, but this is bad practice

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
        # Find all header containers (panels)
        header_containers = soup.find_all('div', class_='task-header-panel') # Adjust selector as needed
        # Find all question blocks (qblocks)
        qblocks = soup.find_all('div', class_='qblock') # Adjust selector as needed

        if len(header_containers) != len(qblocks):
            logger.warning(f"Mismatch between header panels ({len(header_containers)}) and qblocks ({len(qblocks)}) on page {url}. Attempting pairing by index.")
            # Handle mismatch - maybe log, pair by index up to min(len), or skip malformed pairs
            # For now, pair by index up to the shorter list
            pairs_to_process = min(len(header_containers), len(qblocks))
        else:
            pairs_to_process = len(header_containers)

        problems = []

        for i in range(pairs_to_process):
            header_container = header_containers[i]
            qblock = qblocks[i]

            try:
                # 3. Process the block using IHTMLProcessor
                # This returns raw data suitable for the IProblemFactory
                # Pass the newly injected IAssetDownloader
                raw_block_data = await self.html_processor.process_html_block(
                    header_container=header_container,
                    qblock=qblock,
                    block_index=i,
                    subject_info=subject_info,
                    base_url=base_url,
                    run_folder_page=run_folder_page,
                    asset_downloader=self.asset_downloader, # Pass the asset downloader
                    files_location_prefix=files_location_prefix
                )

                # 4. Create Problem entity using IProblemFactory
                # The factory receives the raw data and any context needed (e.g., subject_info)
                # Potentially, task_number inference, difficulty calculation happen inside the factory or are passed from here
                # For now, we assume the factory handles this based on raw data and potentially injected services
                # (e.g., task_inferer, task_classifier passed to factory's constructor)
                problem = self.problem_factory.create_problem(raw_block_data)
                problems.append(problem)

            except Exception as e:
                logger.error(f"Error processing block {i} on page {url}: {e}", exc_info=True)
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

