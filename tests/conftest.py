import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
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
