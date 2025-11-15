"""
Infrastructure adapter implementing domain interface for processing a single problem block from FIPI pages.

This module provides the `BlockProcessorAdapter` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for processing a single block
pair (header_container, qblock), including applying HTML processors, downloading
assets, extracting metadata, and preparing data for IProblemFactory.
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Tag
import asyncio
from datetime import datetime

from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем обновлённый интерфейс
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем новый интерфейс
from src.application.interfaces.factories.i_problem_factory import IProblemFactory # Импортируем интерфейс фабрики
from src.domain.models.problem import Problem # Импортируем доменную сущность
from src.application.value_objects.scraping.subject_info import SubjectInfo # Импортируем VO
# from processors.html import ( # Импорты процессоров HTML будут добавлены позже
#     ImageScriptProcessor,
#     FileLinkProcessor,
#     TaskInfoProcessor,
#     InputFieldRemover,
#     MathMLRemover,
#     UnwantedElementRemover
# )
# from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter # Импорт адаптера извлечения метаданных будет добавлен позже

logger = logging.getLogger(__name__)


class BlockProcessorAdapter(IHTMLProcessor):
    """
    Infrastructure adapter implementing domain interface for processing a single problem block from FIPI pages.
    
    It takes paired header and question blocks, applies a series of transformations
    (asset downloading, HTML cleaning), extracts metadata, and prepares structured
    data for the IProblemFactory.
    """

    def __init__(
        self,
        problem_factory: IProblemFactory,
        # html_processors: List[IHTMLProcessor], # Пока не добавляем список процессоров, используем встроенные или pipeline
        # metadata_extractor: HTMLMetadataExtractorAdapter, # Пока не добавляем как зависимость, инлайним логику или используем VO
    ):
        """
        Initializes the BlockProcessorAdapter with required services.

        Args:
            problem_factory: Service for creating domain problems (implements IProblemFactory)
            # html_processors: List of HTML processors to apply (implement IHTMLProcessor or similar interface) - NOT ADDED YET
            # metadata_extractor: Adapter for extracting metadata from headers - NOT ADDED YET
        """
        self.problem_factory = problem_factory
        # self.html_processors = html_processors # Пока не храним
        # self.metadata_extractor = metadata_extractor # Пока не храним

    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject_info: SubjectInfo,
        base_url: str,
        run_folder_page: Path,
        asset_downloader: IAssetDownloader, # Принимаем интерфейс
        files_location_prefix: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Processes a single block pair (header_container, qblock) into structured data.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject_info: The SubjectInfo object containing subject details.
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            asset_downloader: Service for downloading assets (implements IAssetDownloader).
            files_location_prefix: Prefix for file paths in the output.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing structured data from the processed block.
            This data is suitable for passing to IProblemFactory.
        """
        logger.debug(f"Starting processing of block {block_index} for subject '{subject_info.alias}'.")

        # --- 1. Combine header and question blocks (if needed for processing together) ---
        # For now, we'll process them separately for metadata and content
        # Create a new soup instance to hold the combined content for further processing
        combined_soup = BeautifulSoup('', 'html.parser')
        # Append the content of the qblock first
        combined_qblock = qblock.extract() # Extract from original soup to avoid duplication
        combined_soup.append(combined_qblock)

        # --- 2. Extract metadata (KES, KOS codes, task number) from header_container ---
        # This logic will be expanded using HTMLMetadataExtractorAdapter or similar
        # For now, let's simulate extraction
        metadata = self._extract_metadata_stub(header_container)
        kes_codes = metadata.get('kes_codes', [])
        kos_codes = metadata.get('kos_codes', [])
        task_number_from_header = metadata.get('task_number', None) # Извлекаем номер из заголовка, если возможно

        # --- 3. Apply HTML processing logic (STUBBED - NO REAL PROCESSORS YET) ---
        # This is where AssetProcessor-like logic would apply
        # We'll simulate the effect of processors that might download assets and modify HTML
        # In the future, we would iterate through self.html_processors or use an HTMLProcessingPipeline
        processed_html_str = str(combined_soup)
        all_proc_metadata = {}

        # Example: Simulate what ImageScriptProcessor might do
        # Find all img tags and potentially download them
        img_tags = combined_soup.find_all('img')
        downloaded_images = []
        for img_tag in img_tags:
            src = img_tag.get('src')
            if src:
                full_url = urljoin(base_url, src) # Construct full URL if src is relative
                # Construct destination path
                # Extract filename from URL
                from urllib.parse import urlparse
                parsed_url = urlparse(full_url)
                filename = Path(parsed_url.path).name
                if not filename:
                    # If no filename in path, generate one
                    filename = f"image_block_{block_index}_{len(downloaded_images)}.jpg" # Default extension
                dest_path = run_folder_page / "assets" / filename # Create assets subfolder
                dest_path.parent.mkdir(parents=True, exist_ok=True) # Ensure assets dir exists

                # Download using the injected IAssetDownloader
                try:
                    success = await asset_downloader.download(full_url, dest_path)
                    if success:
                        # Calculate relative path for the problem data
                        relative_path = dest_path.relative_to(run_folder_page)
                        downloaded_images.append(str(relative_path))
                        # Optionally, update the img src in processed_html_str to point to local file
                        # This is tricky with BeautifulSoup objects, so we'll handle it after string conversion if needed
                        # For now, just store the path
                    else:
                        logger.warning(f"Failed to download image {full_url} for block {block_index}.")
                except Exception as e:
                    logger.error(f"Error downloading image {full_url} for block {block_index}: {e}")

        # Example: Simulate what FileLinkProcessor might do
        # Find all links with specific classes/attributes indicating downloadable files
        file_link_selectors = ['.file-link', 'a[href$=".pdf"]', 'a[href$=".doc"]', 'a[href$=".zip"]'] # Example selectors
        downloaded_files = []
        for selector in file_link_selectors:
             file_links = combined_soup.select(selector)
             for link_tag in file_links:
                 href = link_tag.get('href')
                 if href:
                     full_url = urljoin(base_url, href)
                     from urllib.parse import urlparse
                     parsed_url = urlparse(full_url)
                     filename = Path(parsed_url.path).name
                     if not filename:
                         filename = f"file_block_{block_index}_{len(downloaded_files)}.{parsed_url.path.split('.')[-1] or 'dat'}"
                     dest_path = run_folder_page / "assets" / filename
                     dest_path.parent.mkdir(parents=True, exist_ok=True)

                     try:
                         success = await asset_downloader.download(full_url, dest_path)
                         if success:
                             relative_path = dest_path.relative_to(run_folder_page)
                             downloaded_files.append(str(relative_path))
                         else:
                             logger.warning(f"Failed to download file {full_url} for block {block_index}.")
                     except Exception as e:
                         logger.error(f"Error downloading file {full_url} for block {block_index}: {e}")

        # Update the processed_html_str after potential modifications (e.g., changing src/href)
        # For simplicity here, we don't modify the original soup's src/href, just store the local paths
        # A real processor would modify the soup and then str(soup) would reflect those changes.
        # We'll assume the stored paths in metadata are sufficient for the final Problem object.
        processed_html_str = str(combined_soup) # Still original, unless soup was modified during download logic above (it wasn't in this stub)

        all_proc_metadata.update({
            'images': downloaded_images,
            'files': downloaded_files
        })


        # --- 4. Prepare raw data for IProblemFactory ---
        # Extract the final processed text/content from the combined soup
        processed_text = combined_soup.get_text(separator=' ', strip=True)
        # Extract other relevant content like images, files paths from metadata gathered by processors
        extracted_images = all_proc_metadata.get('images', []) # From simulated ImageScriptProcessor
        extracted_files = all_proc_metadata.get('files', []) # From simulated FileLinkProcessor
        # Extract answer if present in qblock (often not visible, but sometimes possible)
        # This is a simple example, real extraction might be more complex
        # Example: Look for hidden inputs, specific spans, etc.
        answer_element = combined_soup.find('input', {'type': 'hidden', 'name': 'correct_answer'}) # Example selector
        if not answer_element:
            answer_element = combined_soup.find('span', class_='correct-answer') # Another example
        extracted_answer = answer_element.get('value') if answer_element else None
        if not extracted_answer:
             # Try to get text if it's a span
             extracted_answer = answer_element.get_text(strip=True) if answer_element else None


        # --- 5. Infer/extrapolate domain-specific attributes ---
        # This is where task_number inference, difficulty level estimation, etc. happen
        # These might be handled by services passed to PageScrapingService, not here
        # For now, we pass the extracted metadata and header info
        # PageScrapingService or ProblemFactory can use task_inferer/classifier
        # Let's prepare a raw data dict
        raw_data = {
            'problem_id': f"{subject_info.alias}_{block_index}_{hash(processed_text) % 1000000}", # Generate a unique ID
            'subject_name': subject_info.subject_name, # Use the full name from SubjectInfo
            'text': processed_text,
            'source_url': base_url, # The base URL of the page this block came from
            'answer': extracted_answer,
            'images': extracted_images,
            'files': extracted_files,
            'kes_codes': kes_codes,
            'kos_codes': kos_codes,
            'topics': kes_codes[:], # For DB compatibility, topics often map to kes_codes
            # 'difficulty_level': inferred_difficulty, # Would come from classifier/inferer
            # 'task_number': inferred_task_number or task_number_from_header, # Would come from inferer/classifier
            # 'exam_part': inferred_exam_part, # Would come from classifier/inferer
            'fipi_proj_id': subject_info.proj_id, # Link back to FIPI project
            # 'form_id': extracted_form_id, # Would be extracted similarly to answer
            # Add any other fields needed by Problem or IProblemFactory
            # Pass the metadata extracted from header for potential use in inference/classification
            'header_metadata': metadata,
            'block_index': block_index,
            'original_block_index': block_index # Preserve original index if needed for debugging/ordering
        }

        # --- 6. Return raw data for use by PageScrapingService/IProblemFactory ---
        # The PageScrapingService will take this raw_data, potentially enhance it
        # using task_inferer/classifier, and then call problem_factory.create_problem(raw_data)
        logger.debug(f"Finished processing block {block_index}. Extracted raw data keys: {list(raw_data.keys())}")
        return raw_data

    def _extract_metadata_stub(self, header_container: Tag) -> Dict[str, Any]:
        """
        STUBBED method to simulate extraction of metadata (KES, KOS, task number) from header_container.
        This will be replaced by logic using HTMLMetadataExtractorAdapter or similar.
        """
        # Example: Simulate finding KES codes like "КЭС: 1.1, 1.2"
        kes_codes = []
        kos_codes = []
        task_number = None
        # Find elements containing "КЭС" or "Кодификатор"
        kes_text_elements = header_container.find_all(string=re.compile(r"(КЭС|кодификатор)", re.IGNORECASE))
        for elem in kes_text_elements:
            parent = elem.parent
            text = parent.get_text()
            # Regex to find codes after КЭС/Kodifikator
            kes_match = re.search(r'(?:КЭС|кодификатор)[:\s]*([0-9.,\s-]+)', text, re.IGNORECASE)
            if kes_match:
                codes_str = kes_match.group(1)
                codes_list = [c.strip() for c in codes_str.split(',')]
                kes_codes.extend(codes_list)

        # Find elements containing "КОС" or "Требование"
        kos_text_elements = header_container.find_all(string=re.compile(r"(КОС|требование)", re.IGNORECASE))
        for elem in kos_text_elements:
            parent = elem.parent
            text = parent.get_text()
            # Regex to find codes after КОС/Trebovanie
            kos_match = re.search(r'(?:КОС|требование)[:\s]*([0-9.,\s-]+)', text, re.IGNORECASE)
            if kos_match:
                codes_str = kos_match.group(1)
                codes_list = [c.strip() for c in codes_str.split(',')]
                kos_codes.extend(codes_list)

        # Find task number
        task_text_elements = header_container.find_all(string=re.compile(r"(Задание|Task)\s+(\d+)", re.IGNORECASE))
        for elem in task_text_elements:
            match = re.search(r"(?:Задание|Task)\s+(\d+)", elem, re.IGNORECASE)
            if match:
                task_number = int(match.group(1))
                break # Take the first match

        return {
            'kes_codes': list(set(kes_codes)), # Remove duplicates
            'kos_codes': list(set(kos_codes)), # Remove duplicates
            'task_number': task_number
        }

