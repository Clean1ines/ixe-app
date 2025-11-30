"""
Tests for scraping progress logic - functional core that determines next page to scrape.

These tests focus on state verification rather than interaction verification and
use real data structures instead of mocks.
"""
import pytest
from datetime import datetime
from src.application.services.scraping.progress_logic import determine_next_page, extract_page_number_from_url
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
from tests.fakes import FakeProblemRepository

def create_test_problem(problem_id, subject_name, source_url):
    """Helper to create test problems with consistent data"""
    return Problem(
        problem_id=problem_id,
        subject_name=subject_name,
        text="Test problem text",
        source_url=source_url,
        created_at=datetime.now()
    )

def test_extract_page_number_from_url():
    """Test extraction of page numbers from FIPI URLs"""
    # Test valid URLs
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0") == 1
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=1") == 2
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=42") == 43
    
    # Test URL with additional parameters
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0&extra=param") == 1
    
    # Test invalid URLs
    assert extract_page_number_from_url(None) is None
    assert extract_page_number_from_url("") is None
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC") is None
    assert extract_page_number_from_url("https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=invalid") is None

def test_determine_next_page_returns_1_when_no_problems_exist():
    """When no problems exist in database, scraping should start from page 1"""
    existing_problems = []
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=False
    )
    
    next_page = determine_next_page(existing_problems, config)
    assert next_page == 1

def test_determine_next_page_returns_2_when_page_1_is_complete():
    """When page 1 is fully scraped, next page should be 2"""
    existing_problems = [
        create_test_problem("math_1", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        create_test_problem("math_2", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=False
    )
    
    next_page = determine_next_page(existing_problems, config)
    assert next_page == 2

def test_determine_next_page_returns_1_when_force_restart():
    """When force_restart is True, always start from page 1 regardless of existing problems"""
    existing_problems = [
        create_test_problem("math_1", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        create_test_problem("math_2", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=True
    )
    
    next_page = determine_next_page(existing_problems, config)
    assert next_page == 1

def test_determine_next_page_handles_mixed_page_numbers():
    """When problems exist from multiple pages, start from the next page after the highest"""
    existing_problems = [
        # Page 1 problems
        create_test_problem("math_1", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        create_test_problem("math_2", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
        # Page 3 problems (maybe page 2 was skipped)
        create_test_problem("math_5", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=2"),
        create_test_problem("math_6", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=2"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=None,
        max_pages=None,
        force_restart=False
    )
    
    next_page = determine_next_page(existing_problems, config)
    assert next_page == 4  # Start after the highest page (3)

def test_determine_next_page_uses_config_start_page():
    """When start_page is set in config, it should be used regardless of existing problems"""
    existing_problems = [
        create_test_problem("math_1", "Математика. Базовый уровень", "https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=0"),
    ]
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=5,  # Explicitly start from page 5
        max_pages=None,
        force_restart=False
    )
    
    next_page = determine_next_page(existing_problems, config)
    assert next_page == 5
