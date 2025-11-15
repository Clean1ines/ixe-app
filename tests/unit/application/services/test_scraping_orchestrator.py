"""
Unit tests for ScrapingOrchestrator.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from src.application.services.scraping_orchestrator import ScrapingOrchestrator
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.scraping_result import ScrapingResult

@pytest.fixture
def mock_scrape_use_case():
    """Mock for ScrapeSubjectUseCase."""
    return AsyncMock(spec=ScrapeSubjectUseCase)

@pytest.fixture
def orchestrator(mock_scrape_use_case):
    """Instance of ScrapingOrchestrator with mocked dependencies."""
    return ScrapingOrchestrator(scrape_use_case=mock_scrape_use_case)

class TestScrapingOrchestrator:
    """Tests for ScrapingOrchestrator."""

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_single_subject(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator runs scraping for a single subject."""
        subject_alias = "math"
        # Используем правильное значение ScrapingMode
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": subject_alias, "config": config}]
        
        mock_result = ScrapingResult(
            subject_name="Математика (профильный уровень)",
            success=True,
            total_pages=1,
            total_problems_found=5,
            total_problems_saved=5,
            page_results=[],
            errors=[],
            start_time=None,
            end_time=None
        )
        mock_scrape_use_case.execute.return_value = mock_result

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert subject_alias in results
        assert results[subject_alias] == mock_result
        mock_scrape_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_multiple_subjects(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator runs scraping for multiple subjects concurrently."""
        subjects = ["math", "informatics"]
        # Используем правильное значение ScrapingMode
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": alias, "config": config} for alias in subjects]
        
        mock_result_math = ScrapingResult(
            subject_name="Математика (профильный уровень)",
            success=True,
            total_pages=1,
            total_problems_found=5,
            total_problems_saved=5,
            page_results=[],
            errors=[],
            start_time=None,
            end_time=None
        )
        mock_result_inf = ScrapingResult(
            subject_name="Информатика и ИКТ",
            success=True,
            total_pages=1,
            total_problems_found=3,
            total_problems_saved=3,
            page_results=[],
            errors=[],
            start_time=None,
            end_time=None
        )
        # Configure side_effect to return different results based on the subject
        # For simplicity in this test, we'll assume the order is consistent or use a more complex mock
        # Here, we'll mock the execute call to return results based on the subject passed
        async def mock_execute_side_effect(subject_info, config):
            if subject_info.alias == "math":
                return mock_result_math
            elif subject_info.alias == "informatics":
                return mock_result_inf
            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=0,
                total_problems_found=0,
                total_problems_saved=0,
                page_results=[],
                errors=[],
                start_time=None,
                end_time=None
            )
        
        mock_scrape_use_case.execute.side_effect = mock_execute_side_effect

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert len(results) == 2
        assert "math" in results
        assert "informatics" in results
        assert results["math"] == mock_result_math
        assert results["informatics"] == mock_result_inf
        assert mock_scrape_use_case.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_handles_exception(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator handles exceptions from a subject's scraping."""
        subject_alias = "math"
        # Используем правильное значение ScrapingMode
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": subject_alias, "config": config}]
        
        mock_scrape_use_case.execute.side_effect = Exception("Network error")

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert subject_alias in results
        assert not results[subject_alias].success
        # Проверяем, что ошибка была захвачена и сохранена в результатах
        # Предположим, что ScrapingResult в этом случае будет с success=False и ошибкой
        # Это зависит от реализации, но в тесте мы проверим, что возвращается объект с success=False
        assert results[subject_alias].success is False
