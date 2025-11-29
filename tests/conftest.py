import pytest
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.domain.value_objects.scraping.subject_info import SubjectInfo
    from src.domain.models.problem import Problem
except ImportError as e:
    print(f"Import error in conftest: {e}")
    # Fallback для случаев когда src не установлен как пакет
    import importlib.util
    spec = importlib.util.spec_from_file_location("subject_info", "src/application/value_objects/scraping/subject_info.py")
    subject_info_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject_info_module)
    SubjectInfo = subject_info_module.SubjectInfo
    
    spec = importlib.util.spec_from_file_location("problem", "src/domain/models/problem.py")  
    problem_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(problem_module)
    Problem = problem_module.Problem

from unittest.mock import AsyncMock, MagicMock

# Настройка логирования для тестов
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр цикла событий для всей сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def subject_info():
    """Фикстура с тестовыми данными для предмета математика"""
    return SubjectInfo(
        alias='math',
        official_name='Математика. Базовый уровень',
        proj_id='E040A72A1A3DABA14C90C97E0B6EE7DC',
        exam_year=2026
    )

@pytest.fixture
def sample_problem(subject_info):
    """Фикстура с тестовой задачей"""
    return Problem(
        problem_id=f"math_0_{int(datetime.now().timestamp())}",
        subject_name=subject_info.official_name,
        text="Sample problem text",
        source_url="https://ege.fipi.ru/sample",
        created_at=datetime.now()
    )

@pytest.fixture
def test_run_folder(tmp_path):
    """Фикстура с временной папкой для тестов"""
    return tmp_path / "test_assets"

@pytest.fixture
def mock_dependencies(subject_info):
    """Фикстура с моками зависимостей для тестов"""
    return {
        'page_scraping_service': AsyncMock(),
        'problem_repository': AsyncMock(),
        'problem_factory': MagicMock(),
        'browser_service': AsyncMock(),
        'progress_service': AsyncMock(),
        'progress_reporter': AsyncMock(),
        'asset_downloader_impl': AsyncMock()
    }
