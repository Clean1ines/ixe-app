from typing import Any
from src.domain.models.validators import IProblemValidator

class ExamPartValidator(IProblemValidator):
    """Validates the exam_part field of a Problem."""
    
    def validate(self, problem: 'Problem') -> None:
        if problem.exam_part and problem.exam_part not in ["Part 1", "Part 2"]:
            raise ValueError(f"Invalid exam part: {problem.exam_part}")
