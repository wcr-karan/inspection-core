.PHONY: install test coverage build deploy clean

# Install development dependencies
install:
	pip install -r requirements-dev.txt

# Run all tests
test:
	python -m pytest

# Run tests with coverage report
coverage:
	python -m pytest --cov=backend --cov-report=term-missing

# Build the SAM application
build:
	sam build

# Deploy to AWS (guided mode for first deploy)
deploy:
	sam deploy --guided

# Clean build artifacts
clean:
	rm -rf .aws-sam/ .pytest_cache/ __pycache__/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
