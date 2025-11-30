"""
Unit tests for the ScrapingResult value object.
"""
import pytest
from datetime import datetime, timedelta
from src.domain.value_objects.scraping.scraping_result import ScrapingResult


class TestScrapingResult:
    """Tests for ScrapingResult value object."""

    def test_creation_success(self):
        """Test successful creation of a ScrapingResult with valid data."""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 1, 0)  # 1 minute later

        result = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=5,
            total_problems_found=10,
            total_problems_saved=8,
            page_results=[{"page": 1, "found": 2, "saved": 2}],
            errors=[],
            start_time=start_time,
            end_time=end_time,
            metadata={"extra": "info"}
        )

        assert result.subject_name == "Math"
        assert result.success is True
        assert result.total_pages == 5
        assert result.total_problems_found == 10
        assert result.total_problems_saved == 8
        assert result.page_results == [{"page": 1, "found": 2, "saved": 2}]
        assert result.errors == []
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.metadata == {"extra": "info"}

    def test_duration_seconds(self):
        """Test the duration_seconds property."""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 1, 30)  # 1 minute 30 seconds later

        result = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=1,
            total_problems_found=1,
            total_problems_saved=1,
            page_results=[],
            errors=[],
            start_time=start_time,
            end_time=end_time
        )

        assert result.duration_seconds == 90.0  # 1 min 30 sec = 90 sec

    def test_success_rate(self):
        """Test the success_rate property."""
        # Case 1: Some problems saved
        result1 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=10,
            total_problems_found=10,
            total_problems_saved=8,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        # Success rate is based on problems_saved / total_pages
        assert result1.success_rate == (8 / 10) * 100.0  # 80.0%

        # Case 2: No pages processed
        result2 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=0,
            total_problems_found=0,
            total_problems_saved=0,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        assert result2.success_rate == 0.0  # Avoid division by zero

        # Case 3: All pages processed, no problems saved
        result3 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=5,
            total_problems_found=0,
            total_problems_saved=0,
            page_results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        assert result3.success_rate == (0 / 5) * 100.0  # 0.0%

    def test_equality_same_values(self):
        """Test that ScrapingResult instances with same values are equal."""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 1, 0)

        result1 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=1,
            total_problems_found=1,
            total_problems_saved=1,
            page_results=[],
            errors=[],
            start_time=start_time,
            end_time=end_time
        )
        result2 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=1,
            total_problems_found=1,
            total_problems_saved=1,
            page_results=[],
            errors=[],
            start_time=start_time,
            end_time=end_time
        )

        assert result1 == result2
        # Note: hash is not tested as ScrapingResult is not hashable due to mutable fields (List, Dict)

    def test_equality_different_values(self):
        """Test that ScrapingResult instances with different values are not equal."""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 1, 0)

        result1 = ScrapingResult(
            subject_name="Math",
            success=True,
            total_pages=1,
            total_problems_found=1,
            total_problems_saved=1,
            page_results=[],
            errors=[],
            start_time=start_time,
            end_time=end_time
        )
        result2 = ScrapingResult(
            subject_name="Rus",  # Different subject
            success=True,
            total_pages=1,
            total_problems_found=1,
            total_problems_saved=1,
            page_results=[],
            errors=[],
            start_time=start_time,
            end_time=end_time
        )

        assert result1 != result2
        # Note: hash is not tested as ScrapingResult is not hashable due to mutable fields (List, Dict)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
