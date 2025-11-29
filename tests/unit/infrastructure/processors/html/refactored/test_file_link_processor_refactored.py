"""Tests for FileLinkProcessor refactoring"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor

class TestFileLinkProcessorRefactored:
    """Test suite for refactored FileLinkProcessor"""
    
    @pytest.fixture
    def processor(self):
        return FileLinkProcessor()
    
    @pytest.fixture
    def mock_context(self):
        # Use temporary directory instead of /test
        with tempfile.TemporaryDirectory() as temp_dir:
            return {
                "base_url": "https://fipi.ru",
                "run_folder_page": Path(temp_dir),
                "files_location_prefix": "assets/",
                "asset_downloader": AsyncMock()
            }
    
    @pytest.mark.asyncio
    async def test_process_with_no_links(self, processor, mock_context):
        """Test processing HTML with no file links"""
        raw_data = {
            "body_html": "<div>No links here</div>",
            "files": []
        }
        
        result = await processor.process(raw_data, mock_context)
        
        assert result["files"] == []
        assert "body_html" in result
    
    @pytest.mark.asyncio 
    async def test_process_with_pdf_link(self, processor, mock_context):
        """Test processing HTML with PDF link"""
        raw_data = {
            "body_html": '<a href="document.pdf">PDF</a>',
            "files": []
        }
        mock_context["asset_downloader"].download.return_value = True
        
        result = await processor.process(raw_data, mock_context)
        
        # Should attempt download and add to files list
        mock_context["asset_downloader"].download.assert_called_once()
        assert len(result["files"]) == 1
