from typing import Optional
from dataclasses import dataclass
from .difficulty_level_enum import DifficultyLevelEnum  # Импортируем enum


@dataclass(frozen=True)
class DifficultyLevel:
    """
    Value Object representing the difficulty level of a problem.
    """
    value: DifficultyLevelEnum

    def __post_init__(self):
        """Validate the difficulty level value after initialization."""
        if not isinstance(self.value, DifficultyLevelEnum):
            raise ValueError(f"DifficultyLevel value must be a DifficultyLevelEnum, got: {type(self.value)}")

    def __str__(self):
        """Return the string value of the enum."""
        return self.value.value

    @classmethod
    def from_string(cls, level_str: str) -> Optional['DifficultyLevel']:
        """
        Create a DifficultyLevel instance from a string.
        Args:
            level_str: String representation like 'basic', 'intermediate', 'advanced'.
        Returns:
            DifficultyLevel instance or None if string is invalid.
        """
        try:
            enum_value = DifficultyLevelEnum[level_str.upper()]
            return cls(enum_value)
        except KeyError:
            return None
