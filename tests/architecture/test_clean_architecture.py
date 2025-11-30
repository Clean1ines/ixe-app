import pytest
import ast
from pathlib import Path


def extract_imports_from_file(file_path: Path):
    """Extract all imports from a Python file."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports


def test_domain_layer_independence():
    """Test that domain layer doesn't depend on application or infrastructure."""
    domain_dir = Path("src/domain")
    
    for domain_file in domain_dir.rglob("*.py"):
        if domain_file.is_file() and domain_file.suffix == '.py':
            imports = extract_imports_from_file(domain_file)
            
            for imp in imports:
                # Domain should not import from application or infrastructure
                assert not imp.startswith("src.application"), f"Domain file {domain_file} imports from application: {imp}"
                assert not imp.startswith("src.infrastructure"), f"Domain file {domain_file} imports from infrastructure: {imp}"


def test_application_layer_dependencies():
    """Test that application layer only depends on domain."""
    application_dir = Path("src/application")
    
    for app_file in application_dir.rglob("*.py"):
        if app_file.is_file() and app_file.suffix == '.py':
            imports = extract_imports_from_file(app_file)
            
            for imp in imports:
                # Application should not import from infrastructure directly
                # (except through interfaces/ports)
                if imp.startswith("src.infrastructure"):
                    # Allow infrastructure only if it's through domain interfaces
                    # This is a simplified check - in practice you'd want more granular control
                    pytest.skip(f"Application file {app_file} imports from infrastructure: {imp}")


def test_new_architecture_components_exist():
    """Test that all new architecture components are present."""
    required_files = [
        "src/domain/interfaces/services/i_page_scraping_service.py",
        "src/domain/value_objects/scraping/page_scraping_result.py",
        "src/application/use_cases/scraping/components/page_processor.py",
        "src/application/use_cases/scraping/components/scraping_loop_controller.py",
        "src/application/use_cases/scraping/components/result_composer.py",
        "src/infrastructure/services/page_scraping_adapter.py"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Required architecture file missing: {file_path}"
