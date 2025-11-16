"""
Domain interface for HTML processing operations.

This interface defines the contract for processing a single HTML block pair
(header_container, qblock), allowing the domain layer to remain independent of the
specific HTML parsing and extraction implementation.
It mirrors the signature of the old processors from ~/iXe for compatibility.
"""
import abc
from typing import Dict, Any
from bs4.element import Tag


class IHTMLProcessor(abc.ABC):
    """
    Domain interface for processing a single HTML block pair (header_container, qblock).

    This interface abstracts the logic for extracting structured data (like text, images,
    KES/KOS codes, answers, etc.) from a specific HTML structure representing one problem block.
    It expects the same signature as the old processors from ~/iXe.
    """

    @abc.abstractmethod
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str, # Use subject name string
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics"). This is a string.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            **kwargs: Additional keyword arguments (e.g., for passing asset downloader, run folders).

        Returns:
            A dictionary containing structured data extracted from the block.
            The exact keys depend on the implementation but should align with
            fields required by the Problem domain entity or ProblemFactory.
            Example keys might include:
            - 'problem_id': str
            - 'text': str
            - 'answer': Optional[str]
            - 'images': List[str] (local relative paths)
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
