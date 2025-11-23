#!/usr/bin/env python3
"""
Check compatibility of our code with older package versions
"""
import sys
import importlib

def check_imports():
    """Check if all required imports work"""
    imports_to_check = [
        "aiohttp",
        "bs4", 
        "playwright",
        "sqlalchemy",
        "pytest",
        "pytest_asyncio"
    ]
    
    print("=== CHECKING IMPORTS ===")
    for import_name in imports_to_check:
        try:
            module = importlib.import_module(import_name)
            print(f"✅ {import_name}: {getattr(module, '__version__', 'unknown')}")
        except ImportError as e:
            print(f"❌ {import_name}: {e}")
    
    print("\n=== CHECKING OUR IMPORTS ===")
    our_imports = [
        "src.application.value_objects.scraping.subject_info",
        "src.domain.models.problem", 
        "src.application.use_cases.scraping.scrape_subject_use_case"
    ]
    
    for import_name in our_imports:
        try:
            module = importlib.import_module(import_name)
            print(f"✅ {import_name}")
        except ImportError as e:
            print(f"❌ {import_name}: {e}")

if __name__ == "__main__":
    sys.path.insert(0, '.')
    check_imports()
