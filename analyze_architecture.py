import ast
import os
from pathlib import Path

def analyze_imports(file_path):
    """Анализирует импорты в файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    
    return imports

def check_layer_violations():
    """Проверяет нарушения слоевой архитектуры"""
    violations = []
    
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                imports = analyze_imports(file_path)
                
                # Проверяем, чтобы domain не импортировал application/infrastructure
                if 'domain' in str(file_path):
                    for imp in imports:
                        if any(layer in imp for layer in ['application', 'infrastructure']):
                            violations.append(f"Domain layer violation: {file_path} imports {imp}")
                
                # Application не должен импортировать infrastructure напрямую
                elif 'application' in str(file_path):
                    for imp in imports:
                        if 'infrastructure' in imp and 'interfaces' not in imp:
                            violations.append(f"Application layer violation: {file_path} imports {imp}")
    
    return violations

if __name__ == "__main__":
    violations = check_layer_violations()
    for violation in violations:
        print(violation)
