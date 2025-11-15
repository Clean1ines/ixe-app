"""
Application service for page scraping operations.

This service coordinates the scraping of individual pages, handling the interaction
between browser management (via IBrowserService) and converting results into
domain entities (via IProblemFactory).
It now integrates the concrete HTML processors from the infrastructure layer,
adapting the new IAssetDownloader to the old processor interface expectations via AssetDownloaderAdapter.
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем интерфейс
from src.application.interfaces.factories.i_problem_factory import IProblemFactory # Используем интерфейс фабрики
from src.domain.models.problem import Problem # Импортируем доменную сущность
from src.application.value_objects.scraping.subject_info import SubjectInfo # Импортируем VO

# Импортируем конкретные процессоры из инфраструктуры
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover
# Импортируем адаптер с правильным именем
from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter

logger = logging.getLogger(__name__)

class PageScrapingService:
    """
    Application service for page scraping operations.
    
    Business Rules:
    - Coordinates the scraping of a single page
    - Handles browser management for page navigation via IBrowserService
    - Processes HTML content using concrete infrastructure processors from ~/ixe/src/infrastructure/processors/html/
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
    ):
        """
        Initialize page scraping service with required dependencies.
        
        Args:
            browser_service: Service for browser management (implements IBrowserService)
            asset_downloader_impl: Concrete implementation of IAssetDownloader (e.g., HTTPXAssetDownloaderAdapter)
                                   This will be used by the AssetDownloaderAdapterForProcessors.
            problem_factory: Factory for creating domain problems (implements IProblemFactory)
        """
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl # Сохраняем IAssetDownloader impl
        self.problem_factory = problem_factory

        # Instantiate concrete processors from the new project structure (~/ixe)
        # These processors expect a 'downloader' object with a 'download(url, path, type)' interface (via adapter)
        self.image_processor = ImageScriptProcessor()
        self.file_processor = FileLinkProcessor()
        self.task_info_processor = TaskInfoProcessor()
        self.input_field_remover = InputFieldRemover()
        self.mathml_remover = MathMLRemover()
        self.unwanted_element_remover = UnwantedElementRemover()

        # Collect them in a list for sequential processing if needed
        # Define a sensible order (e.g., download assets first, then clean, then modify attributes)
        self.processors = [
            self.mathml_remover, # Remove MathML early
            self.unwanted_element_remover, # Remove unwanted elements early
            self.image_processor, # Download images and update src - requires downloader adapter
            self.file_processor, # Download files and update href - requires downloader adapter
            self.task_info_processor, # Update task info onclick
            self.input_field_remover, # Remove input fields last
        ]

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
            run_folder_page = Path(".") # Fallback, but this is bad practice if assets need per-page organization

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

        # 3. Process each block pair using the chain of CONCRETE processors from src.infrastructure.processors.html
        for i in range(pairs_to_process):
            header_container = header_containers[i]
            qblock = qblocks[i]

            try:
                # Prepare common kwargs for all processors for this *single block*, including the ADAPTER INSTANCE
                # The critical part: pass the ADAPTER instance where old processors expect 'downloader'
                processor_kwargs = {
                    'run_folder_page': run_folder_page, # Pass the specific run folder for this page's assets (if processors use it)
                    'downloader': asset_downloader_adapter_instance, # <-- KEY INTEGRATION POINT: Pass the ADAPTER INSTANCE
                    'base_url': base_url,
                    'files_location_prefix': files_location_prefix,
                    'subject': subject_info.subject_name, # Pass subject name string as expected by old processors
                    # Add other common context if needed by processors
                }

                # Apply processors sequentially to the *qblock* content (modifying it in-place or getting a new one back)
                # The old processors' process_html_block likely modifies the soup object in place or returns a new one.
                # They return a dict containing the *new* processed header/qblock tags and metadata.
                # Let's assume they return the modified tags.
                # Start with the original pair
                current_header = header_container
                current_qblock = qblock

                for processor in self.processors:
                    logger.debug(f"Applying processor {processor.__class__.__name__} to block {i} for subject {subject_info.alias}.")
                    try:
                        # Call the processor and get the potentially updated blocks and metadata
                        # CRITICAL: Pass the 'downloader' (adapter instance) via kwargs
                        processed_data = await processor.process_html_block(
                            header_container=current_header,
                            qblock=current_qblock,
                            block_index=i,
                            subject=subject_info.subject_name, # Pass subject name string
                            base_url=base_url,
                            **processor_kwargs # Pass common context including the 'downloader' adapter instance
                        )
                        # Update the containers with the ones returned by the processor
                        # This assumes the processor returns the modified blocks in the dict.
                        current_header = processed_data.get('header_container', current_header)
                        current_qblock = processed_data.get('qblock', current_qblock) # Update qblock with processed one

                        # Optionally, collect metadata from each processor if needed later
                        # e.g., downloaded_files.update(processed_data.get('downloaded_files', {}))
                        # e.g., downloaded_images.update(processed_data.get('downloaded_images', {}))

                    except Exception as e:
                        logger.error(f"Error applying processor {processor.__class__.__name__} to block {i}: {e}", exc_info=True)
                        # Depending on business rules, decide whether to skip this block or fail the whole page
                        # For now, let's log and continue with the *current* state of the block (before this processor failed)
                        # This means the block might be in a partially processed state when passed to the next processor or for data extraction.
                        # Or, we could break this inner loop and skip to the next page block pair.
                        # Let's continue processing with the current state for this block.
                        continue # Move to the next processor in the chain for this block

                # After all processors have run on the block pair (current_header, current_qblock)
                # The 'current_qblock' (and maybe 'current_header') now contains the *processed* HTML.
                # It should have local paths for assets, cleaned elements, updated task info, etc.

                # 4. Extract raw data from the *processed* HTML blocks
                # This replicates what the old HTMLMetadataExtractorAdapter did or would do based on *processed* HTML.
                # We need to parse the final 'current_qblock' and 'current_header' to get the raw data for the Problem entity.
                # This extraction might also be its own service/application component later.
                raw_problem_data = self._extract_raw_data_from_processed_blocks(
                    header_container=current_header,
                    qblock=current_qblock,
                    subject_info=subject_info,
                    source_url=url,
                    run_folder_page=run_folder_page # Pass run folder for potential use in extraction logic if needed later
                )

                # 5. Create Problem entity using IProblemFactory
                # The factory receives the raw data and any context needed (e.g., subject_info)
                # It uses the raw data to populate the Problem entity fields.
                problem = self.problem_factory.create_problem(raw_problem_data)
                problems.append(problem)

            except Exception as e:
                logger.error(f"Error processing block {i} on page {url}: {e}", exc_info=True)
                # Decide how to handle block-level errors - continue with other blocks, or fail the whole page
                # For now, log and continue processing other blocks
                continue # Skip this block and move to the next one

        logger.info(f"Scraped {len(problems)} problems from page: {url}")
        return problems

    def _extract_raw_data_from_processed_blocks(self, header_container: Tag, qblock: Tag, subject_info: SubjectInfo, source_url: str, run_folder_page: Path) -> Dict[str, Any]:
        """
        Extract raw data from the processed HTML blocks.

        Args:
            header_container: The processed header container BeautifulSoup Tag.
            qblock: The processed question block BeautifulSoup Tag.
            subject_info: The SubjectInfo object.
            source_url: The URL of the page where the blocks were found.
            run_folder_page: Path to the run folder for this page's assets (for potential use in extraction logic).

        Returns:
            A dictionary containing raw data suitable for IProblemFactory.create_problem.
        """
        import re # Import inside function if not used globally in file
        # Example extraction logic (this needs to be fleshed out based on actual HTML structure after processing)
        # This replicates what the old HTMLMetadataExtractorAdapter did or would do based on *processed* HTML.

        # Find the main text content *after* processors have run (e.g., images/files paths updated)
        text_content = qblock.get_text(separator=' ', strip=True)

        # Extract task number from header (example logic, adapt selectors after processing)
        task_number_text_elem = header_container.find(string=re.compile(r"Задание|Task", re.IGNORECASE))
        task_number = None
        if task_number_text_elem and task_number_text_elem.parent:
             match = re.search(r'(?:Задание|Task)\s+(\d+)', task_number_text_elem.parent.get_text(), re.IGNORECASE)
             if match:
                 try:
                     task_number = int(match.group(1))
                 except ValueError:
                     pass # If parsing fails, leave as None

        # Extract KES codes from header (example logic, adapt selectors after processing)
        kes_codes_text = ""
        kes_elem = header_container.find(string=re.compile(r"КЭС|кодификатор", re.IGNORECASE))
        if kes_elem and kes_elem.parent:
            kes_codes_text = kes_elem.parent.get_text()
        # Parse kes codes from text
        kes_codes = re.findall(r'(\d+(?:\.\d+)*)', kes_codes_text) # Simple regex, might need refinement

        # Extract KOS codes from header (example logic, adapt selectors after processing)
        kos_codes_text = ""
        kos_elem = header_container.find(string=re.compile(r"КОС|требование", re.IGNORECASE))
        if kos_elem and kos_elem.parent:
            kos_codes_text = kos_elem.parent.get_text()
        # Parse kos codes from text
        kos_codes = re.findall(r'(\d+(?:\.\d+)*)', kos_codes_text) # Simple regex, might need refinement

        # Extract answer (example - might not be visible, depends on page structure after processing)
        # Look for hidden inputs, specific spans, etc., that *might* have been identified by processors or are visible now
        # Processors like InputFieldRemover might have changed the structure.
        # Let's assume the answer *might* be in a specific tag/class left after processing or inferred differently.
        # For now, let's try a common pattern.
        answer_elem = qblock.find('input', {'type': 'hidden', 'name': 'correct_answer'}) # Example selector
        if not answer_elem:
            answer_elem = qblock.find('span', class_='correct-answer') # Another example, depends on how page is structured after processing
        answer = answer_elem.get('value') if answer_elem else None
        if not answer:
             # Try to get text if it's a span
             answer = answer_elem.get_text(strip=True) if answer_elem and hasattr(answer_elem, 'get_text') else None

        # Extract images and files paths (these should now be local paths like 'assets/filename.ext' after processing by ImageScriptProcessor/FileLinkProcessor)
        # Find img tags with src starting with 'assets/'
        images = [img['src'] for img in qblock.find_all('img', src=re.compile(r'^assets/'))]
        # Find a tags with href starting with 'assets/'
        files = [a['href'] for a in qblock.find_all('a', href=re.compile(r'^assets/'))]

        # Infer difficulty level based on task number (example logic, can be more sophisticated)
        # This logic might also be handled by a dedicated service later or inferred by a processor
        difficulty_level = "basic" if task_number and task_number <= 12 else "advanced" if task_number else None
        exam_part = "Part 1" if task_number and task_number <= 12 else "Part 2" if task_number else None

        # Construct the raw data dictionary
        # This dictionary maps the processed HTML data to the fields expected by Problem or IProblemFactory
        raw_data = {
            'problem_id': f"{subject_info.alias}_{i}_{hash(text_content) % 1000000}", # Generate a unique ID based on content hash and block index
            'subject_name': subject_info.subject_name, # Use the full name from SubjectInfo VO
            'text': text_content,
            'source_url': source_url, # The URL of the page this block came from
            'answer': answer,
            'images': images,
            'files': files,
            'kes_codes': kes_codes,
            'topics': kes_codes[:], # For DB compatibility, topics often map to kes_codes
            'kos_codes': kos_codes,
            'difficulty_level': difficulty_level,
            'task_number': task_number,
            'exam_part': exam_part,
            'fipi_proj_id': subject_info.proj_id, # Link back to FIPI project
            # Add other fields as needed by Problem or IProblemFactory
            # This is where data from processors (like downloaded file paths) is aggregated
        }

        return raw_data

    # Optional: Method to determine last page number from pager element on the page
    # This could also be a separate service or handled by ScrapeSubjectUseCase
    # async def determine_last_page(self, proj_id: str) -> Optional[int]:
    #     # Logic to scrape the initial page and parse the pager
    #     # Similar to how it was done in ScrapeSubjectUseCase before
    #     pass

