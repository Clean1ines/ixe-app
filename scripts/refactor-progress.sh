#!/bin/bash

echo "=== REFACTORING PROGRESS TRACKER ==="
echo "Baseline: 50 C-complexity methods"

CURRENT_C=$(python -m radon cc src/ -s | grep " C " | wc -l)
IMPROVEMENT=$((50 - CURRENT_C))
PERCENT_IMPROVEMENT=$(echo "scale=2; $IMPROVEMENT / 50 * 100" | bc)

echo "Current C-methods: $CURRENT_C"
echo "Improvement: $IMPROVEMENT methods ($PERCENT_IMPROVEMENT%)"

# Top candidates for refactoring
echo ""
echo "TOP REFACTORING CANDIDATES:"
python -m radon cc src/ -s | grep " C " | sort -k5 -nr | head -5

# Check critical files
echo ""
echo "CRITICAL FILES STATUS:"
for file in "src/domain/models/problem.py" "src/application/use_cases/scraping/scrape_subject_use_case.py" "src/application/services/page_scraping_service.py"; do
    if [ -f "$file" ]; then
        COMPLEXITY=$(python -m radon cc "$file" -s | grep " C " | wc -l)
        echo "$file: $COMPLEXITY C-methods"
    fi
done
