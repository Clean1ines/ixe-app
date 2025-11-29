"""Comprehensive tests for FileLinkProcessor refactoring"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor

class TestFileLinkProcessorComprehensive:
    """Comprehensive test suite for FileLinkProcessor"""
    
    @pytest.fixture
    def processor(self):
        return FileLinkProcessor()
    
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
    async def test_process_empty_html(self, processor, mock_context):
        """Test processing empty HTML"""
        raw_data = {"body_html": "", "files": []}
        result = await processor.process(raw_data, mock_context)
        assert result["files"] == []
    
    @pytest.mark.asyncio
    async def test_process_no_file_links(self, processor, mock_context):
        """Test HTML with no file links"""
        raw_data = {
            "body_html": '<a href="/page.html">Regular link</a>',
            "files": []
        }
        result = await processor.process(raw_data, mock_context)
        assert result["files"] == []
    
    @pytest.mark.asyncio
    async def test_process_pdf_link(self, processor, mock_context):
        """Test PDF link processing"""
        raw_data = {
            "body_html": '<a href="document.pdf">PDF Document</a>',
            "files": []
        }
        mock_context["asset_downloader"].download.return_value = True
        
        result = await processor.process(raw_data, mock_context)
        
        assert len(result["files"]) == 1
        mock_context["asset_downloader"].download.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_multiple_file_types(self, processor, mock_context):
        """Test multiple file types"""
        raw_data = {
            "body_html": '''
                <a href="doc.pdf">PDF</a>
                <a href="file.doc">DOC</a>
                <a href="archive.zip">ZIP</a>
            ''',
            "files": []
        }
        mock_context["asset_downloader"].download.return_value = True
        
        result = await processor.process(raw_data, mock_context)
        
        assert len(result["files"]) == 3
        assert mock_context["asset_downloader"].download.call_count == 3
