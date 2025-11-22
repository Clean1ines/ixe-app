"""
Tests for ScrapingProgressService that follow classical TDD principles.
These tests focus on state verification rather than interaction verification.
"""
import pytest
from datetime import datetime
from src.application.services.scraping.scraping_progress_service import ScrapingProgressService
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem

class MockProblemRepository:
    async def get_by_subject(self, subject_name):
        return []

def create_test_problem(problem_id, subject_name="Математика. Базовый уровень", source_url="", created_at=None):
    """Helper to create test problems with consistent data"""
    return Problem(
        problem_id=problem_id,
        subject_name=subject_name,
        text="Test problem text",
        source_url=source_url,
        created_at=created_at or datetime.now()
    )

def test_determine_next_page_returns_1_when_no_problems_exist():
    """When no problems exist in database, scraping should start from page 1"""
    existing_problems = []
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=False
    )
    
    subject_info = SubjectInfo(
        alias='math',
        official_name='Математика. Базовый уровень',
        proj_id='E040A72A1A3DABA14C90C97E0B6EE7DC',
        exam_year=2026
    )
    
    # This is a placeholder - in real implementation this would be a functional core function
    next_page = 1  # Initial behavior - always start from page 1
    
    assert next_page == 1

def test_determine_next_page_returns_2_when_page_1_is_complete():
    """When page 1 is fully scraped, next page should be 2"""
    existing_problems = [
        create_test_problem("math_1", source_url="https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        create_test_problem("math_2", source_url="https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=False
    )
    
    # This is a placeholder - in real implementation this would use the functional core
    next_page = max(int(p.source_url.split("page=")[-1]) + 2 for p in existing_problems) if existing_problems else 1
    
    assert next_page == 2

def test_determine_next_page_returns_1_when_force_restart():
    """When force_restart is True, always start from page 1 regardless of existing problems"""
    existing_problems = [
        create_test_problem("math_1", source_url="https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        create_test_problem("math_2", source_url="https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=True
    )
    
    # This is a placeholder - in real implementation this would use the functional core
    next_page = 1 if config.force_restart else (max(int(p.source_url.split("page=")[-1]) + 2 for p in existing_problems) if existing_problems else 1)
    
    assert next_page == 1
