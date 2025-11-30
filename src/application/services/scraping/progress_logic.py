from typing import List, Optional
"""
Functional core for scraping progress logic.

This module contains pure functions that determine scraping progress based on
existing problems and configuration, without any external dependencies or side effects.
"""
from src.domain.models.problem import Problem
from src.application.value_objects.scraping.scraping_config import ScrapingConfig


def extract_page_number_from_url(url: str) -> Optional[int]:
    """
    Extract page number from FIPI URL.

    FIPI URLs use 0-based page numbering in query parameters like:
    https://ege.fipi.ru/...&page=0 (page 1)
    https://ege.fipi.ru/...&page=1 (page 2)

    Returns 1-based page number or None if not found.
    """
    # Use centralized configuration for base URL detection
    try:
        from src.core.config import config
        base_url = getattr(config.scraping, 'base_url', 'https://fipi.ru')
        browser_base_url = getattr(config.browser, 'base_url', 'https://ege.fipi.ru')
    except ImportError:
        # Fallback to hardcoded values if config is not available
        base_url = 'https://fipi.ru'
        browser_base_url = 'https://ege.fipi.ru'

    if not url or ("&page=" not in url and "page=" not in url):
        return None

    # Check both base URLs
    if not (url.startswith(base_url) or url.startswith(browser_base_url)):
        return None

    try:
        # Try different URL parameter patterns
        if "&page=" in url:
            page_param = url.split("&page=")[1].split("&")[0]
        elif "?page=" in url:
            page_param = url.split("?page=")[1].split("&")[0]
        else:
            return None

        page_num = int(page_param)
        return page_num + 1  # Convert 0-based to 1-based
    except (ValueError, IndexError):
        return None


def _get_highest_scraped_page(existing_problems: List[Problem]) -> Optional[int]:
    """
    Чистая функция для извлечения максимального 1-based номера страницы
    из списка существующих проблем.
    """
    page_numbers = []
    for problem in existing_problems:
        # Проверяем наличие атрибута и его значение перед вызовом extract_page_number_from_url
        if hasattr(problem, 'source_url') and problem.source_url:
            page_num = extract_page_number_from_url(problem.source_url)
            if page_num is not None:
                page_numbers.append(page_num)

    return max(page_numbers) if page_numbers else None


def determine_next_page(
    existing_problems: List[Problem],
    config: ScrapingConfig,
    highest_known_page: Optional[int] = None
) -> int:
    """
    Determine the next page to scrape based on existing problems and configuration.

    Returns:
        Page number to start scraping from (1-based)
    """
    # 1. СТРАТЕГИЯ: Принудительный перезапуск
    if config.force_restart:
        return 1

    # 2. СТРАТЕГИЯ: Явно заданная страница начала
    if config.start_page is not None and config.start_page != "init":
        try:
            return int(config.start_page)
        except (ValueError, TypeError):
            # Если невалидное значение, игнорируем его и продолжаем
            pass

    # 3. СТРАТЕГИЯ: Нет существующих проблем
    if not existing_problems:
        return 1

    # 4. СТРАТЕГИЯ: Продолжение скрейпинга (основной поток)
    highest_scraped_page = _get_highest_scraped_page(existing_problems)

    if highest_scraped_page is not None:
        next_page = highest_scraped_page + 1

        # Учет известной максимальной страницы
        if highest_known_page is not None and highest_scraped_page >= highest_known_page:
            return highest_known_page 

        return next_page

    # 5. СТРАТЕГИЯ: Не удалось найти страницы (нет source_url или ошибка парсинга)
    return 1  # Fallback, если не смогли найти номер страницы ни в одной проблеме
