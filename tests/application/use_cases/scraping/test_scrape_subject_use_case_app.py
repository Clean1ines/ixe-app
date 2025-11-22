"""
Unit tests for ScrapeSubjectUseCase that follow classical TDD principles. These tests focus on state-based and
interaction-based expectations for the use case's behavior.
"""
import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
from src.application.value_objects.scraping.scraping_result import ScrapingResult

@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for ScrapeSubjectUseCase."""
    return {
        'page_scraping_service': AsyncMock(),
        'problem_repository': AsyncMock(),
        'problem_factory': MagicMock(),
        'browser_service': AsyncMock(),
        'progress_service': AsyncMock(),
        'progress_reporter': MagicMock(),  # Используем MagicMock вместо AsyncMock
        'asset_downloader_impl': AsyncMock()
    }

@pytest.fixture
def subject_info():
    """Create a sample SubjectInfo for testing."""
    return SubjectInfo(
        alias='math',
        official_name='Математика. Базовый уровень',
        proj_id='E040A72A1A3DABA14C90C97E0B6EE7DC',
        exam_year=2026
    )

@pytest.mark.asyncio
async def test_force_restart_rescrapes_from_page_1(subject_info, mock_dependencies):
    """Test that force_restart=True causes scraping to start from page 1."""
    repository = mock_dependencies['problem_repository']
    page_scraping_service = mock_dependencies['page_scraping_service']
    progress_service = mock_dependencies['progress_service']
    progress_reporter = mock_dependencies['progress_reporter']
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Мокаем правильный метод get_next_page_to_scrape
    progress_service.get_next_page_to_scrape = AsyncMock(return_value=1)
    
    # Настраиваем репозиторий
    repository.get_by_subject.return_value = []
    repository.save = AsyncMock()
    repository.clear_subject_problems = AsyncMock()
    
    # Создаем mock проблемы для новой загрузки
    new_problems = [
        Problem(
            problem_id="math_4FF3441",
            subject_name=subject_info.official_name,
            text="New problem from page 1",
            source_url="https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=1",
            created_at=datetime.now()
        )
    ]
    
    # Настраиваем scraping service для возврата проблем
    page_scraping_service.scrape_page.return_value = new_problems
    
    # Убеждаемся, что все методы progress_reporter являются MagicMock (не AsyncMock)
    progress_reporter.report_start = MagicMock()
    progress_reporter.report_page_progress = MagicMock()
    progress_reporter.report_page_error = MagicMock()
    progress_reporter.report_summary = MagicMock()
    
    use_case = ScrapeSubjectUseCase(**mock_dependencies)
    
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        timeout_seconds=30,
        force_restart=True,
        start_page=None,
        max_pages=1,
        max_empty_pages=2
    )
    
    result = await use_case.execute(subject_info, config)
    
    # Проверяем что скрапинг был выполнен для страницы 1
    page_scraping_service.scrape_page.assert_awaited_once()
    
    # Проверяем результат
    assert result.success is True
    assert result.total_pages == 1
    assert result.total_problems_saved == 1
