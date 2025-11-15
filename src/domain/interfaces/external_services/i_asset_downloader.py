"""
Domain interface for asset downloading operations.

This interface defines the contract for downloading external assets (e.g., images, files)
referenced in scraped HTML content, allowing the domain layer to remain independent
of the specific downloading implementation (e.g., httpx, requests, playwright).
"""
import abc
from pathlib import Path
from typing import Optional


class IAssetDownloader(abc.ABC):
    """
    Domain interface for downloading assets from the web.
    """

    @abc.abstractmethod
    async def download(self, asset_url: str, destination_path: Path) -> bool:
        """
        Download an asset from the web and save it to a local destination.

        Args:
            asset_url: The full URL of the asset to download.
            destination_path: The local path where the asset should be saved.

        Returns:
            True if the download was successful, False otherwise.
        """
        pass

    @abc.abstractmethod
    async def download_bytes(self, asset_url: str) -> Optional[bytes]:
        """
        Download an asset from the web and return its content as bytes.

        Args:
            asset_url: The full URL of the asset to download.

        Returns:
            The content of the asset as bytes if successful, otherwise None.
        """
        pass
