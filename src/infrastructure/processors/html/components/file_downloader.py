"""FileDownloader implementation"""
import asyncio
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
from src.domain.interfaces.html_processing.i_file_downloader import IFileDownloader

class FileDownloader(IFileDownloader):
    """Handles file downloading operations"""
    
    async def download_files(
        self,
        file_links: List[Tuple[str, str]],
        base_url: str,
        download_dir: Path,  # Теперь ожидает Path, а не str
        files_prefix: str,
        max_concurrent: int,
        asset_downloader
    ) -> List[str]:
        """
        Download multiple files concurrently
        """
        if not file_links:
            return []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        downloaded_files = []
        
        async def download_single(link_element, href, index):
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            filename = Path(parsed.path).name or f"file_{index}.dat"
            dest_path = download_dir / "assets" / filename
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                async with semaphore:
                    success = await asset_downloader.download(full_url, dest_path)
                if success:
                    relative_path = dest_path.relative_to(download_dir)
                    local_ref = str(relative_path).replace("\\", "/")
                    downloaded_files.append(local_ref)
            except Exception:
                pass
        
        tasks = [
            download_single(link, href, i)
            for i, (link, href) in enumerate(file_links)
        ]
        
        if tasks:
            await asyncio.gather(*tasks)
        
        return downloaded_files
