"""
Integration tests for ScrapeSubjectUseCase and PageScrapingService.
These tests verify the interaction between the use case, page scraping service,
and other application/domain components using real implementations where possible,
but mocking external resources like the browser and real asset downloads.
"""
import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from bs4 import BeautifulSoup
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.services.page_scraping_service import PageScrapingService
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.factories.problem_factory import ProblemFactory
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.infrastructure.adapters.external_services.playwright_asset_downloader_adapter import PlaywrightAssetDownloaderAdapter
from src.infrastructure.adapters.browser_pool_service_adapter import BrowserPoolServiceAdapter
from src.infrastructure.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem


@pytest_asyncio.fixture
async def mock_browser_service():
    """Mock for IBrowserService to avoid real browser calls."""
    service = AsyncMock(spec=IBrowserService)
    # Mock get_page_content to return a simple HTML page with a problem block
    sample_html = """
    <html>
    <body>
        <div class="task-header-panel">
            <span>Задание 1</span>
            <span>КЭС: 1.1 1.2</span>
            <span>Требование: 3.1 3.2</span>
        </div>
        <div class="qblock">
            <p>Решите уравнение: x + 2 = 5</p>
            <input type="hidden" name="correct_answer" value="3">
            <img src="https://example.com/image1.png" alt="Graph">
            <a href="https://example.com/file1.pdf">Download file</a>
        </div>
        <div class="task-header-panel">
            <span>Задание 2</span>
            <span>КЭС: 2.1</span>
        </div>
        <div class="qblock">
            <p>Найдите производную функции f(x) = x^2</p>
            <input type="hidden" name="correct_answer" value="2x">
        </div>
    </body>
    </html>
    """
    service.get_page_content.return_value = sample_html
    return service

@pytest_asyncio.fixture
async def mock_asset_downloader():
    """Mock for IAssetDownloader to avoid real downloads."""
    downloader = AsyncMock(spec=IAssetDownloader)
    # Mock download methods to do nothing or return dummy paths
    downloader.download.return_value = None
    downloader.download_bytes.return_value = b"dummy_content"
    return downloader

@pytest_asyncio.fixture
async def mock_problem_repository():
    """Mock for IProblemRepository."""
    repo = Mock(spec=IProblemRepository)
    repo.save.return_value = None # Assuming save is async void or returns success indicator
    repo.get_by_id.return_value = None
    repo.get_by_subject.return_value = []
    return repo

@pytest_asyncio.fixture
async def mock_problem_factory():
    """Mock for IProblemFactory."""
    factory = Mock(spec=IProblemFactory)
    # Create a simple mock Problem instance
    mock_problem = Mock(spec=Problem)
    mock_problem.problem_id = "mock_id_123"
    mock_problem.subject_name = "Mathematics"
    mock_problem.text = "Mock problem text"
    mock_problem.source_url = "https://mock.url"
    factory.create_problem.return_value = mock_problem
    return factory

@pytest_asyncio.fixture
async def html_block_processing_service(mock_asset_downloader, mock_problem_factory):
    """Create a real HTMLBlockProcessingService with mocked asset downloader and problem factory."""
    # Use real processors for integration test, but they will use the mocked downloader
    image_processor = ImageScriptProcessor()
    file_processor = FileLinkProcessor()
    task_info_processor = TaskInfoProcessor()
    input_field_remover = InputFieldRemover()
    mathml_remover = MathMLRemover()
    unwanted_element_remover = UnwantedElementRemover()

    service = HTMLBlockProcessingService(
        asset_downloader_impl=mock_asset_downloader,
        problem_factory=mock_problem_factory,
        image_processor=image_processor,
        file_processor=file_processor,
        task_info_processor=task_info_processor,
        input_field_remover=input_field_remover,
        mathml_remover=mathml_remover,
        unwanted_element_remover=unwanted_element_remover
    )
    return service

@pytest_asyncio.fixture
async def page_scraping_service(mock_browser_service, mock_asset_downloader, mock_problem_factory, html_block_processing_service):
    """Create a real PageScrapingService with mocked dependencies."""
    service = PageScrapingService(
        browser_service=mock_browser_service,
        asset_downloader_impl=mock_asset_downloader,
        problem_factory=mock_problem_factory,
        html_block_processing_service=html_block_processing_service
    )
    return service

