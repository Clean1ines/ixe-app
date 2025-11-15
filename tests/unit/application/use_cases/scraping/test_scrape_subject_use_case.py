"""
Unit tests for ScrapeSubjectUseCase.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.services.page_scraping_service import PageScrapingService
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.domain.models.problem import Problem

@pytest.fixture
def mock_page_scraping_service():
    """Mock for PageScrapingService."""
    return AsyncMock(spec=PageScrapingService)

@pytest.fixture
def mock_problem_repository():
    """Mock for IProblemRepository."""
    return Mock(spec=IProblemRepository)

@pytest.fixture
def mock_problem_factory():
    """Mock for IProblemFactory."""
    return Mock(spec=IProblemFactory)

@pytest.fixture
def mock_browser_service():
    """Mock for IBrowserService."""
    return Mock(spec=IBrowserService)

@pytest.fixture
def mock_asset_downloader_impl():
    """Mock for IAssetDownloader implementation."""
    return AsyncMock(spec=IAssetDownloader)

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
    async def test_successful_scraping(self, use_case, mock_page_scraping_service, mock_problem_repository):
        """Test successful scraping execution."""
        subject_info = SubjectInfo.from_alias("math")
        # Установим max_pages=1 и start_page=1, чтобы избежать бесконечного цикла
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30, start_page=1, max_pages=1, max_empty_pages=1)
        
        mock_problem = Mock(spec=Problem)
        mock_problem.problem_id = "math_0_12345"
        mock_problems_list = [mock_problem]
        # Мокнем scrape_page, чтобы он возвращал список проблем только для первой итерации
        mock_page_scraping_service.scrape_page.return_value = mock_problems_list
        
        # Мокнем _save_problems, чтобы он возвращал количество сохраненных проблем
        with patch.object(use_case, '_save_problems', return_value=1) as mock_save:
            result = await use_case.execute(subject_info, config)

        assert result.success is True
        assert result.total_pages == 1
        assert result.total_problems_found == 1
        assert result.total_problems_saved == 1
        # Проверим, что _save_problems был вызван с правильными аргументами
        mock_save.assert_called_once_with(mock_problems_list, config.force_restart)

    @pytest.mark.asyncio
    async def test_error_in_page_scraping(self, use_case, mock_page_scraping_service):
        """Test use case handles errors from PageScrapingService."""
        subject_info = SubjectInfo.from_alias("math")
        # Установим max_pages=1 и start_page=1, чтобы избежать бесконечного цикла
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30, start_page=1, max_pages=1, max_empty_pages=1)
        
        # Мокнем scrape_page, чтобы он выбрасывал исключение
        mock_page_scraping_service.scrape_page.side_effect = Exception("Browser error")

        result = await use_case.execute(subject_info, config)

        # Проверим, что возвращается ошибка
        assert result.success is False
        assert result.total_problems_saved == 0
        assert len(result.errors) == 1
        assert "Browser error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_force_restart_behavior(self, use_case, mock_problem_repository):
        """Test that force_restart is passed correctly to the repository via _save_problems."""
        subject_info = SubjectInfo.from_alias("math")
        # Установим max_pages=1 и start_page=1, чтобы избежать бесконечного цикла
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30, start_page=1, max_pages=1, force_restart=True, max_empty_pages=1)
        
        mock_problem = Mock(spec=Problem)
        mock_problem.problem_id = "math_0_12345"
        mock_problems_list = [mock_problem]
        
        # Создадим мок для PageScrapingService, который возвращает одну проблему
        actual_page_service = Mock(spec=PageScrapingService)
        actual_page_service.scrape_page = AsyncMock(return_value=[mock_problem])

        # Создадим экземпляр UseCase с моками
        final_use_case = ScrapeSubjectUseCase(
            page_scraping_service=actual_page_service,
            problem_repository=mock_problem_repository,
            problem_factory=Mock(spec=IProblemFactory),
            browser_service=Mock(spec=IBrowserService),
            asset_downloader_impl=Mock(spec=IAssetDownloader)
        )
        
        # Мокнем _save_problems, чтобы избежать реального вызова save
        # Но теперь _save_problems будет вызывать mock_problem_repository.save
        # Проверим, что save вызывается с force_restart=True
        # Для этого нужно замокать _save_problems, чтобы он вызвал реальный save на замоканном репозитории
        # Или проверить, что save был вызван после выполнения
        # Лучше всего будет проверить, что save был вызван с force_restart=True
        # Проверим, что save вызывается в _save_problems
        # Замокаем _save_problems, но внутри него вызовем реальный save
        def real_save_side_effect(problems, force_restart):
            for p in problems:
                mock_problem_repository.save(p, force_restart=force_restart)
            return len(problems)

        with patch.object(final_use_case, '_save_problems', side_effect=real_save_side_effect):
            await final_use_case.execute(subject_info, config)
        
        # Проверим, что mock_problem_repository.save был вызван с force_restart=True
        assert mock_problem_repository.save.call_count == 1
        # Проверим аргументы вызова save
        call_args = mock_problem_repository.save.call_args
        assert call_args is not None
        # args[0] - проблема, kwargs['force_restart'] - force_restart
        assert call_args[1]['force_restart'] == config.force_restart
