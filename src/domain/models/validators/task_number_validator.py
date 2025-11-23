from typing import Any
from src.domain.models.validators import IProblemValidator

class TaskNumberValidator(IProblemValidator):
    """Validates the task_number field of a Problem."""
    
    def validate(self, problem: 'Problem') -> None:
        if problem.task_number is not None and (problem.task_number < 1 or problem.task_number > 19):
            raise ValueError(f"Task number {problem.task_number} is out of range (1-19)")
