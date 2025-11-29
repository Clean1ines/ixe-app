"""
Unit tests for ScrapeSubjectUseCase.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.services.page_scraping_service import PageScrapingService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem

@pytest.fixture
def mock_page_scraping_service():
    """Mock for PageScrapingService."""
    mock = AsyncMock(spec=PageScrapingService)
    mock.scrape_page = AsyncMock(return_value=[])
    return mock

@pytest.fixture
def mock_problem_repository():
    """Mock for IProblemRepository."""
    mock = MagicMock(spec=IProblemRepository)
    mock.save = AsyncMock()  # Важно: делаем save асинхронным
    mock.get_by_subject = AsyncMock(return_value=[])
    mock.clear_subject_problems = AsyncMock()
    mock.get_all = AsyncMock(return_value=[])
    return mock

@pytest.fixture
def mock_problem_factory():
    """Mock for IProblemFactory."""
    mock = MagicMock(spec=IProblemFactory)
    mock.create_problem = MagicMock(return_value=Problem(
        problem_id="test_problem",
        subject_name="Математика. Базовый уровень",
        text="Test problem",
        source_url="https://test.url",
        created_at=datetime.now()
    ))
    return mock

@pytest.fixture
def mock_browser_service():
    """Mock for IBrowserService."""
    mock = MagicMock(spec=IBrowserService)
    mock.get_page_content = AsyncMock(return_value="<html></html>")
    mock.get_browser = AsyncMock()
    mock.release_browser = AsyncMock()
    return mock

@pytest.fixture
def mock_asset_downloader_impl():
    """Mock for IAssetDownloader implementation."""
    mock = AsyncMock(spec=IAssetDownloader)
    mock.download = AsyncMock(return_value="/path/to/file")
    mock.download_bytes = AsyncMock()
    return mock

@pytest.fixture
def use_case(mock_page_scraping_service, mock_problem_repository, mock_problem_factory, mock_browser_service, mock_asset_downloader_impl):
    """Instance of ScrapeSubjectUseCase with mocked dependencies."""
    return ScrapeSubjectUseCase(
        page_scraping_service=mock_page_scraping_service,
        problem_repository=mock_problem_repository,
        problem_factory=mock_problem_factory,
        browser_service=mock_browser_service,
        asset_downloader_impl=mock_asset_downloader_impl
    )

class TestScrapeSubjectUseCase:

    @pytest.mark.asyncio
    async def test_successful_scraping(self, use_case, mock_page_scraping_service, mock_problem_repository, mock_problem_factory, subject_info):
        """Test successful scraping execution."""
        config = ScrapingConfig(
            mode=ScrapingMode.SEQUENTIAL,
            timeout_seconds=30,
            start_page=1,
            max_pages=1,
            max_empty_pages=1
        )
        
        # Создаем тестовую проблему
        mock_problem = Problem(
            problem_id="math_0_12345",
            subject_name=subject_info.official_name,
            text="Test problem text",
            source_url=f"{subject_info.base_url}?page=1",
            created_at=datetime.now()
        )
        
        # Мокаем возврат проблемы
        mock_page_scraping_service.scrape_page = AsyncMock(return_value=[mock_problem])
        
        # Выполняем use case
        result = await use_case.execute(subject_info, config)

        # Проверяем результат
        assert result.success is True
        assert result.total_pages == 1
        assert result.total_problems_found == 1
        assert result.total_problems_saved == 1
        
        # Проверяем, что проблема была сохранена
        mock_problem_repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_error_in_page_scraping(self, use_case, mock_page_scraping_service, subject_info):
        """Test use case handles errors from PageScrapingService."""
        config = ScrapingConfig(
            mode=ScrapingMode.SEQUENTIAL,
            timeout_seconds=30,
            start_page=1,
            max_pages=1,
            max_empty_pages=1
        )
        
        # Мокаем ошибку в scraping service
        mock_page_scraping_service.scrape_page.side_effect = Exception("Browser error")

        result = await use_case.execute(subject_info, config)

        # Проверяем, что возвращается ошибка
        assert result.success is False
        assert result.total_problems_saved == 0
        assert len(result.errors) == 1
        assert "Browser error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_force_restart_behavior(self, use_case, mock_problem_repository, mock_page_scraping_service, subject_info):
        """Test that force_restart is passed correctly to the repository."""
        config = ScrapingConfig(
            mode=ScrapingMode.SEQUENTIAL,
            timeout_seconds=30,
            start_page=1,
            max_pages=1,
            max_empty_pages=1,
            force_restart=True
        )
        
        # Создаем тестовую проблему
        mock_problem = Problem(
            problem_id="math_0_12345",
            subject_name=subject_info.official_name,
            text="Test problem text",
            source_url=f"{subject_info.base_url}?page=1",
            created_at=datetime.now()
        )
        
        # Мокаем возврат проблемы
        mock_page_scraping_service.scrape_page = AsyncMock(return_value=[mock_problem])
        
        # Выполняем use case
        result = await use_case.execute(subject_info, config)
        
        # Проверяем результат
        assert result.success is True
        assert result.total_problems_saved == 1
        
        # Проверяем, что clear_subject_problems был вызван при force_restart=True
        mock_problem_repository.clear_subject_problems.assert_awaited_once()
        
        # Проверяем, что save был вызван
        mock_problem_repository.save.assert_awaited_once()
