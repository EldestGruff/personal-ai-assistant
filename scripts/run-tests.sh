#!/bin/bash
#
# Run test suite with various options
# Usage: ./scripts/run-tests.sh [options]
#
# Options:
#   all         - Run all tests (default)
#   unit        - Run only unit tests
#   integration - Run only integration tests
#   coverage    - Run tests with coverage report
#   fast        - Run fast tests only (skip slow)

set -e

TEST_OPTION=${1:-all}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🧪 Running tests: $TEST_OPTION"

case $TEST_OPTION in
    unit)
        pytest tests/ -m unit -v
        ;;
    integration)
        pytest tests/ -m integration -v
        ;;
    coverage)
        pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
        echo ""
        echo "📊 Coverage report generated: htmlcov/index.html"
        ;;
    fast)
        pytest tests/ -m "not slow" -v
        ;;
    all|*)
        pytest tests/ -v
        ;;
esac

echo "✅ Tests complete"
