import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path

from src.application.use_cases.scraping.components.page_processor import PageProcessor
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.page_scraping_result import PageScrapingResult
from src.domain.models.problem import Problem


@pytest.fixture
def test_dependencies():
    return {
        'page_scraping_service': AsyncMock(),
        'problem_repository': AsyncMock(),
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
        timeout_seconds=30
    )


@pytest.fixture
def base_run_folder():
    return Path("data") / "math"


class TestPageProcessor:
    @pytest.mark.asyncio
    async def test_process_page_success(self, test_dependencies, subject_info, scraping_config, base_run_folder):
        """Test successful page processing."""
        # Arrange
        processor = PageProcessor(**test_dependencies)
        page_num = 1
        
        # Mock page scraping result
        mock_problems = [
            Problem(problem_id="math_1", subject_name=subject_info.official_name, text="Problem 1", source_url="http://page1/p1"),
            Problem(problem_id="math_2", subject_name=subject_info.official_name, text="Problem 2", source_url="http://page1/p2")
        ]
        mock_scraping_result = PageScrapingResult(problems=mock_problems, assets_downloaded=3)
        
        test_dependencies['page_scraping_service'].scrape_page.return_value = mock_scraping_result
        test_dependencies['problem_repository'].save.return_value = None

        # Act
        result = await processor.process_page(page_num, subject_info, scraping_config, base_run_folder)

        # Assert
        assert result.page_number == page_num
        assert result.problems_found == 2
        assert result.problems_saved == 2
        assert result.assets_downloaded == 3
        assert result.error is None
        assert result.page_duration_seconds > 0
        
        test_dependencies['page_scraping_service'].scrape_page.assert_awaited_once()
        assert test_dependencies['problem_repository'].save.await_count == 2
        test_dependencies['progress_reporter'].report_page_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_page_empty_result(self, test_dependencies, subject_info, scraping_config, base_run_folder):
        """Test page processing with empty result."""
        # Arrange
        processor = PageProcessor(**test_dependencies)
        page_num = 1
        
        mock_scraping_result = PageScrapingResult(problems=[], assets_downloaded=0)
        test_dependencies['page_scraping_service'].scrape_page.return_value = mock_scraping_result

        # Act
        result = await processor.process_page(page_num, subject_info, scraping_config, base_run_folder)

        # Assert
        assert result.page_number == page_num
        assert result.problems_found == 0
        assert result.problems_saved == 0
        assert result.assets_downloaded == 0
        assert result.error is None
        
        test_dependencies['page_scraping_service'].scrape_page.assert_awaited_once()
        test_dependencies['problem_repository'].save.assert_not_awaited()
        test_dependencies['progress_reporter'].report_page_progress.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_page_error(self, test_dependencies, subject_info, scraping_config, base_run_folder):
        """Test page processing with error."""
        # Arrange
        processor = PageProcessor(**test_dependencies)
        page_num = 1
        
        test_dependencies['page_scraping_service'].scrape_page.side_effect = Exception("Scraping failed")

        # Act
        result = await processor.process_page(page_num, subject_info, scraping_config, base_run_folder)

        # Assert
        assert result.page_number == page_num
        assert result.problems_found == 0
        assert result.problems_saved == 0
        assert result.assets_downloaded == 0
        assert "Scraping failed" in result.error
        
        test_dependencies['progress_reporter'].report_page_error.assert_called_once()
