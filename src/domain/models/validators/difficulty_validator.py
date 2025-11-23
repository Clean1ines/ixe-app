from typing import Any
from src.domain.models.validators import IProblemValidator

class DifficultyValidator(IProblemValidator):
    """Validates the difficulty_level field of a Problem."""
    
    def validate(self, problem: 'Problem') -> None:
        if problem.difficulty_level and problem.difficulty_level not in ["basic", "advanced"]:
            raise ValueError(f"Invalid difficulty level: {problem.difficulty_level}")
