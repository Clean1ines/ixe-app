from datetime import datetime
from typing import Any
from src.domain.models.problem import Problem
from src.application.interfaces.factories.i_problem_factory import IProblemFactory


class ProblemFactory(IProblemFactory):
    """Factory for creating Problem entities."""
    
    def create_problem(self, raw_data: dict[str, Any]) -> Problem:
        """Create a new Problem instance from raw data."""
        return Problem(
            problem_id=str(raw_data.get('problem_id', '')),
            subject_name=str(raw_data.get('subject_name', '')),
            text=str(raw_data.get('text', '')),
            source_url=str(raw_data.get('source_url', '')),
            difficulty_level=raw_data.get('difficulty_level'),
            task_number=raw_data.get('task_number'),
            exam_part=raw_data.get('exam_part'),
            answer=raw_data.get('answer'),
            images=raw_data.get('images', []),
            files=raw_data.get('files', []),
            kes_codes=raw_data.get('kes_codes', []),
            topics=raw_data.get('topics', []),
            kos_codes=raw_data.get('kos_codes', []),
            form_id=raw_data.get('form_id'),
            fipi_proj_id=raw_data.get('fipi_proj_id'),
            created_at=raw_data.get('created_at', datetime.now()),
            updated_at=raw_data.get('updated_at')
        )
