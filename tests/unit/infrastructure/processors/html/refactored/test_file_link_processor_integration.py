"""Integration tests for refactored FileLinkProcessor"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from src.infrastructure.processors.html.file_link_processor_refactored import FileLinkProcessorRefactored

class TestFileLinkProcessorRefactoredIntegration:
    """Integration tests for refactored FileLinkProcessor"""
    
    @pytest.fixture
    def processor(self):
        return FileLinkProcessorRefactored()
    
    @pytest.fixture
    def mock_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            return {
                "base_url": "https://fipi.ru",
                "run_folder_page": Path(temp_dir),
                "files_location_prefix": "assets/",
                "asset_downloader": AsyncMock()
            }
    
    @pytest.mark.asyncio
    async def test_integration_pdf_download(self, processor, mock_context):
        """Test full integration with PDF download"""
        raw_data = {
            "body_html": '<a href="document.pdf">PDF</a>',
            "files": []
        }
        mock_context["asset_downloader"].download.return_value = True
        
        result = await processor.process(raw_data, mock_context)
        
        assert len(result["files"]) == 1
        mock_context["asset_downloader"].download.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integration_no_downloader(self, processor, mock_context):
        """Test behavior when no downloader is available"""
        raw_data = {
            "body_html": '<a href="document.pdf">PDF</a>',
            "files": []
        }
        context_without_downloader = {k: v for k, v in mock_context.items() if k != "asset_downloader"}
        
        result = await processor.process(raw_data, context_without_downloader)
        
        assert result["files"] == []  # No files downloaded without downloader
