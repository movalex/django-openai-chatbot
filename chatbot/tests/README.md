# Chatbot Tests

Comprehensive test suite for the Django OpenAI Chatbot application using pytest.

## Test Structure

```
chatbot/tests/
├── __init__.py              # Package marker
├── conftest.py              # Pytest fixtures and configuration
├── factories.py             # Factory Boy factories for test data
├── test_models.py           # Model tests (ChatRoom, Chat, ChatSession, UserProfile)
├── test_views.py            # View tests (authentication, chat management, API endpoints)
├── test_templatetags.py     # Template tag and filter tests
└── test_smoke.py            # Basic smoke tests
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run with coverage report

```bash
pytest --cov=chatbot --cov-report=html
```

### Run specific test file

```bash
pytest chatbot/tests/test_models.py
```

### Run specific test class

```bash
pytest chatbot/tests/test_models.py::TestChatRoomModel
```

### Run specific test method

```bash
pytest chatbot/tests/test_models.py::TestChatRoomModel::test_create_chat_room
```

### Run tests by marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"
```

### Run with verbose output

```bash
pytest -v
```

## Test Coverage

Current test coverage includes:

### Models (test_models.py)
- **ChatRoom**: Creation, string representation, visibility, cascade deletion, multiple rooms per user, ordering
- **Chat**: Creation, string representation, room association, cascade deletion, multiple messages
- **ChatSession**: Creation, string representation, unique session IDs, cascade deletion, context storage
- **UserProfile**: Creation, last opened chat, cascade deletion, one-to-one relationship

### Views (test_views.py)
- **Authentication**: Login, logout, remember me, redirects
- **Chatbot View**: GET/POST requests, room access control, message sending, context management
- **Chat Room Management**: Create, rename, archive, list rooms
- **API Endpoints**: get_chat_rooms, create_chat_room, save_chat_name, archive_chat
- **Context Management**: Session persistence, history tracking, invalid JSON handling

### Template Tags (test_templatetags.py)
- **markdown_to_html**: Markdown conversion, code blocks, tables, lists, headers, links
- **inline_code_formatting**: Inline code wrapping, code block handling
- **adjust_indentation**: List formatting adjustments

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests that involve multiple components
- `@pytest.mark.slow` - Tests that take longer to execute

## Fixtures

Common fixtures available in `conftest.py`:

- `user` - Creates a test user
- `another_user` - Creates a second test user for multi-user scenarios
- `user_profile` - Creates a user profile
- `chat_room` - Creates a visible chat room
- `hidden_chat_room` - Creates a hidden chat room
- `chat_session` - Creates a chat session with context
- `chat_message` - Creates a chat message
- `authenticated_client` - Returns a Django test client with authenticated user

## Factories

Factory Boy factories in `factories.py`:

- `UserFactory` - Creates User instances
- `ChatRoomFactory` - Creates ChatRoom instances
- `ChatFactory` - Creates Chat instances
- `ChatSessionFactory` - Creates ChatSession instances
- `UserProfileFactory` - Creates UserProfile instances

Example usage:

```python
from chatbot.tests.factories import UserFactory, ChatRoomFactory

def test_example():
    user = UserFactory(username="testuser")
    room = ChatRoomFactory(user=user, name="Test Room")
```

## Mocking OpenAI API

Tests that interact with OpenAI API use mocking to avoid actual API calls:

```python
@patch("chatbot.views.ask_openai")
def test_chatbot_post_request(mock_openai, authenticated_client, chat_room):
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="AI response"))]
    mock_openai.return_value = mock_response

    # Test code here
```

## Coverage Reports

After running tests with coverage, view the HTML report:

```bash
pytest --cov=chatbot --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

To run tests in CI/CD pipelines:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=chatbot --cov-report=xml --cov-report=term

# Fail if coverage below 80%
pytest --cov=chatbot --cov-fail-under=80
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Fixtures**: Use fixtures for common setup to avoid code duplication
3. **Factories**: Use Factory Boy for creating test data with realistic values
4. **Mocking**: Mock external dependencies (OpenAI API, file system, etc.)
5. **Markers**: Tag tests appropriately for easy filtering
6. **Naming**: Use descriptive test names that explain what is being tested
7. **AAA Pattern**: Follow Arrange-Act-Assert pattern in tests

## Troubleshooting

### Database errors

If you encounter database errors, ensure Django settings are properly configured:

```bash
export DJANGO_SETTINGS_MODULE=django_chatbot.settings
```

### Import errors

Make sure you're in the project root directory and the virtual environment is activated:

```bash
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### OpenAI API errors

Tests should mock OpenAI calls. If you see actual API errors, check that mocking is properly set up.

## Adding New Tests

When adding new tests:

1. Choose the appropriate test file or create a new one
2. Use existing fixtures when possible
3. Add appropriate markers (`@pytest.mark.unit`, etc.)
4. Follow the AAA pattern (Arrange, Act, Assert)
5. Write descriptive test names
6. Mock external dependencies
7. Update this README if adding new test categories

## Test Database

Pytest-django automatically creates a test database for each test run. The database is created before tests run and destroyed afterward. No manual database setup is required.
