import ast
import os
from collections import defaultdict

def analyze_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    imports = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith('src.'):
                imports['absolute_src'].append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('src.'):
                    imports['absolute_src'].append(alias.name)
    
    return imports

print("=== IMPORT ANALYSIS ===")
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            imports = analyze_file(path)
            if imports['absolute_src']:
                print(f"{path}:")
                for imp in imports['absolute_src']:
                    print(f"  - {imp}")
