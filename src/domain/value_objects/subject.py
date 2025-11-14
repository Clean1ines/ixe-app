from dataclasses import dataclass
from typing import Dict, Optional

# Пример маппинга, можно хранить в отдельном файле или загружать из конфига
SUBJECT_MAPPING = {
    "math": {
        "official_name": "Математика (профильный уровень)",
        "subject_key": "mathematics",
        "proj_id": "12345",
        "exam_year": 2026
    },
    "rus": {
        "official_name": "Русский язык",
        "subject_key": "russian",
        "proj_id": "67890",
        "exam_year": 2026
    },
    "phys": {
        "official_name": "Физика",
        "subject_key": "physics",
        "proj_id": "11111",
        "exam_year": 2026
    },
    # ... другие предметы
}

@dataclass(frozen=True)
class Subject:
    """
    Value Object representing a subject for an EGE problem.
    Contains all identifiers and names associated with the subject.
    """
    alias: str  # e.g., "math", "rus"
    official_name: str  # e.g., "Математика (профильный уровень)"
    subject_key: str  # e.g., "mathematics", "russian"
    proj_id: str  # e.g., "12345" - FIPI project ID
    exam_year: int  # e.g., 2026

    def __post_init__(self):
        """Validate the subject data after initialization."""
        if not all([self.alias, self.official_name, self.subject_key, self.proj_id]):
            raise ValueError("All subject fields must be non-empty")
        if self.exam_year < 2000 or self.exam_year > 2100:  # Простая валидация года
            raise ValueError(f"Invalid exam year: {self.exam_year}")

    @classmethod
    def from_alias(cls, alias: str) -> 'Subject':
        """
        Create a Subject instance from its alias using the mapping.
        Args:
            alias: Short alias like 'math', 'rus'.
        Returns:
            Subject instance.
        Raises:
            ValueError: If alias is not found in mapping.
        """
        if alias not in SUBJECT_MAPPING:
            raise ValueError(f"Unknown subject alias: {alias}")
        data = SUBJECT_MAPPING[alias]
        return cls(
            alias=alias,
            official_name=data["official_name"],
            subject_key=data["subject_key"],
            proj_id=data["proj_id"],
            exam_year=data["exam_year"]
        )

    def __str__(self):
        """Return the official name for string representation."""
        return self.official_name
