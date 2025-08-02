# Finance Hub - Test Suite Makefile

.PHONY: help test test-backend test-frontend test-e2e test-all coverage clean

# Default target
help:
	@echo "Finance Hub Test Suite Commands:"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make test-e2e       - Run E2E tests"
	@echo "  make test-all       - Run all tests"
	@echo "  make coverage       - Generate coverage reports"
	@echo "  make clean          - Clean test artifacts"

# Backend tests
test-backend:
	@echo "Running backend tests..."
	cd backend && python manage.py test apps.banking.tests -v 2

test-backend-coverage:
	@echo "Running backend tests with coverage..."
	cd backend && coverage run --source='.' manage.py test apps.banking.tests -v 2
	cd backend && coverage report
	cd backend && coverage html

# Frontend tests
test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

test-frontend-coverage:
	@echo "Running frontend tests with coverage..."
	cd frontend && npm run test:coverage

test-frontend-watch:
	@echo "Running frontend tests in watch mode..."
	cd frontend && npm run test:watch

# E2E tests
test-e2e:
	@echo "Running E2E tests..."
	npx playwright test

test-e2e-ui:
	@echo "Running E2E tests with UI..."
	npx playwright test --ui

test-e2e-debug:
	@echo "Running E2E tests in debug mode..."
	npx playwright test --debug

# Run all tests
test-all: test-backend test-frontend test-e2e
	@echo "All tests completed!"

# Generate coverage reports
coverage: test-backend-coverage test-frontend-coverage
	@echo "Coverage reports generated:"
	@echo "  Backend: backend/htmlcov/index.html"
	@echo "  Frontend: frontend/coverage/lcov-report/index.html"

# Linting and type checking
lint-backend:
	@echo "Linting backend code..."
	cd backend && flake8 apps/
	cd backend && black --check apps/
	cd backend && isort --check-only apps/

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

typecheck-frontend:
	@echo "Type checking frontend code..."
	cd frontend && npm run typecheck

lint-all: lint-backend lint-frontend typecheck-frontend
	@echo "All linting completed!"

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/htmlcov backend/.coverage backend/coverage.xml
	rm -rf frontend/coverage
	rm -rf playwright-report test-results
	@echo "Clean complete!"

# Install dependencies
install-deps:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt && pip install -r requirements-dev.txt
	cd frontend && npm ci
	npx playwright install --with-deps

# Database operations
db-reset:
	@echo "Resetting test database..."
	cd backend && python manage.py migrate --noinput
	cd backend && python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='test@example.com').delete(); User.objects.create_user(email='test@example.com', password='Test123!@#')"

# Development servers
dev-backend:
	cd backend && python manage.py runserver

dev-frontend:
	cd frontend && npm run dev

dev-all:
	@echo "Starting all development servers..."
	@make -j2 dev-backend dev-frontend