"""Interface for file downloading"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

class IFileDownloader(ABC):
    """Handles file downloading operations"""
    
    @abstractmethod
    async def download_files(
        self,
        file_links: List[Tuple[str, str]],
        base_url: str,
        download_dir: Path,
        files_prefix: str,
        max_concurrent: int
    ) -> List[str]:
        """
        Download multiple files concurrently
        
        Args:
            file_links: List of (link_element, href) tuples
            base_url: Base URL for resolving relative links
            download_dir: Directory to save files
            files_prefix: Prefix for file paths
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            List of local file paths
        """
        pass
