"""Tests for FileDownloader component"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock
from src.infrastructure.processors.html.components.file_downloader import FileDownloader

class TestFileDownloader:
    """Test suite for FileDownloader"""
    
    @pytest.fixture
    def downloader(self):
        return FileDownloader()
    
    @pytest.mark.asyncio
    async def test_download_files_empty_list(self, downloader):
        """Test downloading with empty file list"""
        mock_downloader = AsyncMock()
        file_links = []
        
        result = await downloader.download_files(
            file_links=file_links,
            base_url="https://example.com",
            download_dir=Path("/tmp"),  # Исправлено: Path вместо str
            files_prefix="assets/",
            max_concurrent=3,
            asset_downloader=mock_downloader
        )
        
        assert result == []
        mock_downloader.download.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_download_single_file(self, downloader):
        """Test downloading single file"""
        mock_downloader = AsyncMock()
        mock_downloader.download.return_value = True
        file_links = [("<a>link</a>", "file.pdf")]
        
        result = await downloader.download_files(
            file_links=file_links,
            base_url="https://example.com",
            download_dir=Path("/tmp"),  # Исправлено: Path вместо str
            files_prefix="assets/",
            max_concurrent=3,
            asset_downloader=mock_downloader
        )
        
        assert len(result) == 1
        mock_downloader.download.assert_called_once()
