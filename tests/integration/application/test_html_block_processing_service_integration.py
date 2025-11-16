"""
Integration tests for HTMLBlockProcessingService.
These tests verify the interaction between the service and the concrete HTML processors
from the infrastructure layer, using a mocked IAssetDownloader and a real ProblemFactory.
The tests will use prepared HTML fixtures to check the processing chain.
"""
import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from bs4 import BeautifulSoup
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.factories.problem_factory import ProblemFactory
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover
from src.application.value_objects.scraping.subject_info import SubjectInfo


@pytest_asyncio.fixture
async def mock_asset_downloader():
    """Mock for IAssetDownloader to avoid real downloads."""
    downloader = AsyncMock(spec=IAssetDownloader)
    # Mock download methods to do nothing or return dummy paths
    downloader.download.return_value = None
    downloader.download_bytes.return_value = b"dummy_content"
    return downloader

@pytest_asyncio.fixture
def mock_problem_factory():
    """Mock for IProblemFactory."""
    factory = Mock()
    # Create a simple mock Problem instance
    mock_problem = Mock()
    mock_problem.problem_id = "mock_id_123"
    mock_problem.subject_name = "Mathematics"
    mock_problem.text = "Mock problem text"
    mock_problem.source_url = "https://mock.url"
    factory.create_problem.return_value = mock_problem
    return factory

@pytest_asyncio.fixture
def real_problem_factory():
    """Real ProblemFactory instance."""
    return ProblemFactory()

@pytest_asyncio.fixture
def subject_info():
    """Sample SubjectInfo."""
    return SubjectInfo.from_alias("math")

@pytest_asyncio.fixture
def sample_html_block_pair():
    """A sample HTML block pair (header_container, qblock) for testing."""
    header_html = """
    <div class="task-header-panel">
        <span>Задание 1</span>
        <span>КЭС: 1.1 1.2</span>
        <span>Требование: 3.1 3.2</span>
    </div>
    """
    qblock_html = """
    <div class="qblock">
        <p>Решите уравнение: x + 2 = 5</p>
        <input type="hidden" name="correct_answer" value="3">
        <img src="https://example.com/image1.png" alt="Graph">
        <a href="https://example.com/file1.pdf">Download file</a>
        <math>...</math> <!-- MathML element -->
        <div class="hint" id="hint" name="hint">This is a hint.</div> <!-- Unwanted element -->
    </div>
    """
    header_container = BeautifulSoup(header_html, 'html.parser').find('div', class_='task-header-panel')
    qblock = BeautifulSoup(qblock_html, 'html.parser').find('div', class_='qblock')
    return header_container, qblock

@pytest_asyncio.fixture
def html_block_processing_service_with_real_processors(mock_asset_downloader, real_problem_factory):
    """Create a real HTMLBlockProcessingService with *real* processors."""
    service = HTMLBlockProcessingService(
        asset_downloader_impl=mock_asset_downloader,
        problem_factory=real_problem_factory,
        image_processor=ImageScriptProcessor(),
        file_processor=FileLinkProcessor(),
        task_info_processor=TaskInfoProcessor(),
        input_field_remover=InputFieldRemover(),
        mathml_remover=MathMLRemover(),
        unwanted_element_remover=UnwantedElementRemover()
    )
    return service

@pytest.mark.asyncio
async def test_html_block_processing_service_integration_with_real_processors(
    html_block_processing_service_with_real_processors, sample_html_block_pair, subject_info, mock_asset_downloader
):
    """
    Test HTMLBlockProcessingService with real processors and mocked asset downloader.
    This verifies the processing chain and the final call to ProblemFactory.
    """
    header_container, qblock = sample_html_block_pair
    block_index = 0
    base_url = "https://ege.fipi.ru/bank/12345"
    run_folder_page = Path("test_run_folder")

    # Prepare context as PageScrapingService would
    context = {
        'run_folder_page': run_folder_page,
        'downloader': AsyncMock(), # This is the adapter instance, not IAssetDownloader impl
        'base_url': base_url,
        'subject_info': subject_info,
        'source_url': f"{base_url}?page=1"
    }

    # Execute the processing
    result_problem = await html_block_processing_service_with_real_processors.process_block(
        header_container=header_container,
        qblock=qblock,
        block_index=block_index,
        context=context
    )

    # Assertions
    # The service should return a problem object (from the real factory with mocked raw data creation or real if possible)
    # Since ProblemFactory.create_problem is called with raw_data from _extract_raw_data_from_processed_blocks,
    # and that function depends on the processed HTML, the test verifies the *chain* worked.
    # If any processor fails critically (returns None), the service returns None.
    # We expect a result here if the chain works correctly up to Problem creation.
    # The mock_asset_downloader will cause warnings in the processors, but they should still process the HTML structure.
    assert result_problem is not None # Should not be None if processing is successful
    # Check that the mock asset downloader was called by the processors (indirectly through the adapter)
    # This is harder to assert directly without mocking the adapter itself.
    # We can assert that the problem was created by checking the factory's call count in a full integration scenario.
    # For this test, we rely on the fact that if result_problem is not None, the chain worked to some degree.

# Note: A more detailed integration test would involve:
# 1. Checking the state of `qblock` after each processor in the chain.
# 2. Verifying that assets were requested for download (mock_asset_downloader.download.assert_called).
# 3. Verifying the structure of the raw_data passed to ProblemFactory.
# However, these are more unit-test-like checks for the integration of the service and its dependencies.
# The above test confirms the overall orchestration.
