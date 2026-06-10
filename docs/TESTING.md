# Testing Guide

This project uses pytest for testing with comprehensive coverage of models, views, and template tags.

## Quick Start

```bash
# Install dependencies (runtime + dev)
uv sync
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=chatbot --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Statistics

- **Total Tests**: 84
- **Test Files**: 4
- **Code Coverage**: 81%
- **All Tests**: PASSING ✓

## Test Suite Breakdown

### Models (25 tests)
- ChatRoom model (7 tests)
- Chat model (6 tests)
- ChatSession model (6 tests)
- UserProfile model (6 tests)

Coverage: **100%** of models.py

### Views (58 tests)
- Authentication (login, logout, register)
- Chatbot main view (GET/POST)
- Chat room management (create, rename, archive)
- API endpoints
- Context management
- Access control

Coverage: **78%** of views.py

### Template Tags (25 tests)
- markdown_to_html filter
- inline_code_formatting filter
- adjust_indentation helper
- Integration tests

Coverage: **100%** of custom_filters.py

### Smoke Tests (1 test)
- Basic Django settings validation

## Running Specific Tests

```bash
# Run by file
uv run pytest chatbot/tests/test_models.py

# Run by class
uv run pytest chatbot/tests/test_models.py::TestChatRoomModel

# Run by test name
uv run pytest chatbot/tests/test_models.py::TestChatRoomModel::test_create_chat_room

# Run by marker
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m "not slow"    # Skip slow tests
```

## Test Organization

```
chatbot/tests/
├── conftest.py              # Shared fixtures
├── factories.py             # Factory Boy data factories
├── test_models.py           # Model tests
├── test_views.py            # View and API tests
├── test_templatetags.py     # Template filter tests
├── test_smoke.py            # Smoke tests
└── README.md                # Detailed test documentation
```

## Key Features

- **Fixtures**: Reusable test data via pytest fixtures
- **Factories**: Factory Boy for generating realistic test data
- **Mocking**: OpenAI API calls are mocked to avoid actual API usage
- **Markers**: Tests tagged as unit, integration, or slow
- **Coverage**: HTML and terminal coverage reports
- **Database**: Automatic test database creation/teardown

## Configuration Files

- `pyproject.toml` - pytest, coverage, and dev-dependency configuration

## Continuous Integration

For CI/CD pipelines:

```bash
# Install dependencies
uv sync
# Run tests with coverage
uv run pytest --cov=chatbot --cov-report=xml --cov-report=term

# Fail if coverage below 80%
uv run pytest --cov=chatbot --cov-fail-under=80
```

## Common Commands

```bash
# Quick test run
uv run pytest -v

# Detailed output with coverage
uv run pytest -v --cov=chatbot --cov-report=term-missing

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Run in parallel (requires pytest-xdist)
uv run pytest -n auto

# Show print statements
uv run pytest -s
```

## Coverage Goals

- **Models**: 100% (achieved ✓)
- **Template Tags**: 100% (achieved ✓)
- **Views**: Target 85% (current 78%)
- **Overall**: Target 85% (current 81%)

## Uncovered Code

Main uncovered areas in views.py:
- OpenAI API error handling (lines 167-174)
- Register view (lines 290-321) - disabled when DEBUG=False
- Edge cases in chatbot redirect logic (lines 90-99)

## Writing New Tests

See `chatbot/tests/README.md` for detailed guidelines on:
- Using fixtures and factories
- Mocking external dependencies
- Following naming conventions
- Best practices and patterns

## Dependencies

Test dependencies (the `dev` group in `pyproject.toml`, installed by default with `uv sync`):
- pytest >= 8.0.0
- pytest-django >= 4.7.0
- pytest-cov >= 4.1.0
- pytest-mock >= 3.12.0
- factory-boy >= 3.3.0

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'pytest'`
**Solution**: Run `uv sync`

**Issue**: Database errors
**Solution**: Ensure `DJANGO_SETTINGS_MODULE=config.settings` is set

**Issue**: Import errors
**Solution**: Run from project root with activated virtual environment

For more help, see `chatbot/tests/README.md`
