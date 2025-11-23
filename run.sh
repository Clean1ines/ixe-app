#!/bin/bash
set -e

# Determine Python version and set appropriate paths
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Set PYTHONPATH based on execution context
if [ -d "/app" ]; then
    # Docker context
    export PYTHONPATH="/app"
elif [ -d "src" ]; then
    # Local development context
    export PYTHONPATH=".:$PYTHONPATH"
else
    echo "❌ Cannot determine execution context"
    exit 1
fi

# Main command
case "${1:-help}" in
    test)
        echo "Running tests..."
        python -m pytest tests/ -v --cov=src
        ;;
    quality)
        echo "Running quality checks..."
        ./scripts/quality-monitor.sh
        ;;
    security)
        echo "Running security scan..."
        bandit -r src/ -c bandit.yml
        ;;
    docker-build)
        echo "Building Docker image..."
        docker build -t scraping-refactor:latest .
        ;;
    *)
        echo "Usage: $0 {test|quality|security|docker-build}"
        echo "  test        - Run test suite"
        echo "  quality     - Run quality checks"
        echo "  security    - Run security scan"
        echo "  docker-build - Build Docker image"
        exit 1
        ;;
esac
