from typing import List, Optional
"""
Domain interface for Problem repository operations.

This interface defines the contract for persisting and retrieving Problem entities,
allowing the domain layer to remain independent of the specific infrastructure
implementation (e.g., SQL, NoSQL, file-based).
"""
from abc import abstractmethod
from src.domain.models.problem import Problem


class IProblemRepository:
    """
    Interface for operations related to Problem persistence and retrieval.
    """

    @abstractmethod
    async def save(self, problem: Problem, force_update: bool = False) -> None:
        """
        Save a Problem entity to the persistence layer.

        Args:
            problem: The Problem entity to save.
            force_update: If True, forces updating the problem even if it already exists (e.g., for re-scraping).
                          If False, applies default upsert logic.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, problem_id: str) -> Optional[Problem]:
        """
        Retrieve a Problem entity by its unique identifier.

        Args:
            problem_id: The unique identifier (str) of the problem.

        Returns:
            The Problem entity if found, otherwise None.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_subject(self, subject_name: str) -> List[Problem]:
        """
        Retrieve all Problem entities associated with a specific subject name.

        Args:
            subject_name: The name of the subject (e.g., "mathematics").

        Returns:
            A list of Problem entities for the given subject name.
        """
        raise NotImplementedError
