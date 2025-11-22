"""
Fake implementation of IProblemRepository for testing.

This is a working implementation that uses in-memory storage rather than a real database.
It's designed for tests where we need to verify state rather than interactions.
"""
from typing import List, Optional
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.models.problem import Problem

class FakeProblemRepository(IProblemRepository):
    """
    Fake repository implementation for testing that stores problems in memory.
    
    Unlike mocks that verify interactions, this fake allows us to verify final state
    by inspecting the stored problems after test execution.
    """
    
    def __init__(self):
        self._problems = []
    
    async def save(self, problem: Problem, force_update: bool = False) -> None:
        """Save a problem to the in-memory store."""
        # Check if problem already exists
        existing = next((p for p in self._problems if p.problem_id == problem.problem_id), None)
        
        if existing and not force_update:
            # Skip saving if exists and not forced
            return
        elif existing and force_update:
            # Update existing problem
            idx = self._problems.index(existing)
            self._problems[idx] = problem
        else:
            # Add new problem
            self._problems.append(problem)
    
    async def get_by_id(self, problem_id: str) -> Optional[Problem]:
        """Get a problem by ID from the in-memory store."""
        return next((p for p in self._problems if p.problem_id == problem_id), None)
    
    async def get_by_subject(self, subject_name: str) -> List[Problem]:
        """Get all problems for a subject from the in-memory store."""
        return [p for p in self._problems if p.subject_name == subject_name]
    
    def clear(self):
        """Clear all problems from the store (useful for test setup)."""
        self._problems = []
    
    @property
    def all_problems(self):
        """Get all problems currently stored (for verification in tests)."""
        return self._problems.copy()
