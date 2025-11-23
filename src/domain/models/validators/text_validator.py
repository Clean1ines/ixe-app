from typing import Any
from src.domain.models.validators import IProblemValidator

class TextValidator(IProblemValidator):
    """Validates the text field of a Problem."""
    
    def validate(self, problem: 'Problem') -> None:
        if not problem.text.strip():
            raise ValueError("Problem text cannot be empty")
