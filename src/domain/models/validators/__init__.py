from abc import ABC, abstractmethod
from typing import Any

class IProblemValidator(ABC):
    """Interface for Problem validation components."""
    
    @abstractmethod
    def validate(self, problem: 'Problem') -> None:
        """Validate the problem instance. Raises ValueError if invalid."""
        pass

from .text_validator import TextValidator
from .difficulty_validator import DifficultyValidator
from .task_number_validator import TaskNumberValidator
from .exam_part_validator import ExamPartValidator
from .composite_validator import CompositeProblemValidator

__all__ = [
    'IProblemValidator',
    'TextValidator',
    'DifficultyValidator',
    'TaskNumberValidator',
    'ExamPartValidator',
    'CompositeProblemValidator',
]
