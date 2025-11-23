#!/bin/bash
set -e

echo "=== QUALITY MONITOR ==="
echo "Timestamp: $(date)"
echo ""

# Проверка импортов
echo "## IMPORT CHECK"
PYTHONPATH=.:$PYTHONPATH python -c "
import sys
print('Python path:')
for p in sys.path:
    print(f'  {p}')

try:
    from src.application.value_objects.scraping.subject_info import SubjectInfo
    print('✅ SubjectInfo import - OK')
except Exception as e:
    print(f'❌ SubjectInfo import failed: {e}')

try:
    from src.domain.models.problem import Problem  
    print('✅ Problem import - OK')
except Exception as e:
    print(f'❌ Problem import failed: {e}')

try:
    from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
    print('✅ ScrapeSubjectUseCase import - OK')
except Exception as e:
    print(f'❌ ScrapeSubjectUseCase import failed: {e}')
"

# Complexity analysis
echo ""
echo "## COMPLEXITY ANALYSIS"
if command -v python > /dev/null 2>&1; then
    PYTHONPATH=.:$PYTHONPATH python -m radon cc src/ -s 2>/dev/null > /dev/null
    if [ $? -eq 0 ]; then
        C_METHODS=$(PYTHONPATH=.:$PYTHONPATH python -m radon cc src/ -s 2>/dev/null | grep " C " | wc -l)
        B_METHODS=$(PYTHONPATH=.:$PYTHONPATH python -m radon cc src/ -s 2>/dev/null | grep " B " | wc -l)
        echo "C-complexity methods: $C_METHODS"
        echo "B-complexity methods: $B_METHODS"

        if [ $C_METHODS -gt 50 ]; then
            echo "❌ CRITICAL: Too many high-complexity methods"
        elif [ $C_METHODS -gt 45 ]; then
            echo "⚠️  WARNING: High complexity methods approaching threshold"
        else
            echo "✅ Complexity within acceptable range"
        fi

        echo ""
        echo "Top 10 most complex methods:"
        PYTHONPATH=.:$PYTHONPATH python -m radon cc src/ -s 2>/dev/null | grep -E "(C |B )" | head -10
    else
        echo "Radon analysis failed"
    fi
else
    echo "Python not available for complexity analysis"
fi

# Security scan
echo ""
echo "## SECURITY SCAN"
if command -v bandit > /dev/null 2>&1; then
    bandit -r src/ -f plain 2>/dev/null | head -20 || echo "Bandit scan completed"
else
    echo "Bandit not installed"
fi

# Architecture check
echo ""
echo "## ARCHITECTURE CHECK"
PYTHONPATH=.:$PYTHONPATH python -c "
import ast, os

violation_count = 0
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path) as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and 'src.infrastructure' in node.module and 'src.domain' in path:
                                print(f'❌ Domain imports Infrastructure: {path}')
                                violation_count += 1
            except Exception as e:
                print(f'Error parsing {path}: {e}')

print(f'Total architecture violations: {violation_count}')
" || echo "Architecture check failed"

# Hardcoded values check
echo ""
echo "## HARCODED VALUES"
if command -v find > /dev/null 2>&1; then
    HARCODED_COUNT=$(find src/ -name "*.py" -exec grep -c "https://fipi.ru" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
    echo "Hardcoded FIPI URLs: ${HARCODED_COUNT:-0}"

    if [ "${HARCODED_COUNT:-0}" -gt 0 ]; then
        echo "Files with hardcoded URLs:"
        find src/ -name "*.py" -exec grep -l "https://fipi.ru" {} \; 2>/dev/null || true
    fi
else
    echo "Find command not available"
fi

echo ""
echo "=== QUALITY MONITOR COMPLETE ==="
