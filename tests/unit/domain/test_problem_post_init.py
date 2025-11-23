"""
Unit tests for Problem.__post_init__ method.
These tests verify the validation and default value assignment logic.
"""
import pytest
from datetime import datetime
from src.domain.models.problem import Problem


class TestProblemPostInit:

    def test_post_init_sets_defaults_correctly(self):
        """Test that __post_init__ sets default empty lists and current datetime."""
        problem = Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com"
        )

        assert problem.images == []
        assert problem.files == []
        assert problem.kes_codes == []
        assert problem.topics == []
        assert problem.kos_codes == []
        assert problem.created_at is not None
        assert problem.updated_at is not None
        assert isinstance(problem.created_at, datetime)
        assert isinstance(problem.updated_at, datetime)

    def test_post_init_preserves_provided_lists(self):
        """Test that __post_init__ does not overwrite provided lists."""
        provided_images = ["img1.png"]
        provided_files = ["file1.pdf"]
        provided_kes = ["KES001"]
        provided_topics = ["Topic1"]
        provided_kos = ["KOS001"]

        problem = Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            images=provided_images,
            files=provided_files,
            kes_codes=provided_kes,
            topics=provided_topics,
            kos_codes=provided_kos
        )

        assert problem.images == provided_images
        assert problem.files == provided_files
        assert problem.kes_codes == provided_kes
        assert problem.topics == provided_topics
        assert problem.kos_codes == provided_kos

    def test_post_init_sets_current_datetime_if_none_provided(self):
        """Test that __post_init__ sets current datetime if not provided."""
        before_creation = datetime.now()
        problem = Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com"
        )
        after_creation = datetime.now()

        assert before_creation <= problem.created_at <= after_creation
        assert before_creation <= problem.updated_at <= after_creation

    def test_post_init_preserves_provided_datetime(self):
        """Test that __post_init__ does not overwrite provided datetime."""
        custom_dt = datetime(2023, 1, 1, 12, 0, 0)
        problem = Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            created_at=custom_dt,
            updated_at=custom_dt
        )

        assert problem.created_at == custom_dt
        assert problem.updated_at == custom_dt

    def test_post_init_raises_for_empty_text(self):
        """Test that __post_init__ raises ValueError for empty text."""
        with pytest.raises(ValueError, match="Problem text cannot be empty"):
            Problem(
                problem_id="test_123",
                subject_name="Math",
                text="",
                source_url="https://example.com"
            )

    def test_post_init_raises_for_whitespace_only_text(self):
        """Test that __post_init__ raises ValueError for whitespace-only text."""
        with pytest.raises(ValueError, match="Problem text cannot be empty"):
            Problem(
                problem_id="test_123",
                subject_name="Math",
                text="   \n\t  ",
                source_url="https://example.com"
            )

    def test_post_init_validates_exam_part_correctly(self):
        """Test that __post_init__ validates exam_part values."""
        # Valid values should not raise
        Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            exam_part="Part 1"
        )
        Problem(
            problem_id="test_124",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            exam_part="Part 2"
        )

        # Invalid value should raise
        with pytest.raises(ValueError, match="Invalid exam part: InvalidPart"):
            Problem(
                problem_id="test_125",
                subject_name="Math",
                text="Sample problem text",
                source_url="https://example.com",
                exam_part="InvalidPart"
            )

    def test_post_init_validates_task_number_correctly(self):
        """Test that __post_init__ validates task_number range."""
        # Valid values should not raise
        for num in [1, 10, 19]:
            Problem(
                problem_id=f"test_{num}",
                subject_name="Math",
                text="Sample problem text",
                source_url="https://example.com",
                task_number=num
            )

        # Invalid values should raise
        with pytest.raises(ValueError, match=f"Task number 0 is out of range"):
            Problem(
                problem_id="test_0",
                subject_name="Math",
                text="Sample problem text",
                source_url="https://example.com",
                task_number=0
            )

        with pytest.raises(ValueError, match=f"Task number 20 is out of range"):
            Problem(
                problem_id="test_20",
                subject_name="Math",
                text="Sample problem text",
                source_url="https://example.com",
                task_number=20
            )

    def test_post_init_validates_difficulty_level_correctly(self):
        """Test that __post_init__ validates difficulty_level values."""
        # Valid values should not raise
        Problem(
            problem_id="test_123",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            difficulty_level="basic"
        )
        Problem(
            problem_id="test_124",
            subject_name="Math",
            text="Sample problem text",
            source_url="https://example.com",
            difficulty_level="advanced"
        )

        # Invalid value should raise
        with pytest.raises(ValueError, match="Invalid difficulty level: invalid_level"):
            Problem(
                problem_id="test_125",
                subject_name="Math",
                text="Sample problem text",
                source_url="https://example.com",
                difficulty_level="invalid_level"
            )