@pytest_asyncio.fixture
async def scrape_subject_use_case(page_scraping_service, mock_problem_repository, mock_problem_factory, mock_browser_service, mock_asset_downloader):
    """Create a real ScrapeSubjectUseCase with mocked dependencies."""
    use_case = ScrapeSubjectUseCase(
        page_scraping_service=page_scraping_service,
        problem_repository=mock_problem_repository,
        problem_factory=mock_problem_factory,
        browser_service=mock_browser_service,
        asset_downloader_impl=mock_asset_downloader
    )
    return use_case

@pytest.mark.asyncio
async def test_scrape_subject_use_case_integration(scrape_subject_use_case, mock_problem_repository, mock_browser_service):
    """Test that ScrapeSubjectUseCase correctly orchestrates scraping with mocked external dependencies."""
    subject_info = SubjectInfo.from_alias("math")
    config = ScrapingConfig(
        mode=ScrapingMode.SEQUENTIAL,
        start_page=1,
        max_pages=1,
        max_empty_pages=1,
        timeout_seconds=30
    )

    # Execute the use case
    result = await scrape_subject_use_case.execute(subject_info, config)

    # Assertions
    assert result.success is True
    # The mock factory returns 1 problem per block, and sample HTML has 2 blocks
    # However, the actual count depends on how _save_problems aggregates the calls.
    # Mock _save_problems to return a specific number, or assert on repository calls.
    # Let's assert on the repository save calls.
    # Since we have 2 blocks in the HTML and get_page_content is called once, we expect 2 problems to be processed.
    # The factory.create_problem should be called twice.
    # The repo.save should be called twice (once for each problem).
    # Assuming _save_problems calls repo.save for each problem returned by page service
    # The PageScrapingService returns a list of problems from scrape_page
    # The ScrapeSubjectUseCase iterates and calls _save_problems
    # The _save_problems calls repo.save for each problem
    # So, repo.save.call_count should be 2.
    # And result.total_problems_saved should reflect this.
    # The mock factory returns the same mock_problem each time.
    # Let's adjust the mock factory to return different problems or just count calls.
    # For now, let's just check the call count on repo.
    # The mock repo's save method was called.
    # We expect it to be called twice, once for each problem processed by the page service.
    assert mock_problem_repository.save.call_count == 2 # Assuming 2 blocks -> 2 problems -> 2 saves

    # Check that the browser service was called to get page content
    mock_browser_service.get_page_content.assert_called_once()

@pytest.mark.asyncio
async def test_page_scraping_service_integration(page_scraping_service, mock_problem_factory):
    """Test that PageScrapingService correctly uses HTMLBlockProcessingService and ProblemFactory."""
    subject_info = SubjectInfo.from_alias("math")
    base_url = f"https://ege.fipi.ru/bank/{subject_info.proj_id}"
    url = f"{base_url}?page=1"
    timeout = 30
    run_folder_page = Path("test_run_folder")

    # Execute the page scraping service
    problems = await page_scraping_service.scrape_page(
        url=url,
        subject_info=subject_info,
        base_url=base_url,
        timeout=timeout,
        run_folder_page=run_folder_page,
        files_location_prefix="assets/"
    )

    # Assertions
    # The mock factory returns a single mock problem instance.
    # PageScrapingService processes 2 blocks, so create_problem should be called twice.
    # The returned list 'problems' should contain the mock problems created by the factory.
    # Since the factory is mocked to return the same instance, problems list will have 2 of the same instance.
    assert len(problems) == 2
    assert all(p == mock_problem_factory.create_problem.return_value for p in problems)
    assert mock_problem_factory.create_problem.call_count == 2 # Called once per block processed by HTMLBlockProcessingService

# Note: A full integration test involving real asset downloading and browser calls
# would require a test server and is significantly more complex.
# The above tests focus on the application layer orchestration and interaction
# between services/factories with mocked external resources.
