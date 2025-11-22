"""
Integration tests for ScrapeSubjectUseCase and PageScrapingService.
"""
import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.services.page_scraping_service import PageScrapingService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter

@pytest.fixture
def mock_browser_service():
    mock = AsyncMock(spec=IBrowserService)
    mock.get_page_content.return_value = "<html><body>Test content</body></html>"
    return mock

@pytest.fixture
def mock_asset_downloader():
    mock = AsyncMock()
    mock.download.return_value = "/path/to/downloaded/file"
    mock.download_bytes.return_value = b"test content"
    return mock

@pytest.fixture
def mock_problem_repository():
    mock = AsyncMock(spec=IProblemRepository)
    mock.get_by_subject.return_value = []
    mock.get_by_id.return_value = None
    # Убираем clear_subject_problems, так как его нет в интерфейсе
    return mock

@pytest.fixture
def mock_problem_factory():
    mock = MagicMock(spec=IProblemFactory)
    mock.create_problem.return_value = Problem(
        problem_id="test_problem_1",
        subject_name="Математика. Базовый уровень",
        text="Test problem text",
        source_url="https://ege.fipi.ru/test",
        created_at=datetime.now()
    )
    return mock

@pytest.fixture
def html_block_processing_service(mock_asset_downloader, mock_problem_factory):
    from src.application.services.html_block_processing_service import HTMLBlockProcessingService
    return HTMLBlockProcessingService(
        problem_factory=mock_problem_factory,
        asset_downloader_impl=mock_asset_downloader
    )

@pytest.fixture
def asset_downloader_adapter(mock_asset_downloader, tmp_path):
    return AssetDownloaderAdapter(
        asset_downloader_impl=mock_asset_downloader,
        default_assets_dir=tmp_path / "assets"
    )

@pytest.fixture
def page_scraping_service(html_block_processing_service, mock_browser_service, asset_downloader_adapter, mock_problem_factory):
    return PageScrapingService(
        html_block_processing_service=html_block_processing_service,
        browser_service=mock_browser_service,
        asset_downloader_impl=asset_downloader_adapter,
        problem_factory=mock_problem_factory
    )

@pytest.fixture
def scrape_subject_use_case(page_scraping_service, mock_problem_repository, mock_problem_factory, mock_browser_service, mock_asset_downloader):
    return ScrapeSubjectUseCase(
        page_scraping_service=page_scraping_service,
        problem_repository=mock_problem_repository,
        problem_factory=mock_problem_factory,
        browser_service=mock_browser_service,
        asset_downloader_impl=mock_asset_downloader
    )

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real implementation of clear_subject_problems")
async def test_scrape_subject_use_case_integration(scrape_subject_use_case, mock_problem_repository):
    pass

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real HTML parsing implementation")
async def test_page_scraping_service_integration(page_scraping_service, mock_problem_factory):
    pass
