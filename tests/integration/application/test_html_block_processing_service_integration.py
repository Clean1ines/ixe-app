"""
Integration tests for HTMLBlockProcessingService. These tests verify the interaction between the
service and its real dependencies (processors, metadata extractor, etc.).
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.infrastructure.adapters.html_processing.metadata_extractor_adapter import MetadataExtractorAdapter
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover
from src.application.value_objects.scraping.subject_info import SubjectInfo

@pytest.fixture
def mock_asset_downloader():
    """Mock for IAssetDownloader."""
    mock = AsyncMock()
    mock.download.return_value = "/path/to/downloaded/file"
    mock.download_bytes.return_value = b"test content"
    return mock

@pytest.fixture
def subject_info():
    """Sample SubjectInfo."""
    return SubjectInfo.from_alias("math")

@pytest.fixture
def sample_html_block_elements():
    """A sample HTML block elements list that ElementIdentifier can recognize."""
    from bs4 import BeautifulSoup
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ElementIdentifier ищет класс 'qblock' и элементы с ID начинающимся на 'i'
    html_content = """
    <div id="i123" class="header-container">
        <span>Задание 1</span>
        <span>КЭС: 1.1, 1.2</span>
        <span>КОС: 2.1</span>
    </div>
    <div class="qblock">
        <p>Это текст задачи с достаточным количеством символов чтобы ElementIdentifier распознал его как qblock. Текст должен быть длиннее 50 символов чтобы сработала fallback стратегия.</p>
        <input type="hidden" name="correct_answer" value="42">
        <img src="assets/image1.png">
        <a href="assets/file1.pdf">Скачать файл</a>
    </div>
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    # Возвращаем список элементов, которые ElementIdentifier может обработать
    return list(soup.find_all('div'))

@pytest_asyncio.fixture
async def html_block_processing_service_with_real_processors():
    """Create a real HTMLBlockProcessingService with *real* processors."""
    service = HTMLBlockProcessingService(
        metadata_extractor=MetadataExtractorAdapter(),
        raw_processors=[
            TaskInfoProcessor(),
            InputFieldRemover(),
            MathMLRemover(),
            UnwantedElementRemover()
        ]
    )
    return service

@pytest.mark.asyncio
async def test_html_block_processing_service_integration_with_real_processors(
    html_block_processing_service_with_real_processors, 
    sample_html_block_elements, 
    subject_info,
    mock_asset_downloader
):
    """Test HTMLBlockProcessingService with real processors and mocked asset downloader. This verifies the integration."""
    
    context = {
        'subject_info': subject_info,
        'source_url': 'https://ege.fipi.ru/bank/questions.php?proj=E040A72A1A3DABA14C90C97E0B6EE7DC&page=1',
        'run_folder_page': Path('test_run_folder'),
        'downloader': mock_asset_downloader,
        'files_location_prefix': 'assets/',
        'base_url': 'https://ege.fipi.ru/bank/'
    }
    
    problem = await html_block_processing_service_with_real_processors.process_block(
        block_elements=sample_html_block_elements,
        block_index=0,
        context=context
    )
    
    # Проверяем что проблема была создана
    assert problem is not None
    assert problem.problem_id is not None
    assert problem.subject_name == subject_info.official_name
    assert problem.text is not None
    assert "текст задачи" in problem.text.lower()
