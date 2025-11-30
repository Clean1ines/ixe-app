import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.page_scraping_result import PageScrapingResult
from dataclasses import replace
from src.domain.models.problem import Problem


@pytest.fixture
def mock_services():
    """Create mocked services for integration testing."""
    return {
        'page_scraping_service': AsyncMock(),
        'problem_repository': AsyncMock(),
        'problem_factory': MagicMock(),
        'browser_service': AsyncMock(),
        'asset_downloader_impl': AsyncMock(),
        'progress_service': AsyncMock(),
        'progress_reporter': MagicMock()
    }


@pytest.fixture
def subject_info():
    return SubjectInfo(
        alias='math',
        official_name='Математика. Базовый уровень',
        proj_id='E040A72A1A3DABA14C90C97E0B6EE7DC',
        exam_year=2026
    )


@pytest.fixture
def scraping_config():
    return ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        max_pages=3,
        timeout_seconds=30,
        force_restart=False
    )


class TestScrapeSubjectUseCaseIntegration:
    @pytest.mark.asyncio
    async def test_execute_successful_scraping(self, mock_services, subject_info, scraping_config):
        """Test successful scraping execution with new architecture."""
        # Arrange
        use_case = ScrapeSubjectUseCase(**mock_services)
        
        # Mock progress service
        mock_services['progress_service'].get_next_page_to_scrape.return_value = 1
        
        # Mock page scraping results
        problems_page1 = [
            Problem(problem_id="math_1", subject_name=subject_info.official_name, text="Problem 1", source_url="http://page1/p1"),
            Problem(problem_id="math_2", subject_name=subject_info.official_name, text="Problem 2", source_url="http://page1/p2")
        ]
        problems_page2 = [
            Problem(problem_id="math_3", subject_name=subject_info.official_name, text="Problem 3", source_url="http://page2/p3")
        ]
        
        mock_services['page_scraping_service'].scrape_page.side_effect = [
            PageScrapingResult(problems=problems_page1, assets_downloaded=2),
            PageScrapingResult(problems=problems_page2, assets_downloaded=1),
            PageScrapingResult(problems=[], assets_downloaded=0)  # Empty page to stop
        ]
        
        # Mock repository
        mock_services['problem_repository'].get_by_subject.return_value = []
        mock_services['problem_repository'].save.return_value = None

        # Act
        result = await use_case.execute(subject_info, scraping_config)

        # Assert
        assert result.success is True
        assert result.total_pages == 3  # Processed 3 pages (last one empty)
        assert result.total_problems_found == 3
        assert result.total_problems_saved == 3
        assert len(result.errors) == 0
        
        # Verify service calls
        mock_services['progress_service'].get_next_page_to_scrape.assert_awaited_once()
        assert mock_services['page_scraping_service'].scrape_page.await_count == 3
        assert mock_services['problem_repository'].save.await_count == 3
        mock_services['progress_reporter'].report_start.assert_called_once()
        mock_services['progress_reporter'].report_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_force_restart(self, mock_services, subject_info, scraping_config):
        """Test scraping with force restart."""
        # Arrange
        use_case = ScrapeSubjectUseCase(**mock_services)
        new_config = replace(scraping_config, force_restart=True)
        
        # Mock existing problems
        existing_problems = [
            Problem(problem_id="math_old", subject_name=subject_info.official_name, text="Old problem", source_url="http://page_old/p_old")
        ]
        mock_services['problem_repository'].get_by_subject.return_value = existing_problems
        
        # Mock progress and scraping
        mock_services['progress_service'].get_next_page_to_scrape.return_value = 1
        mock_services['page_scraping_service'].scrape_page.return_value = PageScrapingResult(
            problems=[], assets_downloaded=0
        )

        # Act
        result = await use_case.execute(subject_info, new_config)

        # Assert
        assert result.success is True
        mock_services['problem_repository'].get_by_subject.assert_called_once_with(subject_info.official_name)

    @pytest.mark.asyncio
    async def test_execute_with_scraping_error(self, mock_services, subject_info, scraping_config):
        """Test scraping execution when page scraping fails."""
        # Arrange
        use_case = ScrapeSubjectUseCase(**mock_services)
        
        mock_services['progress_service'].get_next_page_to_scrape.return_value = 1
        mock_services['page_scraping_service'].scrape_page.side_effect = Exception("Network error")

        # Act
        result = await use_case.execute(subject_info, scraping_config)

        # Assert
        assert result.success is False
        assert len(result.errors) == 1
        assert "Network error" in result.errors[0]
        mock_services['progress_reporter'].report_page_error.assert_called()
