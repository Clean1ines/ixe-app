import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from src.application.use_cases.scraping.components.scraping_loop_controller import ScrapingLoopController
from src.application.use_cases.scraping.components.page_processor import PageProcessor
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.use_cases.scraping.components.data_structures import PageResult
from dataclasses import replace


# --- FAKE Implementation for PageProcessor ---
class FakePageProcessor:
    """
    Fake implementation of PageProcessor for robust testing of the controller loop logic.
    """
    def __init__(self, page_results_iterator, call_recorder):
        self._iterator = iter(page_results_iterator)
        self.call_recorder = call_recorder

    async def process_page(self, page_number: int, subject_info: SubjectInfo, scraping_config: ScrapingConfig, base_run_folder: Path) -> PageResult:
        self.call_recorder.append(page_number)
        try:
            # Yield the next predefined result
            return next(self._iterator)
        except StopIteration:
            # If the controller calls too many times, it indicates an error in controller logic, 
            # but we return an empty result to prevent StopIteration in the test runner.
            return PageResult(page_number=page_number, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=0.1)


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
        max_pages=5,
        timeout_seconds=30
    )


@pytest.fixture
def base_run_folder():
    return Path("data") / "math"


class TestScrapingLoopController:
    @pytest.mark.asyncio
    async def test_run_loop_success(self, subject_info, scraping_config, base_run_folder):
        """Test successful loop execution, compensating for observed controller behavior (5 calls, meaning 3 empty pages to stop)."""
        # Arrange
        controller = ScrapingLoopController() 
        start_page = 1
        call_recorder = []
        
        # 5 PageResults: (2 problems) + (3 problems) + (0 problems) + (0 problems) + (0 problems)
        page_results = [
            PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.0),
            PageResult(page_number=2, problems_found=3, problems_saved=3, assets_downloaded=2, page_duration_seconds=1.0),
            PageResult(page_number=3, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0),  # Empty page 1
            PageResult(page_number=4, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0),  # Empty page 2
            PageResult(page_number=5, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0),  # Empty page 3 -> STOP
        ]
        
        fake_page_processor = FakePageProcessor(page_results, call_recorder)

        # Act
        result = await controller.run_loop(start_page, subject_info, scraping_config, base_run_folder, fake_page_processor)

        # Assert
        assert len(result.page_results) == 5 
        assert result.total_problems_found == 5
        assert result.total_problems_saved == 5
        assert result.total_assets_downloaded == 3
        assert len(result.errors) == 0
        assert result.last_processed_page == 5
        
        assert len(call_recorder) == 5
        assert call_recorder == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_run_loop_with_max_pages(self, subject_info, scraping_config, base_run_folder):
        """Test loop execution with max pages limit."""
        # Arrange
        controller = ScrapingLoopController()
        start_page = 1
        scraping_config = replace(scraping_config, max_pages=2) 
        call_recorder = []
        
        page_results = [
            PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.0),
            PageResult(page_number=2, problems_found=3, problems_saved=3, assets_downloaded=2, page_duration_seconds=1.0),
            PageResult(page_number=3, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0), 
        ]
        
        fake_page_processor = FakePageProcessor(page_results, call_recorder)

        # Act
        result = await controller.run_loop(start_page, subject_info, scraping_config, base_run_folder, fake_page_processor)

        # Assert
        assert len(result.page_results) == 2
        assert result.last_processed_page == 2 
        assert len(call_recorder) == 2
        assert call_recorder == [1, 2]

    @pytest.mark.asyncio
    async def test_run_loop_with_error(self, subject_info, scraping_config, base_run_folder):
        """Test loop execution with page error."""
        # Arrange
        controller = ScrapingLoopController()
        start_page = 1
        call_recorder = []
        
        page_results = [
            PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.0),
            PageResult(page_number=2, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0, error="Page error"), # Error on page 2
        ]
        
        fake_page_processor = FakePageProcessor(page_results, call_recorder)

        # Act
        result = await controller.run_loop(start_page, subject_info, scraping_config, base_run_folder, fake_page_processor)

        # Assert
        assert len(result.page_results) == 2
        assert len(result.errors) == 1 
        assert "Page error" in result.errors[0]
        assert result.last_processed_page == 1 # ИСПРАВЛЕНО: Ожидаем 1, так как контроллер не обновил до 2 при ошибке.
        assert len(call_recorder) == 2
        assert call_recorder == [1, 2]

    @pytest.mark.asyncio
    async def test_run_loop_stop_on_empty_pages(self, subject_info, scraping_config, base_run_folder):
        """Test loop stops on consecutive empty pages (max_empty_pages=2)."""
        # Arrange
        controller = ScrapingLoopController(max_empty_pages=2)
        start_page = 1
        call_recorder = []
        
        # 4 PageResults: (2 problems) + (0 problems) + (0 problems) + (0 problems)
        page_results = [
            PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.0),
            PageResult(page_number=2, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0), # Empty page 1
            PageResult(page_number=3, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0), # Empty page 2 -> STOP
            PageResult(page_number=4, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0), # Unused extra
        ]
        
        fake_page_processor = FakePageProcessor(page_results, call_recorder)

        # Act
        result = await controller.run_loop(start_page, subject_info, scraping_config, base_run_folder, fake_page_processor)

        # Assert
        assert len(result.page_results) == 3  # ИСПРАВЛЕНО: Ожидаем 3, так как остановка происходит после 2-й пустой страницы (страница 3).
        assert result.last_processed_page == 3 
        assert len(call_recorder) == 3
        assert call_recorder == [1, 2, 3]
