"""
Unit tests for the SubjectInfo value object.
"""
import pytest
from src.domain.value_objects.scraping.subject_info import SubjectInfo


class TestSubjectInfoCreation:
    """Tests for creating a SubjectInfo instance."""

    def test_creation_success(self):
        """Test successful creation of a SubjectInfo with valid data."""
        subject_info = SubjectInfo(
            alias="math",
            official_name="Математика (профильный уровень)",
            proj_id="12345",
            exam_year=2026
        )

        assert subject_info.alias == "math"
        assert subject_info.official_name == "Математика (профильный уровень)"
        assert subject_info.proj_id == "12345"
        assert subject_info.exam_year == 2026

    def test_creation_fails_empty_alias(self):
        """Test that creation fails if alias is empty."""
        with pytest.raises(ValueError, match="Alias must be a non-empty string"):
            SubjectInfo(
                alias="",  # Empty alias
                official_name="Math",
                proj_id="12345",
                exam_year=2026
            )

    def test_creation_fails_empty_official_name(self):
        """Test that creation fails if official_name is empty."""
        with pytest.raises(ValueError, match="Official name must be a non-empty string"):
            SubjectInfo(
                alias="math",
                official_name="",  # Empty official_name
                proj_id="12345",
                exam_year=2026
            )

    def test_creation_fails_empty_proj_id(self):
        """Test that creation fails if proj_id is empty."""
        with pytest.raises(ValueError, match="Project ID must be a non-empty string"):
            SubjectInfo(
                alias="math",
                official_name="Math",
                proj_id="",  # Empty proj_id
                exam_year=2026
            )

    def test_creation_fails_invalid_exam_year(self):
        """Test that creation fails if exam_year is out of range."""
        with pytest.raises(ValueError, match="Invalid exam year: 1800"):
            SubjectInfo(
                alias="math",
                official_name="Math",
                proj_id="12345",
                exam_year=1800  # Invalid year
            )

        with pytest.raises(ValueError, match="Invalid exam year: 3000"):
            SubjectInfo(
                alias="math",
                official_name="Math",
                proj_id="12345",
                exam_year=3000  # Invalid year
            )

    def test_equality_same_values(self):
        """Test that SubjectInfo instances with same values are equal."""
        info1 = SubjectInfo(alias="math", official_name="Math", proj_id="123", exam_year=2026)
        info2 = SubjectInfo(alias="math", official_name="Math", proj_id="123", exam_year=2026)

        assert info1 == info2
        assert hash(info1) == hash(info2)

    def test_equality_different_values(self):
        """Test that SubjectInfo instances with different values are not equal."""
        info1 = SubjectInfo(alias="math", official_name="Math", proj_id="123", exam_year=2026)
        info2 = SubjectInfo(alias="rus", official_name="Math", proj_id="123", exam_year=2026)  # Different alias
        info3 = SubjectInfo(alias="math", official_name="Rus", proj_id="123", exam_year=2026)  # Different name

        assert info1 != info2
        assert info1 != info3
        assert hash(info1) != hash(info2) # Hashes likely different if values differ
        assert hash(info1) != hash(info3) # Hashes likely different if values differ

if __name__ == "__main__":
    pytest.main(["-v", __file__])
