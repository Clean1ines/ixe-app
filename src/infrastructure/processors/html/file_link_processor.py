"""Refactored FileLinkProcessor with separated concerns"""
import logging
from pathlib import Path
from typing import Dict, Any
from src.infrastructure.processors.html.components.file_link_extractor import FileLinkExtractor
from src.infrastructure.processors.html.components.file_downloader import FileDownloader

logger = logging.getLogger(__name__)

# ИСПРАВЛЕНО: Класс переименован с FileLinkProcessorRefactored на FileLinkProcessor
class FileLinkProcessor:
    """
    Refactored FileLinkProcessor with separated concerns
    Complexity reduced from C (16) to A (<10)
    """
    
    def __init__(self):
        self.extractor = FileLinkExtractor()
        self.downloader = FileDownloader()
    
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process file links with separated concerns
        """
        from bs4 import BeautifulSoup
        
        body_html = raw_data.get("body_html", "") or ""
        base_url = context.get("base_url", "https://fipi.ru")
        run_folder = Path(context.get("run_folder_page", Path(".")))
        files_prefix = context.get("files_location_prefix", "")
        downloader = context.get("downloader") or context.get("asset_downloader")
        
        if not downloader:
            logger.warning("No downloader available for file links")
            return raw_data
        
        # Extract file links
        soup = BeautifulSoup(body_html, "html.parser")
        file_links = self.extractor.extract_file_links(soup)
        
        if not file_links:
            return raw_data
        
        # Download files
        file_links_local = raw_data.get("files", [])
        downloaded_files = await self.downloader.download_files(
            file_links=file_links,
            base_url=base_url,
            download_dir=run_folder,
            files_prefix=files_prefix,
            max_concurrent=6,
            asset_downloader=downloader
        )
        
        # Update HTML and file list
        for link_element, _ in file_links:
            for local_file in downloaded_files:
                if local_file not in file_links_local:
                    file_links_local.append(local_file)
        
        raw_data["body_html"] = str(soup)
        raw_data["files"] = file_links_local
        
        return raw_data
