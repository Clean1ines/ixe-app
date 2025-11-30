from abc import ABC, abstractmethod
from typing import Any
from src.domain.models.problem import Problem


class IProblemFactory(ABC):
    """Interface for Problem factory components."""

    @abstractmethod
    def create_problem(self, raw_data: dict[str, Any]) -> Problem:
        """Create a Problem instance from raw data.
        
        Args:
            raw_data: Dictionary containing problem data
            
        Returns:
            Problem: Created problem instance
        """
        pass
