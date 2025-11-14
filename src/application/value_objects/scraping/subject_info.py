"""
Value Object representing information required to scrape a specific subject.

This includes identifiers needed to target the correct
set of problems on the FIPI website.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SubjectInfo:
    """
    Value Object for subject-specific scraping parameters.
    """
    alias: str          # e.g., "math", "rus" - short identifier for code, used for internal logic
    official_name: str  # e.g., "Математика (профильный уровень)" - for logging, display
    proj_id: str        # e.g., "12345" - FIPI project ID
    exam_year: int      # e.g., 2026

    def __post_init__(self):
        """Validate the subject information after initialization."""
        if not self.alias or not isinstance(self.alias, str):
            raise ValueError("Alias must be a non-empty string")
        if not self.official_name or not isinstance(self.official_name, str):
            raise ValueError("Official name must be a non-empty string")
        if not self.proj_id or not isinstance(self.proj_id, str):
            raise ValueError("Project ID must be a non-empty string")
        if self.exam_year < 2000 or self.exam_year > 2100:  # Simple year validation
            raise ValueError(f"Invalid exam year: {self.exam_year}")
