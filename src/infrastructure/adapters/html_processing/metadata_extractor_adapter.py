from typing import Any, Dict, List, Optional, Tuple
import re
from bs4 import Tag
from pathlib import Path
from src.domain.value_objects.scraping.subject_info import SubjectInfo


class MetadataExtractorAdapter:
    """
    Infrastructure adapter for extracting metadata from processed HTML blocks.

    Business Rules:
    - Contains all HTML parsing logic for metadata extraction
    - Pure functions with no side effects
    - Fallback strategies are explicit
    - Separates extraction logic from business rules
    """

    def extract(
        self,
        processed_header: Tag,
        processed_qblock: Tag,
        block_index: int,
        subject_info: SubjectInfo,
        source_url: str,
        run_folder_page: Path
    ) -> Dict[str, Any]:
        """Extract raw data from processed HTML blocks."""
        return self._extract_raw_data(
            header_container=processed_header,
            qblock=processed_qblock,
            block_index=block_index,
            subject_info=subject_info,
            source_url=source_url,
            run_folder_page=run_folder_page
        )

    def _extract_raw_data(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject_info: SubjectInfo,
        source_url: str,
        run_folder_page: Path
    ) -> Dict[str, Any]:
        """Core extraction logic - pure function with no side effects."""
        # Get text content
        text_content = qblock.get_text(separator=' ', strip=True)

        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем HTML содержимое для процессоров
        body_html = str(qblock) if qblock else ""
        header_html = str(header_container) if header_container else ""

        # Extract task number
        task_number = self._extract_task_number(header_container)

        # Extract codes
        kes_codes = self._extract_codes(header_container, r"КЭС|кодификатор")
        kos_codes = self._extract_codes(header_container, r"КОС|требование")

        # Extract answer
        answer = self._extract_answer(qblock)

        # Extract assets
        images = self._extract_assets(qblock, 'img', 'src', r'^assets/')
        files = self._extract_assets(qblock, 'a', 'href', r'^assets/')

        # Determine difficulty and exam part
        difficulty_level, exam_part = self._determine_difficulty(task_number)

        # Get stable ID from qblock
        stable_id = self._get_stable_id(qblock)

        return {
            'problem_id': f"{subject_info.alias}_{stable_id}",
            'subject_name': subject_info.official_name,
            'text': text_content,
            'source_url': source_url,
            'answer': answer,
            'images': images,
            'files': files,
            'kes_codes': kes_codes,
            'topics': kes_codes[:],  # For DB compatibility
            'kos_codes': kos_codes,
            'difficulty_level': difficulty_level,
            'task_number': task_number,
            'exam_part': exam_part,
            'fipi_proj_id': subject_info.proj_id,
            'created_at': None,  # Will be set by ProblemFactory or repository
            'updated_at': None,  # Will be set by ProblemFactory or repository
            # КРИТИЧЕСКОЕ ДОБАВЛЕНИЕ: HTML содержимое для процессоров
            'body_html': body_html,
            'header_html': header_html
        }

    # Pure helper functions below - no side effects

    def _extract_task_number(self, header_container: Tag) -> Optional[int]:
        """Extract task number using multiple strategies."""
        strategies = [
            lambda: self._extract_from_text(header_container, r"(?:Задание|Task)\s+(\d+)"),
            lambda: self._extract_from_attribute(header_container, 'data-task-number'),
            lambda: self._extract_from_class(header_container, r'task-(\d+)')
        ]

        for strategy in strategies:
            result = strategy()
            if result:
                return result
        return None

    def _extract_codes(self, header_container: Tag, pattern: str) -> List[str]:
        """Extract KES/KOS codes using flexible patterns."""
        elem = header_container.find(string=re.compile(pattern, re.IGNORECASE))
        if not elem or not elem.parent:
            return []

        text = elem.parent.get_text()
        return re.findall(r'(\d+(?:\.\d+)*)', text)

    def _extract_answer(self, qblock: Tag) -> Optional[str]:
        """Extract answer using multiple strategies."""
        strategies = [
            lambda: self._find_hidden_input(qblock, 'correct_answer'),
            lambda: self._find_hidden_input(qblock, 'answer'),
            lambda: self._find_class_element(qblock, 'correct-answer'),
            lambda: self._find_class_element(qblock, 'answer-value')
        ]

        for strategy in strategies:
            result = strategy()
            if result:
                return result
        return None

    def _extract_assets(self, qblock: Tag, tag_name: str, attr: str, pattern: str) -> List[str]:
        """Extract asset paths using regex pattern matching."""
        return [
            elem[attr] for elem in qblock.find_all(tag_name, **{attr: re.compile(pattern)})
            if elem.get(attr)
        ]

    def _determine_difficulty(self, task_number: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
        """Determine difficulty based on task number with fallback."""
        if task_number is None:
            return None, None

        if 1 <= task_number <= 12:
            return "basic", "Part 1"
        elif 13 <= task_number <= 19:
            return "advanced", "Part 2"
        return None, None

    def _get_stable_id(self, qblock: Tag) -> str:
        """Get stable ID from qblock element with fallback strategies."""
        strategies = [
            lambda: qblock.get('id', '')[1:] if qblock.get('id', '').startswith('q') else None,
            lambda: qblock.get('data-task-id'),
            lambda: qblock.get('data-problem-id'),
            lambda: f"block_{hash(qblock.get_text()) % 1000000}"
        ]

        for strategy in strategies:
            result = strategy()
            if result:
                return result
        return f"block_{id(qblock)}"

    # Helper methods for extraction strategies

    def _extract_from_text(self, element: Tag, pattern: str) -> Optional[int]:
        """Extract number from text using regex pattern."""
        text = element.get_text()
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match and match.group(1).isdigit() else None

    def _extract_from_attribute(self, element: Tag, attr_name: str) -> Optional[int]:
        """Extract number from HTML attribute."""
        value = element.get(attr_name)
        return int(value) if value and value.isdigit() else None

    def _extract_from_class(self, element: Tag, pattern: str) -> Optional[int]:
        """Extract number from CSS class using regex."""
        classes = element.get('class', [])
        for cls in classes:
            match = re.search(pattern, cls)
            if match and match.group(1).isdigit():
                return int(match.group(1))
        return None

    def _find_hidden_input(self, qblock: Tag, name: str) -> Optional[str]:
        """Find hidden input by name attribute."""
        elem = qblock.find('input', {'type': 'hidden', 'name': name})
        return elem.get('value') if elem else None

    def _find_class_element(self, qblock: Tag, class_name: str) -> Optional[str]:
        """Find element by class name and get its text or value."""
        elem = qblock.find(class_=class_name)
        if not elem:
            return None
        return elem.get('value') or elem.get_text(strip=True)
