"""
Unit tests for ScrapingOrchestrator.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock
from datetime import datetime
from src.application.services.scraping_orchestrator import ScrapingOrchestrator
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.application.value_objects.scraping.subject_info import SubjectInfo

@pytest.fixture
def mock_scrape_use_case():
    """Mock for ScrapeSubjectUseCase."""
    mock = AsyncMock(spec=ScrapeSubjectUseCase)
    mock.execute = AsyncMock()
    return mock

@pytest.fixture
def orchestrator(mock_scrape_use_case):
    """Instance of ScrapingOrchestrator with mocked dependencies."""
    return ScrapingOrchestrator(scrape_use_case=mock_scrape_use_case)

class TestScrapingOrchestrator:

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_single_subject(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator runs scraping for a single subject."""
        subject_alias = "math"
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": subject_alias, "config": config}]
        
        mock_result = ScrapingResult(
            subject_name="Математика. Базовый уровень",
            success=True,
            total_pages=1,
            total_problems_found=5,
            total_problems_saved=5,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        mock_scrape_use_case.execute.return_value = mock_result

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert len(results) == 1
        assert subject_alias in results
        assert results[subject_alias] == mock_result
        mock_scrape_use_case.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_multiple_subjects(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator runs scraping for multiple subjects concurrently."""
        subjects = ["math", "inf"]  # Используем существующие предметы из маппинга
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": alias, "config": config} for alias in subjects]
        
        mock_result_math = ScrapingResult(
            subject_name="Математика. Базовый уровень",
            success=True,
            total_pages=1,
            total_problems_found=5,
            total_problems_saved=5,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        mock_result_inf = ScrapingResult(
            subject_name="Информатика и ИКТ",
            success=True,
            total_pages=1,
            total_problems_found=3,
            total_problems_saved=3,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        async def mock_execute_side_effect(subject_info, config):
            if subject_info.alias == "math":
                return mock_result_math
            elif subject_info.alias == "inf":
                return mock_result_inf
            return ScrapingResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=0,
                total_problems_found=0,
                total_problems_saved=0,
                page_results=[],
                errors=[],
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        
        mock_scrape_use_case.execute.side_effect = mock_execute_side_effect

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert len(results) == 2
        assert "math" in results
        assert "inf" in results
        assert results["math"] == mock_result_math
        assert results["inf"] == mock_result_inf

    @pytest.mark.asyncio
    async def test_run_parallel_scraping_handles_exception(self, orchestrator, mock_scrape_use_case):
        """Test orchestrator handles exceptions from a subject's scraping."""
        subject_alias = "math"
        config = ScrapingConfig(mode=ScrapingMode.SEQUENTIAL, timeout_seconds=30)
        subject_configs = [{"subject_alias": subject_alias, "config": config}]
        
        mock_scrape_use_case.execute.side_effect = Exception("Network error")

        results = await orchestrator.run_parallel_scraping(subject_configs)

        assert len(results) == 1
        assert subject_alias in results
        result = results[subject_alias]
        assert result.success is False
        assert len(result.errors) == 1
        assert "Network error" in result.errors[0]
