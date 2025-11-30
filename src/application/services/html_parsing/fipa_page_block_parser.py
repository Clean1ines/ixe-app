from typing import List
import logging
import re
from bs4 import BeautifulSoup, Tag
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser

logger = logging.getLogger(__name__)


class FIPIPageBlockParser(IHTMLBlockParser):
    def parse_blocks(self, page_content: str) -> List[List[Tag]]:
        logger.debug("Starting HTML block parsing.")
        page_soup = BeautifulSoup(page_content, 'html.parser')

        task_elements_by_id = {}

        question_forms = page_soup.find_all('form', attrs={'name': True})
        for form in question_forms:
            form_name = form.get('name', '')
            if form_name and form_name.startswith('qform'):
                if form_name not in task_elements_by_id:
                    task_elements_by_id[form_name] = []
                task_elements_by_id[form_name].append(form)

        if not task_elements_by_id:
            all_divs = page_soup.find_all('div')
            for div in all_divs:
                div_id = div.get('id', '')
                if div_id.startswith('q') or div_id.startswith('i'):
                    identifier = div_id[1:]
                    if identifier not in task_elements_by_id:
                        task_elements_by_id[identifier] = []
                    task_elements_by_id[identifier].append(div)

        result_blocks = list(task_elements_by_id.values())
        logger.info(f"Found {len(result_blocks)} task blocks.")
        return result_blocks

    def get_total_pages(self, page_content: str) -> int:
        soup = BeautifulSoup(page_content, 'html.parser')
        pager = soup.find('div', class_='pager')
        if pager:
            page_links = pager.find_all('a')
            if page_links:
                last_page = 1
                for link in page_links:
                    href = link.get('href', '')
                    page_match = re.search(r'page=(\d+)', href)
                    if page_match:
                        page_num = int(page_match.group(1)) + 1
                        if page_num > last_page:
                            last_page = page_num
                return last_page
        return 1
