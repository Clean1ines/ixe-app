from typing import List, Optional
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.models.problem import Problem

class FakeProblemRepository(IProblemRepository):
    """
    In-memory repository implementation for testing.
    Allows state verification without database dependencies.
    """
    
    def __init__(self):
        self._problems = []
    
    async def save(self, problem: Problem, force_update: bool = False) -> None:
        existing = next((p for p in self._problems if p.problem_id == problem.problem_id), None)
        
        if existing and not force_update:
            return
        elif existing and force_update:
            idx = self._problems.index(existing)
            self._problems[idx] = problem
        else:
            self._problems.append(problem)
    
    async def get_by_id(self, problem_id: str) -> Optional[Problem]:
        return next((p for p in self._problems if p.problem_id == problem_id), None)
    
    async def get_by_subject(self, subject_name: str) -> List[Problem]:
        return [p for p in self._problems if p.subject_name == subject_name]
    
    def clear(self):
        self._problems = []
    
    @property
    def all_problems(self):
        return self._problems.copy()
