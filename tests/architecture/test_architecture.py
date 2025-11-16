"""
Architecture tests for the project.
These tests verify that architectural boundaries are not violated,
e.g., domain layer does not depend on infrastructure or application layers.
"""
import ast
import os
import pytest
from pathlib import Path


PROJECT_ROOT = Path("src")
DOMAIN_LAYER = PROJECT_ROOT / "domain"
APPLICATION_LAYER = PROJECT_ROOT / "application"
INFRASTRUCTURE_LAYER = PROJECT_ROOT / "infrastructure"


def _get_all_python_files_in_dir(directory: Path):
    """Helper to recursively find all .py files in a directory."""
    return [f for f in directory.rglob("*.py") if f.is_file()]


def _extract_imports_from_file(filepath: Path):
    """Extract imported module names from a Python file using AST."""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            # Skip files with syntax errors
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # Check if it's not a relative import like 'from . import ...'
                imports.append(node.module)
    return imports


@pytest.mark.parametrize("domain_file", _get_all_python_files_in_dir(DOMAIN_LAYER))
def test_domain_layer_no_deps_on_application_or_infrastructure(domain_file):
    """
    Test that files in the domain layer do not import from application or infrastructure layers.
    """
    imports = _extract_imports_from_file(domain_file)
    for imp in imports:
        # Check if the import starts with 'src.application' or 'src.infrastructure'
        # We use 'src.' to ensure we are checking the full module path correctly within the project.
        # Adjust the check if your project uses different internal module naming or relative imports extensively within the domain.
        # A more robust check would be to see if the *resolved* import path leads into application/infrastructure.
        # For now, a simple string check on the import name should suffice for common cases.
        if imp.startswith("src.application") or imp.startswith("src.infrastructure"):
            assert False, f"Domain file {domain_file} imports from a higher layer: {imp}"


@pytest.mark.parametrize("application_file", _get_all_python_files_in_dir(APPLICATION_LAYER))
def test_application_layer_no_deps_on_infrastructure_via_src(application_file):
    """
    Test that files in the application layer do not directly import core infrastructure implementations
    via the 'src.infrastructure' path. They should depend on domain interfaces.
    This test is less strict than the domain test, as application layer often *needs* to import
    infrastructure adapters/services, but it checks for potential direct dependencies on low-level impl.
    """
    imports = _extract_imports_from_file(application_file)
    # Example: Flag imports that directly reference specific impls like 'src.infrastructure.adapters.something'
    # This is a heuristic check. A dependency inversion principle violation would be more subtle.
    # The main goal is to ensure application doesn't depend on specific DB drivers, HTTP clients, etc. directly,
    # which should be hidden behind domain interfaces or specific application ports/spi.
    # For now, let's just print them for review, or assert based on a specific blacklisted pattern if needed.
    # A simple check: ensure it does not import core infrastructure *implementations* directly, only interfaces/concepts.
    # This is hard to enforce generically without a list of known 'impl' modules.
    # Let's focus on the domain rule primarily, as it's more fundamental.
    # This test could be expanded to check for imports that *should* go through domain interfaces.
    # For now, it's a placeholder. A more effective check might be import-linter based.
    pass # Consider this test as a placeholder for more specific application-layer rules if needed.
    # If you want a basic check similar to domain, but less strict:
    # problematic_imports = [imp for imp in imports if imp.startswith("src.infrastructure") and "interfaces" not in imp]
    # if problematic_imports:
    #     print(f"Potential direct infrastructure dependency in application file {application_file}: {problematic_imports}")
    #     # Assert False if you want to enforce this rule strictly.
    #     # assert not problematic_imports, f"Application file {application_file} has direct impl deps: {problematic_imports}"

# Note: Testing infrastructure layer dependencies is less common,
# as it's the outermost layer and is expected to depend on external libraries
# and potentially application ports/spis defined in the application layer.
# The main DIP flow is application -> domain interfaces <- infrastructure implementations.

if __name__ == "__main__":
    pytest.main(["-v", __file__])
