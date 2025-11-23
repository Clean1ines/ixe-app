.PHONY: test quality docker clean

# Setup
setup:
	pip install -r requirements.txt

# Testing
test:
	PYTHONPATH=. pytest tests/ -v --tb=short

test-unit:
	PYTHONPATH=. pytest tests/unit/ -v

test-integration:
	PYTHONPATH=. pytest tests/integration/ -v

# Quality
quality:
	PYTHONPATH=. python -m radon cc src/ -s
	bandit -r src/ -f plain

# Docker
docker-build:
	docker build -t scraping-refactor:latest .

docker-test:
	docker run --rm scraping-refactor:latest

# Clean
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf .pytest_cache .coverage htmlcov

# Quick setup verification
check:
	./check-setup.sh
