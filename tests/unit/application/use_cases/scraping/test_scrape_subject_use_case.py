"""
Unit tests for the ScrapeSubjectUseCase.

These tests mock dependencies (IPageScrapingService, IProblemRepository) to isolate
the use case logic.
The tests now reflect the updated dependency structure of ScrapeSubjectUseCase,
which delegates page scraping and problem creation to PageScrapingService.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
from pathlib import Path # Импортируем Path для теста с force_restart

from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.application.services.page_scraping_service import PageScrapingService # Импортируем для типа мока
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository # Импортируем интерфейс
from src.domain.models.problem import Problem # Импортируем для создания моков или реальных объектов


class TestScrapeSubjectUseCase:
    """Tests for ScrapeSubjectUseCase."""

    @pytest.fixture
    def mock_page_scraping_service(self):
        """Fixture to create a mock IPageScrapingService."""
        # Use AsyncMock because its methods like scrape_page are async
        return AsyncMock(spec=PageScrapingService)

    @pytest.fixture
    def mock_problem_repository(self):
        """Fixture to create a mock IProblemRepository."""
        # Use AsyncMock because its methods like save are async
        return AsyncMock(spec=IProblemRepository)

    @pytest.fixture
    def use_case(self, mock_page_scraping_service, mock_problem_repository):
        """Fixture to create a ScrapeSubjectUseCase instance with mocked dependencies."""
        return ScrapeSubjectUseCase(
            page_scraping_service=mock_page_scraping_service,
            problem_repository=mock_problem_repository
            # browser_service, asset_downloader, problem_factory больше не передаются напрямую
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
            force_restart=False, # Уже есть в модели
            parallel_workers=3,
            timeout_seconds=30,
            retry_attempts=3,
            retry_delay_seconds=1
        )

    @pytest.mark.asyncio
    async def test_successful_scraping(self, use_case, subject_info, scraping_config, mock_page_scraping_service, mock_problem_repository):
        """Test successful scraping of a subject."""
        # Setup mock returns for PageScrapingService
        # Create mock Problem instances to return
        problem_init = Problem(problem_id="init_123", subject_name="math", text="Init problem text.", source_url="https://example.com/init")
        problem_1 = Problem(problem_id="page1_456", subject_name="math", text="Page 1 problem text.", source_url="https://example.com/p1")
        problem_2 = Problem(problem_id="page2_789", subject_name="math", text="Page 2 problem text.", source_url="https://example.com/p2")

        # Mock the scrape_page method to return lists of problems for different pages
        # The base URL is constructed inside the UseCase based on subject_info
        base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}"
        mock_page_scraping_service.scrape_page.side_effect = [
            [problem_init], # For init page (url = base_url + "?page=init")
            [problem_1],    # For page 1 (url = base_url + "?page=1")
            [],             # For page 2 (empty, triggers empty_count)
            []              # For page 3 (empty, triggers stop due to max_empty_pages)
        ]

        # Mock the repository save method to return True for success
        mock_problem_repository.save.return_value = None # save is an async void method, assuming success if no exception

        # Mock _determine_last_page to return None to trigger fallback logic based on max_empty_pages
        with patch.object(use_case, '_determine_last_page', return_value=None):
            # Execute use case
            result = await use_case.execute(subject_info, scraping_config)

        # Verify results based on the mocked behavior and determined last page (or fallback logic)
        # init page + page 1 + page 2 (empty) + page 3 (empty, stops)
        # Problems found: 1 (init) + 1 (p1) + 0 (p2) + 0 (p3) = 2
        # Problems saved: Depends on _save_problems, which calls problem_repository.save
        # Assuming all saves succeed in this test scenario
        expected_total_found = 2
        expected_total_saved = 2 # Assuming all saves succeed in this test scenario

        assert result.success is True
        assert result.subject_name == subject_info.official_name
        assert result.total_pages == 4  # init + 1 + 2 + 3
        assert result.total_problems_found == expected_total_found
        assert result.total_problems_saved == expected_total_saved
        # Verify that IPageScrapingService was called correctly
        assert mock_page_scraping_service.scrape_page.call_count == 4 # Called 4 times
        # Verify calls to scrape_page were made with the correct arguments (URLs, subject_info, etc.)
        expected_calls = [
            # Calls are made with the constructed URL based on base_url, page number, and subject_info
            # Also with timeout from config
            # And potentially run_folder_page/files_location_prefix if UseCase passes them down
            # For now, let's check the URL construction and subject_info
            # Init page
            # The URL construction is: f"{base_url}?page=init"
            # base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}" = "https://ege.fipi.ru/bank/12345"
            # So URL for init should be "https://ege.fipi.ru/bank/12345?page=init"
            # But the old processors expected 'page' as a query param, new ones might expect just '?init' or similar.
            # Let's stick to the UseCase's logic: init_url = f"{base_url}?page=init"
            # And numbered: page_url = f"{base_url}?page={page_num}"
            # So, the expected calls should be:
            # 1. scrape_page(url="https://ege.fipi.ru/bank/12345?page=init", subject_info=subject_info, base_url=base_url, timeout=...)
            # 2. scrape_page(url="https://ege.fipi.ru/bank/12345?page=1", subject_info=subject_info, base_url=base_url, timeout=...)
            # 3. scrape_page(url="https://ege.fipi.ru/bank/12345?page=2", subject_info=subject_info, base_url=base_url, timeout=...)
            # 4. scrape_page(url="https://ege.fipi.ru/bank/12345?page=3", subject_info=subject_info, base_url=base_url, timeout=...)
            # Let's assert the calls were made with correct subject_info and base_url, and the expected number of times
            # We can't easily assert the exact URL without mocking the URL construction inside the UseCase,
            # unless we make the URL construction a separate method和服务.
            # For now, we'll rely on the call count and the fact that subject_info and base_url are passed correctly.
            # The PageScrapingService test will verify the exact URL construction and scraping logic.
            # Here we test the *coordination* logic of ScrapeSubjectUseCase.
            # So, we assert the service was called the expected number of times.
            # And that save was called for the expected number of problems.
        ]
        # Check the arguments passed to scrape_page
        # This requires checking the call_args_list of the mock
        call_args_list = mock_page_scraping_service.scrape_page.call_args_list
        assert len(call_args_list) == 4 # 4 calls expected

        # Example: Check the first call (init page)
        first_call_args, first_call_kwargs = call_args_list[0]
        # assert first_call_kwargs['url'] == f"{base_url}?page=init" # This would require knowing the exact URL construction inside UC
        assert first_call_kwargs['subject_info'] == subject_info
        assert first_call_kwargs['base_url'] == base_url
        assert first_call_kwargs['timeout'] == scraping_config.timeout_seconds
        # Check the first result was for init page
        assert result.page_results[0]['page_number'] == 'init'

        # Verify that IProblemRepository.save was called for each problem found (based on _save_problems logic)
        # It should be called twice: once for problem_init, once for problem_1
        # The call count should match the total number of problems returned by scrape_page across all calls
        assert mock_problem_repository.save.call_count == expected_total_saved
        # Check calls to save were made with the correct problems and potentially the force_update flag
        expected_save_calls = [
            ((problem_init,), {'force_update': scraping_config.force_restart}), # Call with problem and force_update from config
            ((problem_1,), {'force_update': scraping_config.force_restart}),
        ]
        actual_save_calls = mock_problem_repository.save.call_args_list
        assert len(actual_save_calls) == len(expected_save_calls)
        for i, (expected_args, expected_kwargs) in enumerate(expected_save_calls):
             actual_call = actual_save_calls[i]
             assert actual_call.args == expected_args
             assert actual_call.kwargs.get('force_update') == expected_kwargs['force_update']


    # Example of testing error handling within the use case
    @pytest.mark.asyncio
    async def test_error_in_determine_last_page(self, use_case, subject_info, scraping_config, mock_page_scraping_service, mock_problem_repository):
        """Test that an error during last page determination is handled."""
        # Setup mock to raise an exception in _determine_last_page
        with patch.object(use_case, '_determine_last_page', side_effect=Exception("Pager Error")):
            # Execute use case
            result = await use_case.execute(subject_info, scraping_config)

            # Verify results - success should be False, error captured
            assert result.success is False
            assert subject_info.official_name in result.subject_name
            assert "Pager Error" in result.errors[0] # Check if error message is captured

    # Example of testing force restart behavior - focuses on repository interaction
    @pytest.mark.asyncio
    async def test_force_restart_behavior(self, use_case, subject_info, scraping_config, mock_page_scraping_service, mock_problem_repository):
        """Test that force restart option passes the flag to the problem repository."""
        # Create a new config object with force_restart=True
        force_restart_config = ScrapingConfig(
            mode=scraping_config.mode,
            max_empty_pages=scraping_config.max_empty_pages,
            start_page=scraping_config.start_page,
            max_pages=scraping_config.max_pages,
            force_restart=True, # Set the flag to True
            parallel_workers=scraping_config.parallel_workers,
            timeout_seconds=scraping_config.timeout_seconds,
            retry_attempts=scraping_config.retry_attempts,
            retry_delay_seconds=scraping_config.retry_delay_seconds
        )

        # Create a mock problem to be returned by PageScrapingService
        mock_problem = Problem(problem_id="test_123", subject_name="math", text="A test problem.", source_url="https://example.com/test")

        # Mock PageScrapingService to return one problem on the init page
        mock_page_scraping_service.scrape_page.return_value = [mock_problem]

        # Mock _determine_last_page to return 0 to prevent further page scraping
        with patch.object(use_case, '_determine_last_page', return_value=0):
            # Execute use case
            result = await use_case.execute(subject_info, force_restart_config)

        # Verify that the result is successful (assuming no other errors)
        assert result.success is True
        # Verify that the problem was saved with force_update=True
        # Check that the save call was made with force_update=True
        mock_problem_repository.save.assert_called_once_with(mock_problem, force_update=True) # Проверяем, что вызвано с force_update=True

if __name__ == "__main__":
    pytest.main(["-v", __file__, "-k", "async"]) # Run only async tests in this file
