"""
Unit tests for the ScrapeSubjectUseCase.

These tests mock dependencies (IBrowserService, IProblemRepository) to isolate
the use case logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from dataclasses import replace # Импортируем replace
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.scraping_result import ScrapingResult
# Удаляем ненужные импорты Value Objects
# from src.domain.value_objects.subject import Subject
# from src.domain.value_objects.problem_id import ProblemId


class TestScrapeSubjectUseCase:
    """Tests for ScrapeSubjectUseCase."""

    @pytest.fixture
    def mock_browser_service(self):
        """Fixture to create a mock IBrowserService."""
        return AsyncMock()

    @pytest.fixture
    def mock_problem_repository(self):
        """Fixture to create a mock IProblemRepository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_browser_service, mock_problem_repository):
        """Fixture to create a ScrapeSubjectUseCase instance with mocked dependencies."""
        return ScrapeSubjectUseCase(
            browser_service=mock_browser_service,
            problem_repository=mock_problem_repository
        )

    @pytest.fixture
    def subject_info(self):
        """Fixture for SubjectInfo."""
        return SubjectInfo(
            alias="math",
            official_name="Математика (профильный уровень)",
            proj_id="12345",
            exam_year=2026
        )

    @pytest.fixture
    def scraping_config(self):
        """Fixture for ScrapingConfig."""
        return ScrapingConfig(
            mode=ScrapingMode.SEQUENTIAL,
            max_empty_pages=2,
            start_page="init",
            max_pages=None,
            force_restart=False, # Убедимся, что по умолчанию False
            parallel_workers=3,
            timeout_seconds=30,
            retry_attempts=3,
            retry_delay_seconds=1
        )

    @pytest.mark.asyncio
    async def test_successful_scraping(self, use_case, subject_info, scraping_config, mock_browser_service, mock_problem_repository):
        """Test successful scraping of a subject."""
        # Setup mock returns for _determine_last_page and _scrape_page_stub (using side_effect for stub)
        # We need to patch the internal stub methods to control their behavior in the test
        # This is a simplified approach, a more robust one might involve injecting a PageScrapingService
        # For now, let's directly test the logic flow assuming stubs work as expected
        # Mock the _determine_last_page method
        with patch.object(use_case, '_determine_last_page', return_value=2):
            # Mock the _scrape_page_stub method
            # This simulates the internal logic of the use case
            # We'll call the execute method and assert the final result
            # The actual page scraping logic (in stub) is tested separately or will be when implemented
            # For this test, we assume stubs return predictable results based on page number
            # e.g., init page has 1 problem, page 1 has 0 problems, page 2 has 0 problems
            # We can't easily mock _scrape_page_stub because it's an async method within the same class
            # Let's focus on the main flow and result structure, assuming stubs work
            # A better approach would be to extract page scraping logic to a separate service
            # and mock that service here instead of the internal stubs.

            # For now, let's proceed with the assumption that the internal logic works as stubbed
            # and focus on the overall result and calls to dependencies like _determine_last_page

            # Execute use case
            result = await use_case.execute(subject_info, scraping_config)

            # Verify results based on the stubbed behavior and determined last page (2)
            # init page + page 1 + page 2 = 3 total pages
            # Assuming 1 problem found/saved on init, 0 on page 1, 0 on page 2 -> 1 found, 1 saved
            assert result.success is True
            assert result.subject_name == subject_info.official_name
            assert result.total_pages == 3  # init + 1 + 2
            assert result.total_problems_found == 1 # From stubs (init page has 1)
            assert result.total_problems_saved == 1 # From stubs (init page has 1 saved)
            # Check that _determine_last_page was called
            mock_use_case_determine = AsyncMock(return_value=2)
            with patch.object(use_case, '_determine_last_page', mock_use_case_determine):
                 await use_case.execute(subject_info, scraping_config)
                 mock_use_case_determine.assert_called_once_with(subject_info.proj_id)

    # Example of testing error handling within the use case
    @pytest.mark.asyncio
    async def test_error_in_determine_last_page(self, use_case, subject_info, scraping_config, mock_browser_service, mock_problem_repository):
        """Test that an error during last page determination is handled."""
        # Setup mock to raise an exception
        with patch.object(use_case, '_determine_last_page', side_effect=Exception("Pager Error")):
            # Execute use case
            result = await use_case.execute(subject_info, scraping_config)

            # Verify results - success should be False, error captured
            assert result.success is False
            assert subject_info.official_name in result.subject_name
            assert "Pager Error" in result.errors[0] # Check if error message is captured

    # Удаляем тест test_force_restart_behavior, так как его логика удаления директории data/... 
    # противоречит принципу "одна база на все предметы".
    # Логика перезаписи задач для предмета должна быть внутри IProblemRepository, 
    # Use Case просто вызывает соответствующий метод, если force_restart=True.
    # Этот сценарий можно протестировать отдельно на уровне интеграции или в тестах репозитория.


if __name__ == "__main__":
    pytest.main(["-v", __file__, "-k", "async"]) # Run only async tests in this file
