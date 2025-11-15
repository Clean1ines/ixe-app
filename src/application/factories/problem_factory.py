"""
Application factory for creating Problem entities from raw data.

This factory implements the IProblemFactory interface and handles the
conversion from raw scraped data (e.g., dict) to a domain Problem entity.
"""
from typing import Dict, Any
from src.domain.models.problem import Problem
from src.application.interfaces.factories.i_problem_factory import IProblemFactory

class ProblemFactory(IProblemFactory):
    """
    Factory for creating Problem entities from raw data.
    """

    def create_problem(self, raw_ Dict[str, Any]) -> Problem: # Исправленная строка
        """
        Create a Problem entity from raw scraped data.

        Args:
            raw_ Dictionary containing raw data extracted from HTML (e.g., by PageScrapingService).

        Returns:
            A fully constructed Problem entity.
        """
        return Problem(
            problem_id=raw_data["problem_id"],
            subject_name=raw_data["subject_name"],
            text=raw_data["text"],
            source_url=raw_data["source_url"],
            answer=raw_data.get("answer"),
            images=raw_data.get("images", []),
            files=raw_data.get("files", []),
            kes_codes=raw_data.get("kes_codes", []),
            topics=raw_data.get("topics", []),
            kos_codes=raw_data.get("kos_codes", []),
            difficulty_level=raw_data.get("difficulty_level"),
            task_number=raw_data.get("task_number"),
            exam_part=raw_data.get("exam_part"),
            fipi_proj_id=raw_data.get("fipi_proj_id"),
        )

