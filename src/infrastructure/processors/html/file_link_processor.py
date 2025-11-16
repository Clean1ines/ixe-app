"""
Infrastructure adapter implementing domain interface for processing file links in HTML blocks.

This module provides the `FileLinkProcessor` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for processing file download links
(both direct and via JavaScript) within a single problem block pair (header_container, qblock),
using an injected AssetDownloader instance.
"""
import logging
import re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, Any
# from utils.downloader import AssetDownloader # УДАЛЯЕМ ЭТОТ ИМПОРТ
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем правильный интерфейс

logger = logging.getLogger(__name__)

class FileLinkProcessor(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for file link processing.
    
    Business Rules:
    - Processes 'window.open' JavaScript calls for files
    - Processes direct file links (e.g., .pdf, .zip)
    - Downloads files using the injected AssetDownloader (via adapter)
    - Updates href attributes to point to local paths
    - Logs errors during download gracefully
    - Returns structured data including local file paths
    """

    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str, # Use subject name string
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data related to files.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics"). This is a string.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            **kwargs: Additional keyword arguments (e.g., 'run_folder_page', 'downloader').

        Returns:
            A dictionary containing processed content and metadata about downloaded files.
            Example: {
                "header_container": updated_header_container,
                "qblock": updated_qblock,
                "block_index": int,
                "subject": str, # subject_info.subject_name
                "base_url": str,
                "downloaded_files": { "original_url1": "local_path1", ... }
            }
        """
        logger.debug(f"Processing file links for block {block_index} in subject {subject}.")

        # Extract context parameters from kwargs
        run_folder_page = kwargs.get('run_folder_page')
        # ИСПОЛЬЗУЕМ 'downloader', который должен быть экземпляром AssetDownloaderAdapterForProcessors
        downloader_instance = kwargs.get('downloader') # Это будет AssetDownloaderAdapterForProcessors instance
        files_location_prefix = kwargs.get('files_location_prefix', '')
        # subject_name = kwargs.get('subject', subject_info.subject_name) # Используем переданный subject_name или из VO
        # subject уже передан как строка

        if downloader_instance is None:
            raise ValueError("AssetDownloader adapter instance must be provided in context via 'downloader' kwarg")

        # Create a soup instance from the qblock content to process it
        qblock_soup = BeautifulSoup(str(qblock), 'html.parser')

        assets_dir = run_folder_page / "assets" if run_folder_page else Path("assets")
        downloaded_files = {}

        # --- 1. Process window.open javascript links ---
        for a in qblock_soup.find_all('a', href=re.compile(r"^javascript:")):
            href = a['href']
            match = re.search(r"window\.open$$'([^']*)'", href)
            if match:
                file_url = match.group(1).lstrip('../')
                # Construct full URL if file_url is relative
                full_file_url = urljoin(base_url, file_url) if base_url else file_url
                try:
                    # ИСПОЛЬЗУЕМ метод download у адаптера
                    local_path = await downloader_instance.download(full_file_url, assets_dir, asset_type='file')
                    if local_path:
                        a['href'] = f"assets/{local_path.name}"
                        downloaded_files[full_file_url] = f"assets/{local_path.name}"
                        logger.info(f"Downloaded and updated JS file link: {full_file_url} -> assets/{local_path.name}")
                    else:
                        logger.warning(f"Failed to download file from JS link: {full_file_url}")
                except Exception as e:
                    logger.error(f"Error downloading file from JS link {full_file_url}: {e}")

        # --- 2. Process direct file links ---
        file_extensions = ('.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.csv')
        for a in qblock_soup.find_all('a', href=re.compile(r"\.(pdf|zip|doc|docx|xls|xlsx|ppt|pptx|txt|rtf|csv)$", re.IGNORECASE)):
            href = a['href']
            file_url = href.lstrip('../')
            # Construct full URL if file_url is relative
            full_file_url = urljoin(base_url, file_url) if base_url else file_url
            try:
                # ИСПОЛЬЗУЕМ метод download у адаптера
                local_path = await downloader_instance.download(full_file_url, assets_dir, asset_type='file')
                if local_path:
                    # Use the correct path structure: assets/filename.ext
                    relative_path = f"assets/{local_path.name}"
                    a['href'] = relative_path
                    downloaded_files[full_file_url] = relative_path
                    logger.info(f"Downloaded and updated direct file link: {full_file_url} -> {relative_path}")
                else:
                    logger.warning(f"Failed to download file from direct link: {full_file_url}")
            except Exception as e:
                logger.error(f"Error downloading file from direct link {full_file_url}: {e}")

        # Update the qblock with processed content
        processed_qblock = qblock_soup.find('div', class_='qblock') or qblock_soup.find('div')

        # Return the processed block data and metadata
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': processed_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject, # Use the string subject
            'base_url': base_url,
            'downloaded_files': downloaded_files # Include metadata
        }
