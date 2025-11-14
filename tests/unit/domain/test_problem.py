"""
Unit tests for the Problem domain entity.

These tests verify the behavior, validation (invariants), and identity methods
of the Problem class.
"""
import pytest
from datetime import datetime
from src.domain.models.problem import Problem


class TestProblemCreation:
    """Tests for creating a Problem instance."""

    def test_creation_success(self):
        """Test successful creation of a Problem with valid data."""
        problem = Problem(
            problem_id="test_id_123",
            subject_name="Mathematics",
            text="Solve for x: x + 2 = 5",
            source_url="https://fipi.ru/test",
            answer="3",
            images=["image1.png"],
            files=["data.csv"],
            kes_codes=["1.1"],
            topics=["Algebra"],
            kos_codes=["3.2"],
            form_id="form_123",
            fipi_proj_id="proj_abc",
            difficulty_level="basic",
            task_number=1,
            exam_part="Part 1"
        )

        assert problem.problem_id == "test_id_123"
        assert problem.subject_name == "Mathematics"
        assert problem.text == "Solve for x: x + 2 = 5"
        assert problem.source_url == "https://fipi.ru/test"
        assert problem.answer == "3"
        assert problem.images == ["image1.png"]
        assert problem.files == ["data.csv"]
        assert problem.kes_codes == ["1.1"]
        assert problem.topics == ["Algebra"]
        assert problem.kos_codes == ["3.2"]
        assert problem.form_id == "form_123"
        assert problem.fipi_proj_id == "proj_abc"
        assert problem.difficulty_level == "basic"
        assert problem.task_number == 1
        assert problem.exam_part == "Part 1"
        assert isinstance(problem.created_at, datetime)
        assert isinstance(problem.updated_at, datetime)

    def test_creation_defaults(self):
        """Test creation with minimal required data and default values."""
        problem = Problem(
            problem_id="minimal_id",
            subject_name="Physics",
            text="Describe gravity.",
            source_url="https://fipi.ru/minimal"
        )

        assert problem.problem_id == "minimal_id"
        assert problem.subject_name == "Physics"
        assert problem.text == "Describe gravity."
        assert problem.source_url == "https://fipi.ru/minimal"
        assert problem.answer is None
        assert problem.images == []  # Default
        assert problem.files == []  # Default
        assert problem.kes_codes == []  # Default
        assert problem.topics == []  # Default
        assert problem.kos_codes == []  # Default
        assert problem.form_id is None
        assert problem.fipi_proj_id is None
        assert problem.difficulty_level is None
        assert problem.task_number is None
        assert problem.exam_part is None
        assert isinstance(problem.created_at, datetime)
        assert isinstance(problem.updated_at, datetime)


class TestProblemValidation:
    """Tests for Problem validation (invariants)."""

    def test_creation_fails_empty_text(self):
        """Test that creation fails if text is empty."""
        with pytest.raises(ValueError, match="Problem text cannot be empty"):
            Problem(
                problem_id="id1",
                subject_name="Math",
                text="",  # Empty text
                source_url="https://fipi.ru/test"
            )

    def test_creation_fails_invalid_exam_part(self):
        """Test that creation fails if exam_part is invalid."""
        with pytest.raises(ValueError, match="Invalid exam part: Part X"):
            Problem(
                problem_id="id2",
                subject_name="Math",
                text="Problem text",
                source_url="https://fipi.ru/test",
                exam_part="Part X"  # Invalid
            )

    def test_creation_fails_task_number_out_of_range(self):
        """Test that creation fails if task_number is out of range."""
        with pytest.raises(ValueError, match="Task number 20 is out of range"):
            Problem(
                problem_id="id3",
                subject_name="Math",
                text="Problem text",
                source_url="https://fipi.ru/test",
                task_number=20  # Out of range (1-19)
            )

        with pytest.raises(ValueError, match="Task number 0 is out of range"):
            Problem(
                problem_id="id4",
                subject_name="Math",
                text="Problem text",
                source_url="https://fipi.ru/test",
                task_number=0  # Out of range (1-19)
            )

    def test_creation_fails_invalid_difficulty_level(self):
        """Test that creation fails if difficulty_level is invalid."""
        with pytest.raises(ValueError, match="Invalid difficulty level: expert"):
            Problem(
                problem_id="id5",
                subject_name="Math",
                text="Problem text",
                source_url="https://fipi.ru/test",
                difficulty_level="expert"  # Invalid
            )


