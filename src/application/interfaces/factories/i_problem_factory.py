"""
Application interface for Problem factory operations.

This interface defines the contract for creating Problem entities from raw scraped data,
allowing the application layer to remain independent of the specific creation logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.domain.models.problem import Problem


class IProblemFactory(ABC):
    """
    Interface for creating Problem entities from raw data.
    """

    @abstractmethod
    def create_problem(self, raw_data: Dict[str, Any]) -> Problem:
        """
        Create a Problem entity from raw scraped data.

        Args:
            raw_data: Dictionary containing raw data extracted from HTML.

        Returns:
            A fully constructed Problem entity.
        """
        raise NotImplementedError

