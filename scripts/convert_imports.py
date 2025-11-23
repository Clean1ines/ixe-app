#!/usr/bin/env python3
import ast
import os
import re
from pathlib import Path

class ImportConverter(ast.NodeTransformer):
    def __init__(self, current_file, project_root):
        self.current_file = current_file
        self.project_root = project_root
        self.changes = []
    
    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith('src.'):
            # Calculate relative import path
            relative_path = self.calculate_relative_import(node.module)
            if relative_path:
                self.changes.append((node.module, relative_path))
                node.module = relative_path
        return node
    
    def calculate_relative_import(self, absolute_import):
        # Convert "src.application.services" to relative path
        parts = absolute_import.split('.')
        if parts[0] != 'src':
            return None
            
        # Remove 'src' prefix
        target_module = '.'.join(parts[1:])
        
        # Calculate relative depth
        current_dir = Path(self.current_file).parent
        rel_depth = len(current_dir.relative_to(self.project_root).parts)
        
        if rel_depth == 0:
            return target_module
        else:
            prefix = '.' * rel_depth
            return prefix + target_module

def convert_file_imports(filepath, project_root):
    with open(filepath, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        converter = ImportConverter(filepath, project_root)
        new_tree = converter.visit(tree)
        
        if converter.changes:
            print(f"Converting imports in {filepath}:")
            for old, new in converter.changes:
                print(f"  {old} -> {new}")
                # Simple string replacement for now
                content = content.replace(f"from {old}", f"from {new}")
            
            with open(filepath, 'w') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False

def main():
    project_root = Path('.').absolute()
    converted_count = 0
    
    for py_file in project_root.rglob('src/**/*.py'):
        if convert_file_imports(str(py_file), project_root):
            converted_count += 1
    
    print(f"Converted imports in {converted_count} files")

if __name__ == "__main__":
    main()
