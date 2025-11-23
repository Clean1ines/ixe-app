from typing import List
from src.domain.models.validators import IProblemValidator

class CompositeProblemValidator(IProblemValidator):
    """Combines multiple validators into a single validator."""
    
    def __init__(self, validators: List[IProblemValidator]):
        self._validators = validators
    
    def validate(self, problem: 'Problem') -> None:
        for validator in self._validators:
            validator.validate(problem)
