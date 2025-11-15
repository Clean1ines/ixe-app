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

    def create_problem(self, raw_data: Dict[str, Any]) -> Problem: # ИСПРАВЛЕНО: Полностью переписана сигнатура
        """
        Create a Problem entity from raw scraped data.

        Args:
            raw_ Dictionary containing raw data extracted from HTML (e.g., by PageScrapingService).

        Returns:
            A fully constructed Problem entity.
        """
        # Map raw data dictionary keys to Problem entity fields
        # This is where the mapping between scraped data structure and domain entity happens
        # Validation of the raw data could also occur here if not done by processors or extraction step
        return Problem(
            problem_id=raw_data["problem_id"],
            subject_name=raw_data["subject_name"],
            text=raw_data["text"],
            source_url=raw_data["source_url"],
            answer=raw_data.get("answer"), # Optional
            images=raw_data.get("images", []), # Optional, default to []
            files=raw_data.get("files", []), # Optional, default to []
            kes_codes=raw_data.get("kes_codes", []), # Optional, default to []
            topics=raw_data.get("topics", []), # Optional, default to []
            kos_codes=raw_data.get("kos_codes", []), # Optional, default to []
            difficulty_level=raw_data.get("difficulty_level"), # Optional
            task_number=raw_data.get("task_number"), # Optional
            exam_part=raw_data.get("exam_part"), # Optional
            fipi_proj_id=raw_data.get("fipi_proj_id"), # Optional
            # Assign default values for non-optional fields if not present in raw_data (though they should be)
            # form_id=raw_data.get("form_id"), # Optional
            # created_at и updated_at будут установлены в __post_init__ Problem
        )
