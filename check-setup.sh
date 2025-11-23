#!/bin/bash
set -e

echo "=== SETUP CHECK ==="

# Check Python
echo "Python version: $(python --version)"
echo "Python path:"
python -c "import sys; [print(f'  {p}') for p in sys.path]"

# Check imports
echo "Testing imports..."
python -c "
import sys
sys.path.append('.')
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

# Check requirements
echo "Testing requirements installation..."
pip install -r requirements.txt --quiet && echo "✅ Requirements installed successfully"

echo "=== SETUP CHECK COMPLETE ==="
