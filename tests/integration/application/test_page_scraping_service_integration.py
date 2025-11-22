"""
Integration tests for PageScrapingService that verify interaction with real dependencies.
"""
import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path
from src.application.services.page_scraping_service import PageScrapingService
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter
from src.infrastructure.adapters.external_services.playwright_asset_downloader_adapter import PlaywrightAssetDownloaderAdapter
from src.infrastructure.adapters.html_processing.metadata_extractor_adapter import MetadataExtractorAdapter

@pytest.fixture
def mock_browser_service():
    """Mock for IBrowserService."""
    mock = AsyncMock(spec=IBrowserService)
    mock.get_page_content.return_value = "<html><body>Test content</body></html>"
    return mock

@pytest.fixture
def mock_asset_downloader():
    """Mock for IAssetDownloader."""
    mock = AsyncMock()
    mock.download.return_value = "/path/to/downloaded/file"
    mock.download_bytes.return_value = b"test content"
    return mock

@pytest.fixture
def mock_problem_factory():
    """Mock for IProblemFactory."""
    mock = MagicMock(spec=IProblemFactory)
    mock.create_problem.return_value = MagicMock(
        problem_id="test_problem_1",
        subject_name="Test Subject",
        text="Test problem text"
    )
    return mock

@pytest.fixture
def html_block_processing_service():
    """Create a real HTMLBlockProcessingService with correct dependencies."""
    return HTMLBlockProcessingService(
        metadata_extractor=MetadataExtractorAdapter(),
        raw_processors=[]
    )

@pytest.fixture
def asset_downloader_adapter(mock_asset_downloader, tmp_path):
    """Create AssetDownloaderAdapter with mocked implementation and default_assets_dir."""
    return AssetDownloaderAdapter(
        asset_downloader_impl=mock_asset_downloader,
        default_assets_dir=tmp_path / "assets"
    )

@pytest.fixture
def page_scraping_service(html_block_processing_service, mock_browser_service, asset_downloader_adapter, mock_problem_factory):
    """Create a real PageScrapingService with all required dependencies."""
    return PageScrapingService(
        html_block_processing_service=html_block_processing_service,
        browser_service=mock_browser_service,
        asset_downloader_impl=asset_downloader_adapter,
        problem_factory=mock_problem_factory
    )

@pytest.mark.asyncio
async def test_page_scraping_service_basic_integration(page_scraping_service):
    """Test that PageScrapingService can successfully scrape a page with minimal dependencies."""
    subject_info = SubjectInfo.from_alias("math")
    base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}"
    url = f"{base_url}?page=1"
    timeout = 30
    run_folder_page = Path("test_run_folder")
    
    # Execute the page scraping service
    problems = await page_scraping_service.scrape_page(
        url=url,
        subject_info=subject_info,
        base_url=base_url,
        timeout=timeout,
        run_folder_page=run_folder_page,
        files_location_prefix="assets/"
    )
    
    # Basic assertions
    assert isinstance(problems, list)
