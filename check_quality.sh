#!/bin/bash

echo "🚀 Running Code Quality Checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 passed${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        FAILED=1
    fi
}

FAILED=0

section "Radon - Cyclomatic Complexity"
radon cc src/ -s -a
check_status "Radon complexity check"

section "Flake8 - Code Style"
flake8 src/ --count --statistics
check_status "Flake8 style check"

section "MyPy - Type Checking"
mypy src/ --no-error-summary
check_status "MyPy type check"

section "Test Suite"
python -m pytest tests/ -x --tb=short -q
check_status "Test suite"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All checks passed! Code quality is good.${NC}"
else
    echo -e "\n${RED}❌ Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
