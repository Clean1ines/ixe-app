"""
Domain interface for HTML processing operations.

This interface defines the contract for processing a single HTML block pair
(header_container, qblock) representing an EGE problem, allowing the domain layer
to remain independent of the specific HTML parsing and extraction implementation.
"""
import abc
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4.element import Tag
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Импортируем новый интерфейс
from src.application.value_objects.scraping.subject_info import SubjectInfo # Импортируем VO


class IHTMLProcessor(abc.ABC):
    """
    Domain interface for processing a single HTML block pair (header_container, qblock).

    This interface abstracts the logic for extracting structured data (like text, images,
    KES/KOS codes, answers, etc.) from a specific HTML structure representing one problem.
    It also handles downloading associated assets using IAssetDownloader.
    """

    @abc.abstractmethod
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject_info: SubjectInfo,
        base_url: str,
        run_folder_page: Path,
        asset_downloader: IAssetDownloader, # Принимаем интерфейс загрузчика
        files_location_prefix: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject_info: The SubjectInfo object containing subject details.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            run_folder_page: Path to the run folder for this page's assets (e.g., downloaded images/files).
            asset_downloader: Service for downloading assets (implements IAssetDownloader).
            files_location_prefix: Prefix for file paths in the output (relative to run_folder_page or a global assets dir).
            **kwargs: Additional keyword arguments (e.g., for passing other services if needed later).

        Returns:
            A dictionary containing structured data extracted from the block.
            The exact keys depend on the implementation but should align with
            fields required by the Problem domain entity or ProblemFactory.
            Example keys might include:
            - 'problem_id': str
            - 'text': str
            - 'answer': Optional[str]
            - 'images': List[str] (local relative paths from run_folder_page/assets or global assets dir)
            - 'files': List[str] (local relative paths)
            - 'kes_codes': List[str]
            - 'topics': List[str]
            - 'kos_codes': List[str]
            - 'difficulty_level': Optional[str]
            - 'task_number': Optional[int]
            - 'exam_part': Optional[str]
            - 'metadata': Dict[str, Any] (for extra info)
        """
        pass
