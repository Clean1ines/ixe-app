"""
Functional core for scraping progress logic.

This module contains pure functions that determine scraping progress based on
existing problems and configuration, without any external dependencies or side effects.
"""
from typing import List, Optional, Any, Dict, Tuple
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
    if not url or "&page=" not in url:
        return None
    
    try:
        page_param = url.split("&page=")[1].split("&")[0]
        page_num = int(page_param)
        return page_num + 1  # Convert 0-based to 1-based
    except (ValueError, IndexError):
        return None

def determine_next_page(
    existing_problems: List[Problem], 
    config: ScrapingConfig,
    highest_known_page: Optional[int] = None
) -> int:
    """
    Determine the next page to scrape based on existing problems and configuration.
    
    This is a pure function with no side effects - it only depends on its inputs.
    
    Args:
        existing_problems: List of problems already in the database
        config: Scraping configuration
        highest_known_page: Optional highest page number known to exist (from UI pager)
        
    Returns:
        Page number to start scraping from
    """
    # If force restart is enabled, always start from page 1
    if config.force_restart:
        return 1
    
    # If start_page is explicitly set in config, use it
    if config.start_page is not None:
        return config.start_page
    
    # If no problems exist, start from page 1
    if not existing_problems:
        return 1
    
    # Extract page numbers from existing problems' source URLs
    page_numbers = []
    for problem in existing_problems:
        if hasattr(problem, 'source_url') and problem.source_url:
            page_num = extract_page_number_from_url(problem.source_url)
            if page_num is not None:
                page_numbers.append(page_num)
    
    # If we have page numbers, find the highest and start from the next one
    if page_numbers:
        highest_scraped_page = max(page_numbers)
        
        # If we know the highest page that exists, don't go beyond it
        if highest_known_page is not None and highest_scraped_page >= highest_known_page:
            return highest_known_page + 1  # Will be caught by max_pages check later
        
        return highest_scraped_page + 1
    
    # Fallback: start from page 1
    return 1
