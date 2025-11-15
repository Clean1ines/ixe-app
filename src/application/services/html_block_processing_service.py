"""
Application service for processing individual HTML blocks (header_container, qblock pairs).

This service coordinates the processing of a single HTML block, applying a chain of
concrete HTML processors from the infrastructure layer, adapting the new IAssetDownloader,
and finally creating a Problem entity using IProblemFactory.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import Tag
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

logger = logging.getLogger(__name__)

class HTMLBlockProcessingService:
    """
    Application service for processing individual HTML blocks.
    
    Business Rules:
    - Processes a single HTML block pair (header_container, qblock)
    - Applies a chain of concrete infrastructure processors
    - Adapts new IAssetDownloader to old processor interface expectations via an adapter passed in context
    - Converts processed data into a domain entity using IProblemFactory
    - Handles errors gracefully during processing by individual processors
    - Returns a single Problem entity or None if processing fails critically
    """

    def __init__(
        self,
        asset_downloader_impl: IAssetDownloader, # NEW DEPENDENCY: Concrete IAssetDownloader implementation
        problem_factory: IProblemFactory, # Using IProblemFactory interface
        # Instantiate concrete processors from the new project structure (~/ixe)
        # These processors expect a 'downloader' object with a 'download(url, path, type)' interface (via adapter passed in context)
        image_processor: ImageScriptProcessor = None,
        file_processor: FileLinkProcessor = None,
        task_info_processor: TaskInfoProcessor = None,
        input_field_remover: InputFieldRemover = None,
        mathml_remover: MathMLRemover = None,
        unwanted_element_remover: UnwantedElementRemover = None,
    ):
        """
        Initialize block processing service with required dependencies and concrete processors.
        
        Args:
            asset_downloader_impl: Concrete implementation of IAssetDownloader (e.g., HTTPXAssetDownloaderAdapter)
                                   This will be used by the AssetDownloaderAdapterForProcessors passed via context.
            problem_factory: Factory for creating domain problems (implements IProblemFactory)
            image_processor: Concrete processor for image scripts and tags (default: create instance)
            file_processor: Concrete processor for file links (default: create instance)
            task_info_processor: Concrete processor for task info buttons (default: create instance)
            input_field_remover: Concrete processor for removing input fields (default: create instance)
            mathml_remover: Concrete processor for removing MathML (default: create instance)
            unwanted_element_remover: Concrete processor for removing unwanted elements (default: create instance)
        """
        self.asset_downloader_impl = asset_downloader_impl # Сохраняем IAssetDownloader impl
        self.problem_factory = problem_factory

        # Instantiate or use provided concrete processors
        self.image_processor = image_processor or ImageScriptProcessor()
        self.file_processor = file_processor or FileLinkProcessor()
        self.task_info_processor = task_info_processor or TaskInfoProcessor()
        self.input_field_remover = input_field_remover or InputFieldRemover()
        self.mathml_remover = mathml_remover or MathMLRemover()
        self.unwanted_element_remover = unwanted_element_remover or UnwantedElementRemover()

        # Define the order in which processors are applied
        # Order matters: e.g., download assets first, then clean, then modify attributes
        self.processors = [
            self.mathml_remover, # Remove MathML early
            self.unwanted_element_remover, # Remove unwanted elements early
            self.image_processor, # Download images and update src - requires downloader adapter from context
            self.file_processor, # Download files and update href - requires downloader adapter from context
            self.task_info_processor, # Update task info onclick
            self.input_field_remover, # Remove input fields last
        ]

    async def process_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        context: Dict[str, Any], # Contains run_folder_page, downloader (adapter), base_url, etc.
    ) -> Optional[Problem]: # Возвращает одну Problem или None
        """
        Process a single HTML block pair and return a Problem entity.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            context: Dictionary containing processing context like run_folder_page, asset_downloader_adapter_instance, base_url, etc.

        Returns:
            A Problem entity created from the processed block, or None if processing fails critically.
        """
        logger.debug(f"Processing block {block_index} for subject {context['subject_info'].official_name} using HTMLBlockProcessingService.")

        # Prepare common kwargs for all processors for this *single block*, including the ADAPTER INSTANCE passed in context
        # The critical part: pass the ADAPTER instance where old processors expect 'downloader'
        processor_kwargs = context.copy() # Copy the context to pass to processors
        # Ensure the 'downloader' key in kwargs points to the adapter instance
        # This assumes context['downloader'] is the AssetDownloaderAdapter instance
        # processor_kwargs.update(context) # This would overwrite, but context is the base

        # Start with the original pair
        current_header = header_container
        current_qblock = qblock

        # Apply processors sequentially to the *qblock* content
        for processor in self.processors:
            logger.debug(f"Applying processor {processor.__class__.__name__} to block {block_index} for subject {context['subject_info'].alias}.")
            try:
                # Call the processor and get the potentially updated blocks and metadata
                # CRITICAL: Pass the context (including 'downloader' adapter instance) via kwargs
                processed_data = await processor.process_html_block(
                    header_container=current_header,
                    qblock=current_qblock,
                    block_index=block_index,
                    subject=context['subject_info'].subject_name, # Pass subject name string from VO in context
                    base_url=context['base_url'],
                    **processor_kwargs # Pass the common context including the 'downloader' adapter instance
                )
                # Update the containers with the ones returned by the processor
                # This assumes the processor returns the modified blocks in the dict.
                current_header = processed_data.get('header_container', current_header)
                current_qblock = processed_data.get('qblock', current_qblock) # Update qblock with processed one

                # Optionally, collect metadata from each processor if needed later
                # e.g., downloaded_files.update(processed_data.get('downloaded_files', {}))
                # e.g., downloaded_images.update(processed_data.get('downloaded_images', {}))

            except Exception as e:
                logger.error(f"Error applying processor {processor.__class__.__name__} to block {block_index}: {e}", exc_info=True)
                # Depending on business rules, decide whether to skip this block or fail the whole page
                # For now, let's log and return None, allowing PageScrapingService to continue with other blocks
                return None # Indicate failure for this specific block

        # After all processors have run on the block pair (current_header, current_qblock)
        # The 'current_qblock' (and maybe 'current_header') now contains the *processed* HTML.
        # It should have local paths for assets, cleaned elements, updated task info, etc.

        # Extract raw data from the *processed* HTML blocks
        # This replicates what the old HTMLMetadataExtractorAdapter did or would do based on *processed* HTML.
        # We need to parse the final 'current_qblock' and 'current_header' to get the raw data for the Problem entity.
        # This extraction might also be its own service/application component later.
        # For now, let's assume this service also handles this final extraction step before creating the Problem.
        raw_problem_data = self._extract_raw_data_from_processed_blocks(
            header_container=current_header,
            qblock=current_qblock,
            subject_info=context['subject_info'],
            source_url=context.get('source_url', 'N/A'), # URL страницы, где был блок
            run_folder_page=context.get('run_folder_page', Path('.')) # Передаём run_folder_page для потенциального использования
        )

        # Create Problem entity using IProblemFactory
        # The factory receives the raw data and any context needed (e.g., subject_info)
        # It uses the raw data to populate the Problem entity fields.
        try:
            problem = self.problem_factory.create_problem(raw_problem_data)
            return problem
        except Exception as e:
            logger.error(f"Error creating Problem entity from raw data for block {block_index}: {e}", exc_info=True)
            # If factory creation fails, we also return None
            return None

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
            'problem_id': f"{subject_info.alias}_{block_index}_{hash(text_content) % 1000000}", # Generate a unique ID based on content hash and block index
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

