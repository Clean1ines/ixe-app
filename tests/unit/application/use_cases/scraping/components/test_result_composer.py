import pytest
from datetime import datetime, timedelta
from src.application.use_cases.scraping.components.result_composer import ResultComposer
from src.application.use_cases.scraping.components.data_structures import PageResult, LoopResult
from src.domain.value_objects.scraping.subject_info import SubjectInfo


@pytest.fixture
def subject_info():
    return SubjectInfo(
        alias='math',
        official_name='Математика. Базовый уровень',
        proj_id='E040A72A1A3DABA14C90C97E0B6EE7DC',
        exam_year=2026
    )


@pytest.fixture
def loop_result():
    page_results = [
        PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.5),
        PageResult(page_number=2, problems_found=3, problems_saved=3, assets_downloaded=2, page_duration_seconds=2.0),
    ]
    return LoopResult(
        page_results=page_results,
        total_problems_found=5,
        total_problems_saved=5,
        total_assets_downloaded=3,
        errors=[],
        last_processed_page=2
    )


@pytest.fixture
def loop_result_with_errors():
    page_results = [
        PageResult(page_number=1, problems_found=2, problems_saved=2, assets_downloaded=1, page_duration_seconds=1.5),
        PageResult(page_number=2, problems_found=0, problems_saved=0, assets_downloaded=0, page_duration_seconds=1.0, error="Page error"),
    ]
    return LoopResult(
        page_results=page_results,
        total_problems_found=2,
        total_problems_saved=2,
        total_assets_downloaded=1,
        errors=["Page error"],
        last_processed_page=2
    )


class TestResultComposer:
    def test_compose_final_result_success(self, subject_info, loop_result):
        """Test composing successful result."""
        # Arrange
        composer = ResultComposer()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)

        # Act
        result = composer.compose_final_result(subject_info, loop_result, start_time, end_time)

        # Assert
        assert result.subject_name == subject_info.official_name
        assert result.success is True
        assert result.total_pages == 2
        assert result.total_problems_found == 5
        assert result.total_problems_saved == 5
        assert len(result.page_results) == 2
        assert len(result.errors) == 0
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.duration_seconds == 10.0
        assert result.metadata['assets_downloaded'] == 3
        assert result.metadata['last_processed_page'] == 2

    def test_compose_final_result_with_errors(self, subject_info, loop_result_with_errors):
        """Test composing result with errors."""
        # Arrange
        composer = ResultComposer()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)

        # Act
        result = composer.compose_final_result(subject_info, loop_result_with_errors, start_time, end_time)

        # Assert
        assert result.subject_name == subject_info.official_name
        assert result.success is False
        assert result.total_pages == 2
        assert result.total_problems_found == 2
        assert result.total_problems_saved == 2
        assert len(result.errors) == 1
        assert "Page error" in result.errors[0]
        assert result.duration_seconds == 5.0

    def test_compose_final_result_empty(self, subject_info):
        """Test composing result with no pages processed."""
        # Arrange
        composer = ResultComposer()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        empty_loop_result = LoopResult(
            page_results=[],
            total_problems_found=0,
            total_problems_saved=0,
            total_assets_downloaded=0,
            errors=[],
            last_processed_page=0
        )

        # Act
        result = composer.compose_final_result(subject_info, empty_loop_result, start_time, end_time)

        # Assert
        assert result.subject_name == subject_info.official_name
        assert result.success is True
        assert result.total_pages == 0
        assert result.total_problems_found == 0
        assert result.total_problems_saved == 0
        assert len(result.page_results) == 0
        assert len(result.errors) == 0
        assert result.duration_seconds == 1.0
