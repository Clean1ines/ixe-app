"""
Domain interface for task classification operations.
This interface defines the contract for classifying a task based on extracted
codes and other attributes, allowing the domain layer to remain independent of
the specific classification logic implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ITaskClassifier(ABC):
    """Domain interface for task classification operations."""
    
    @abstractmethod
    def classify_task(
        self, 
        kes_codes: List[str], 
        kos_codes: List[str], 
        answer_type: str
    ) -> Dict[str, Any]:
        """
        Classify a task based on KES/KOS codes and return classification result.

        Args:
            kes_codes: List of KES codes extracted from the problem block.
            kos_codes: List of KOS codes extracted from the problem block.
            answer_type: The detected type of the answer (e.g., "number", "text").

        Returns:
            A dictionary containing the classification result 
            (e.g., task_number, difficulty_level, exam_part).
        """
        pass
