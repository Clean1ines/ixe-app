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

    def create_problem(self, raw_data: Dict[str, Any]) -> Problem:
        """
        Create a Problem entity from raw scraped data.

        Args:
            raw_data: Dictionary containing raw data extracted from HTML.

        Returns:
            A fully constructed Problem entity.
        """
        # Example mapping - adapt to the exact keys returned by your HTML processor
        return Problem(
            problem_id=raw_data.get('problem_id', 'default_id'),
            subject_name=raw_data.get('subject_name', 'default_subject'),
            text=raw_data.get('text', 'default_text'),
            source_url=raw_data.get('source_url', 'default_url'),
            answer=raw_data.get('answer'),
            images=raw_data.get('images', []),
            files=raw_data.get('files', []),
            kes_codes=raw_data.get('kes_codes', []),
            topics=raw_data.get('topics', []),
            kos_codes=raw_data.get('kos_codes', []),
            form_id=raw_data.get('form_id'),
            fipi_proj_id=raw_data.get('fipi_proj_id'),
            difficulty_level=raw_data.get('difficulty_level'),
            task_number=raw_data.get('task_number'),
            exam_part=raw_data.get('exam_part'),
            # ... map other fields as necessary
        )