class TestProblemIdentity:
    """Tests for Problem identity methods (__eq__, __hash__)."""

    def test_equality_same_id(self):
        """Test that Problems with the same problem_id are equal."""
        problem1 = Problem(
            problem_id="same_id",
            subject_name="Math",
            text="Problem 1",
            source_url="https://fipi.ru/1"
        )
        problem2 = Problem(
            problem_id="same_id",  # Same ID
            subject_name="Physics",  # Different subject
            text="Different text",  # Different text
            source_url="https://fipi.ru/2"  # Different URL
        )

        assert problem1 == problem2
        assert hash(problem1) == hash(problem2)

    def test_equality_different_id(self):
        """Test that Problems with different problem_id are not equal."""
        problem1 = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Problem 1",
            source_url="https://fipi.ru/1"
        )
        problem2 = Problem(
            problem_id="id2",  # Different ID
            subject_name="Math",
            text="Problem 1",
            source_url="https://fipi.ru/1"
        )

        assert problem1 != problem2
        assert hash(problem1) != hash(problem2)

    def test_equality_not_same_type(self):
        """Test that Problem is not equal to a non-Problem object."""
        problem = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test"
        )

        assert problem != "not a problem"
        assert problem != object()
        assert problem != 42


class TestProblemBehavior:
    """Tests for Problem behavior methods."""

    def test_is_answer_correct_true(self):
        """Test is_answer_correct returns True for a matching answer."""
        problem = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Solve x+1=2",
            source_url="https://fipi.ru/test",
            answer="1"  # Correct answer
        )

        assert problem.is_answer_correct("1") is True
        assert problem.is_answer_correct(" 1 ") is True  # Whitespace
        assert problem.is_answer_correct("1.0") is False  # Different format
        assert problem.is_answer_correct("2") is False  # Wrong answer

    def test_is_answer_correct_false_no_answer(self):
        """Test is_answer_correct returns False if no correct answer is set."""
        problem = Problem(
            problem_id="id2",
            subject_name="Math",
            text="Solve x+1=2",
            source_url="https://fipi.ru/test"
            # answer is None by default
        )

        assert problem.is_answer_correct("anything") is False

    def test_can_be_attempted_true(self):
        """Test can_be_attempted returns True if text is present."""
        problem = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Solve x+1=2",
            source_url="https://fipi.ru/test"
        )

        assert problem.can_be_attempted() is True

    def test_can_be_attempted_false_empty_text(self):
        """Test can_be_attempted returns False if text is empty."""
        # Note: This test relies on bypassing __post_init__ validation,
        # which is generally not recommended. In a real scenario, a Problem
        # object should never be created with an empty text due to validation.
        # This test might be less relevant if validation is always enforced strictly.
        # However, if the invariant could be bypassed elsewhere, this test checks the method.
        # For now, let's assume validation is strict and focus on the method logic itself.
        # We can test the logic by temporarily setting text to empty after creation,
        # though this changes the object's state.
        problem = Problem(
            problem_id="id2",
            subject_name="Math",
            text="Initial text",
            source_url="https://fipi.ru/test"
        )
        # Simulate a state where text might become empty (though validation should prevent it)
        original_text = problem.text
        problem.text = "" # This bypasses invariant check
        assert problem.can_be_attempted() is False
        problem.text = original_text # Restore

    def test_has_images_true(self):
        """Test has_images returns True if images list is not empty."""
        problem = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test",
            images=["img1.jpg", "img2.png"]  # Non-empty list
        )

        assert problem.has_images() is True

    def test_has_images_false_empty_list(self):
        """Test has_images returns False if images list is empty."""
        problem = Problem(
            problem_id="id2",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test"
            # images is [] by default
        )

        assert problem.has_images() is False

    def test_is_suitable_for_level_true(self):
        """Test is_suitable_for_level returns True for matching level."""
        problem = Problem(
            problem_id="id1",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test",
            difficulty_level="basic"
        )

        assert problem.is_suitable_for_level("basic") is True

    def test_is_suitable_for_level_false_not_matching(self):
        """Test is_suitable_for_level returns False for non-matching level."""
        problem = Problem(
            problem_id="id2",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test",
            difficulty_level="advanced"
        )

        assert problem.is_suitable_for_level("basic") is False

    def test_is_suitable_for_level_false_none_level(self):
        """Test is_suitable_for_level returns False if problem's level is None."""
        problem = Problem(
            problem_id="id3",
            subject_name="Math",
            text="Problem text",
            source_url="https://fipi.ru/test"
            # difficulty_level is None by default
        )

        assert problem.is_suitable_for_level("basic") is False
        assert problem.is_suitable_for_level("advanced") is False

if __name__ == "__main__":
    pytest.main(["-v", __file__])
