"""Comprehensive tests for FileLinkProcessor refactoring (Using Fakes)"""
import pytest
import tempfile
from pathlib import Path
# УДАЛЕНО: from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from tests.fakes.fake_asset_downloader import FakeAssetDownloader # НОВЫЙ ИМПОРТ ФЕЙКА

class TestFileLinkProcessorComprehensive:
    """Comprehensive test suite for FileLinkProcessor (using Fakes)"""
    
    @pytest.fixture
    def processor(self):
        return FileLinkProcessor()
    
    @pytest.fixture
    def fake_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем реальный фейковый объект для asset_downloader
            fake_downloader = FakeAssetDownloader()
            
            return {
                "base_url": "https://fipi.ru",
                "run_folder_page": Path(temp_dir),
                "files_location_prefix": "assets/",
                # ПЕРЕКЛЮЧЕНО: Вместо AsyncMock используем FakeAssetDownloader
                "asset_downloader": fake_downloader, 
                # Добавляем сам фейк, чтобы в тесте проверять счетчик вызовов
                "fake_downloader_instance": fake_downloader
            }
    
    @pytest.mark.asyncio
    async def test_process_empty_html(self, processor, fake_context):
        """Test processing empty HTML"""
        raw_data = {"body_html": "", "files": []}
        result = await processor.process(raw_data, fake_context)
        assert result["files"] == []
        fake_context["fake_downloader_instance"].assert_download_called_n_times(0)
    
    @pytest.mark.asyncio
    async def test_process_no_file_links(self, processor, fake_context):
        """Test HTML with no file links"""
        raw_data = {
            "body_html": '<a href="/page.html">Regular link</a>',
            "files": []
        }
        result = await processor.process(raw_data, fake_context)
        assert result["files"] == []
        fake_context["fake_downloader_instance"].assert_download_called_n_times(0)
    
    @pytest.mark.asyncio
    async def test_process_pdf_link(self, processor, fake_context):
        """Test PDF link processing"""
        raw_data = {
            "body_html": '<a href="document.pdf">PDF Document</a>',
            "files": []
        }
        
        result = await processor.process(raw_data, fake_context)
        
        assert len(result["files"]) == 1
        # ПЕРЕКЛЮЧЕНО: Проверяем счетчик вызовов на фейке
        fake_context["fake_downloader_instance"].assert_download_called_n_times(1) 
    
    @pytest.mark.asyncio
    async def test_process_multiple_file_types(self, processor, fake_context):
        """Test multiple file types"""
        raw_data = {
            "body_html": '''
                <a href="doc.pdf">PDF</a>
                <a href="file.doc">DOC</a>
                <a href="archive.zip">ZIP</a>
            ''',
            "files": []
        }
        
        result = await processor.process(raw_data, fake_context)
        
        assert len(result["files"]) == 3
        # ПЕРЕКЛЮЧЕНО: Проверяем, что download был вызван 3 раза
        fake_context["fake_downloader_instance"].assert_download_called_n_times(3)
