#!/usr/bin/env python3
import sys
import os
import subprocess

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("=== DIAGNOSTIC REPORT ===")
    
    # Python info
    print("Python Info:")
    print(f"  Version: {sys.version}")
    print(f"  Executable: {sys.executable}")
    print(f"  Path: {sys.path}")
    
    # Check critical files
    critical_files = [
        "src/__init__.py",
        "src/domain/__init__.py", 
        "src/application/__init__.py",
        "src/infrastructure/__init__.py",
        "tests/__init__.py"
    ]
    
    print("\nCritical Files Check:")
    for file in critical_files:
        exists = os.path.exists(file)
        print(f"  {file}: {'✅' if exists else '❌'}")
    
    # Test imports
    print("\nImport Test:")
    test_imports = [
        "src.application.value_objects.scraping.subject_info",
        "src.domain.models.problem",
        "src.application.use_cases.scraping.scrape_subject_use_case"
    ]
    
    for import_path in test_imports:
        try:
            __import__(import_path)
            print(f"  {import_path}: ✅")
        except ImportError as e:
            print(f"  {import_path}: ❌ ({e})")
    
    # Check requirements
    print("\nRequirements Check:")
    code, out, err = run_command("pip list")
    if code == 0:
        packages = ["pytest", "pytest-asyncio", "aiohttp", "playwright"]
        for pkg in packages:
            if pkg in out:
                print(f"  {pkg}: ✅")
            else:
                print(f"  {pkg}: ❌")
    
    print("\n=== DIAGNOSIS COMPLETE ===")

if __name__ == "__main__":
    main()
