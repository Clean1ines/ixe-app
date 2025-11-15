"""
Infrastructure adapter to make IAssetDownloader compatible with the old processor interface.

This adapter wraps the new IAssetDownloader implementation and exposes the 'download(url, path, type)' method
signature expected by the legacy HTML processors from ~/iXe.
"""
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import os
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем интерфейс

logger = logging.getLogger(__name__)

class AssetDownloaderAdapter:
    """
    Adapts IAssetDownloader to the old 'downloader_instance.download(url, path, type)' interface.
    Used to integrate legacy HTML processors from ~/iXe with the new IAssetDownloader infrastructure in ~/ixe.
    """

    def __init__(self, asset_downloader_impl: IAssetDownloader, default_assets_dir: Path):
        """
        Initialize the adapter.

        Args:
            asset_downloader_impl: The concrete implementation of IAssetDownloader
                                   (e.g., HTTPXAssetDownloaderAdapter).
            default_assets_dir: The default directory where assets should be saved.
        """
        self._impl = asset_downloader_impl
        self._default_assets_dir = default_assets_dir

    async def download(self, asset_url: str, save_dir: Optional[Path] = None, asset_type: str = 'file') -> Optional[Path]:
        """
        Download an asset from the web and save it to a local destination.
        This method mimics the interface expected by the old processors.

        Args:
            asset_url: The full URL of the asset to download.
            save_dir: The local directory where the asset should be saved. Uses default if not provided.
            asset_type: The type of asset (e.g., 'image', 'file'). Can be used for naming or categorization.

        Returns:
            The local Path object of the saved file if successful, otherwise None.
        """
        if save_dir is None:
            save_dir = self._default_assets_dir

        # Determine filename from URL or use a hash-based name
        parsed_url = urlparse(asset_url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            # If no filename in path, generate one based on URL hash and type
            import hashlib
            hash_suffix = hashlib.md5(asset_url.encode()).hexdigest()[:8]
            extension_map = {'image': '.jpg', 'file': '.dat', 'pdf': '.pdf', 'zip': '.zip'} # Basic mapping
            ext = extension_map.get(asset_type, '.dat')
            filename = f"{asset_type}_{hash_suffix}{ext}"

        full_path = save_dir / filename
        save_dir.mkdir(parents=True, exist_ok=True) # Ensure parent directory exists

        try:
            # Use the new IAssetDownloader implementation's download method
            # Assuming the impl has async def download(url: str, destination: Path) -> bool
            success = await self._impl.download(asset_url, full_path)
            if success:
                return full_path # Return the local path
            else:
                logger.warning(f"Failed to download asset from {asset_url} using adapter.")
                return None
        except Exception as e:
            # Log the error if a logger is available
            logger.error(f"Error downloading asset {asset_url} using adapter: {e}")
            return None

    # If old processors expect other methods like 'download_bytes', add them here
    # async def download_bytes(self, asset_url: str) -> Optional[bytes]:
    #     # Similar adaptation for bytes download using self._impl
    #     pass

