"""
Infrastructure adapter implementing domain interface for removing unwanted HTML elements from blocks.

This module provides the `UnwantedElementRemover` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for removing specific unwanted elements
(hint divs, status spans, table rows) within a single problem block pair (header_container, qblock).
"""
import logging
import re
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, Any
# from domain.interfaces.html_processor import IHTMLProcessor # УДАЛЯЕМ СТАРЫЙ ИМПОРТ
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем правильный интерфейс

logger = logging.getLogger(__name__)

class UnwantedElementRemover(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for removing unwanted elements.
    
    Business Rules:
    - Removes hint divs, status title spans, task status spans, table rows with bgcolor
    - Logs the number of removed elements per type
    - Returns processed block data
    """

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
        Process a single HTML block pair and remove unwanted elements.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics"). This is a string.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing the updated block data.
            Example: {
                "header_container": updated_header_container,
                "qblock": updated_qblock,
                "block_index": int,
                "subject": str, # subject_info.subject_name
                "base_url": str,
            }
        """
        logger.debug(f"Removing unwanted elements for block {block_index} in subject {subject}.")

        # Process the qblock content to remove unwanted elements
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')

        # Remove hint divs
        removed_hint_count = 0
        for div in soup.find_all('div', class_=re.compile(r'hint'), attrs={'id': 'hint', 'name': 'hint'}):
            div.decompose()
            removed_hint_count += 1
        # Remove status title spans
        removed_status_title_count = 0
        for span in soup.find_all('span', class_=re.compile(r'status-title-text')):
            span.decompose()
            removed_status_title_count += 1
        # Remove task status spans
        removed_task_status_count = 0
        for span in soup.find_all('span', class_=re.compile(r'task-status')):
            span.decompose()
            removed_task_status_count += 1
        # Remove table rows with bgcolor
        removed_tr_bgcolor_count = 0
        for tr in soup.find_all('tr', attrs={'bgcolor': '#FFFFFF'}):
            tr.decompose()
            removed_tr_bgcolor_count += 1

        logger.debug(f"Removed {removed_hint_count} hint divs, {removed_status_title_count} status title spans, "
                     f"{removed_task_status_count} task status spans, {removed_tr_bgcolor_count} table rows with bgcolor "
                     f"from block {block_index}.")

        # Update the qblock with processed content
        processed_qblock = soup.find('div', class_='qblock') or soup.find('div')

        # Return the processed block data
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': processed_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject, # Use the string subject
            'base_url': base_url
        }
