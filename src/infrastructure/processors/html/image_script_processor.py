"""
Infrastructure adapter implementing domain interface for processing image scripts and tags in HTML blocks.

This module provides the `ImageScriptProcessor` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for processing image-related
scripts (e.g., ShowPicture) and direct <img> tags within a single problem block pair
(header_container, qblock), using an injected AssetDownloader instance.
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

class ImageScriptProcessor(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for image script processing.
    
    Business Rules:
    - Processes 'ShowPicture' JavaScript calls
    - Processes direct <img> tags
    - Downloads images using the injected AssetDownloader (via adapter)
    - Updates src attributes to point to local paths
    - Logs errors during download gracefully
    - Returns structured data including local image paths
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
        Process a single HTML block pair and return structured data related to images.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics"). This is a string.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            **kwargs: Additional keyword arguments (e.g., 'run_folder_page', 'downloader').

        Returns:
            A dictionary containing processed content and metadata about downloaded images.
            Example: {
                "header_container": updated_header_container,
                "qblock": updated_qblock,
                "block_index": int,
                "subject": str, # subject_info.subject_name
                "base_url": str,
                "downloaded_images": { "original_url1": "local_path1", ... }
            }
        """
        logger.debug(f"Processing images for block {block_index} in subject {subject}.")

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
        downloaded_images = {}

        # --- 1. Process ShowPicture scripts ---
        for script in qblock_soup.find_all('script', string=re.compile(r"ShowPicture$$'[^']*'$$")):
            match = re.search(r"ShowPicture$$'([^']*)'$$", script.string)
            if match:
                img_url = match.group(1)
                # Construct full URL if img_url is relative
                full_img_url = urljoin(base_url, img_url) if base_url else img_url
                try:
                    # ИСПОЛЬЗУЕМ метод download у адаптера
                    local_path = await downloader_instance.download(full_img_url, assets_dir, asset_type='image')
                    if local_path:
                        img_tag = qblock_soup.new_tag('img', src=f"assets/{local_path.name}")
                        script.replace_with(img_tag)
                        downloaded_images[full_img_url] = f"assets/{local_path.name}"
                        logger.info(f"Downloaded and replaced ShowPicture image: {full_img_url} -> assets/{local_path.name}")
                    else:
                        logger.warning(f"Failed to download image from ShowPicture script: {full_img_url}")
                except Exception as e:
                    logger.error(f"Error downloading image from ShowPicture script {full_img_url}: {e}")

        # --- 2. Process direct <img> tags ---
        for img_tag in qblock_soup.find_all('img', src=True):
            img_src = img_tag['src']
            # Skip if already processed (e.g., already points to local assets/)
            if img_src.startswith('assets/'):
                logger.debug(f"Skipping already processed image: {img_src}")
                continue

            # Construct full URL if img_src is relative
            full_img_url = urljoin(base_url, img_src) if base_url else img_url

            try:
                # ИСПОЛЬЗУЕМ метод download у адаптера
                local_path = await downloader_instance.download(full_img_url, assets_dir, asset_type='image')
                if local_path:
                    # Use the correct path structure: assets/filename.ext
                    relative_path = f"assets/{local_path.name}"
                    img_tag['src'] = relative_path
                    downloaded_images[full_img_url] = relative_path
                    logger.info(f"Downloaded and updated img tag: {full_img_url} -> {relative_path}")
                else:
                    logger.warning(f"Failed to download image from img tag: {full_img_url}")
            except Exception as e:
                logger.error(f"Error downloading image from img tag {full_img_url}: {e}")

        # Update the qblock with processed content
        processed_qblock = qblock_soup.find('div', class_='qblock') or qblock_soup.find('div')

        # Return the processed block data and metadata
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': processed_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject, # Use the string subject
            'base_url': base_url,
            'downloaded_images': downloaded_images # Include metadata
        }
