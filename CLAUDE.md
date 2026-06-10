# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based web application providing a chatbot interface powered by OpenAI's GPT models. The application manages multiple chat rooms per user, maintains conversation context, and supports various GPT models (GPT-4o, GPT-4.1, GPT-o1, etc.).

**Tech Stack:**
- Django 4.2.2 (Python >=3.9.13)
- OpenAI Python SDK (v2.x)
- SQLite database
- Gunicorn WSGI server
- NGINX reverse proxy (Docker deployment)
- Markdown rendering with pymdown-extensions

## Development Commands

### Package Management
Use `uv`. Dependencies live in `pyproject.toml` and are locked in `uv.lock`

```bash
# Install runtime + dev dependencies into the project venv
uv sync
# Run a command in the venv
uv run python manage.py <command>

```

### Database Operations

```bash
# Run migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Create a test user (custom management command)
python manage.py create_test_user
```

### Static Files

```bash
# Collect static files (required before deployment)
python manage.py collectstatic --no-input
```

### Running the Application

**Local development:**
```bash
# Set required environment variables
export DJANGO_DEBUG=True
export OPENAI_API_KEY=sk-...

# Run development server
python manage.py runserver 0.0.0.0:8000
```

**Docker (production-like):**
```bash
# Build and start services (Django + NGINX)
docker-compose up --build

# Access at http://localhost:8888
```

**Local Gunicorn:**
```bash
# Using the helper script (activates .venv and starts Gunicorn)
./start_gunicorn.sh

# Or manually
gunicorn -c ./gunicorn.conf.py config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Testing

Tests run under pytest (pytest-django). All tests live in the `chatbot/tests/` package.

```bash
# Run the whole suite (coverage is configured in pyproject.toml)
uv run pytest

# Run a single module / class / test, or by keyword
uv run pytest chatbot/tests/test_models.py
uv run pytest chatbot/tests/test_views.py::TestLoginView
uv run pytest -k markdown
```

### Linting, formatting, type-checking

```bash
uv run ruff check .      # lint
uv run ruff format       # format
uv run mypy chatbot      # type-check (django-stubs)
```

Pre-commit hooks (ruff + mypy + basic file checks) are defined in `.pre-commit-config.yaml`; enable with `uv run pre-commit install`.

## Architecture

### Core Application Structure

**Django Project:** `config`
- Settings: `config/settings.py`
- Root URL config: `config/urls.py`
- WSGI: `config/wsgi.py`

**Main App:** `chatbot`
- Views: `chatbot/views.py` (handles all chat, auth, and room management)
- Models: `chatbot/models.py`
- URLs: `chatbot/urls.py`
- Template tags: `chatbot/templatetags/custom_filters.py`

### Data Models

**ChatRoom**
- UUID primary key
- Belongs to a User (ForeignKey)
- Has `is_hidden` flag for archiving
- Created timestamp for ordering

**Chat**
- Individual message-response pair
- Links to ChatRoom and User
- Stores both user message and assistant response

**ChatSession**
- Maintains conversation context per user-chatroom pair
- `session_id` format: `{user_id}-{chat_room_id}`
- Context stored as JSON serialized list of messages

**UserProfile**
- OneToOne with User
- Tracks `last_opened_chat` for redirect on login

### Key Views and Flow

**Authentication:**
- `login()` - Handles login and redirects to last opened chat or creates default room
- `register()` - Only enabled when `DEBUG=True`
- `logout()` - Standard logout

**Chat Management:**
- `chatbot(request, chat_room_id=None)` - Main view, handles both GET (render UI) and POST (send message)
- `create_chat_room_view()` - Creates new chat room via AJAX
- `save_chat_name()` - Renames chat room
- `archive_chat()` - Soft-deletes chat room (sets `is_hidden=True`)
- `get_chat_rooms()` - Returns user's chat rooms as JSON

**Message Flow:**
1. User submits message via POST with `message` and `model_id`
2. `handle_post_request()` retrieves or creates ChatSession
3. `get_chat_context()` loads conversation history from ChatSession
4. `get_openai_response()` calls OpenAI with last MAX_USED_CONTEXT messages (8 pairs = 16 messages)
5. `update_chat_context()` appends user message and assistant response
6. Context is trimmed if it exceeds MAX_CONTEXT_SIZE (2000 pairs)
7. Updated context saved to ChatSession
8. Chat message saved to database
9. Response returned as JSON with formatted HTML

### OpenAI Integration

**Configuration (chatbot/views.py:24-36):**
```python
MAX_CONTEXT_SIZE = 2000      # Max conversation pairs to keep
MAX_USED_CONTEXT = 8         # Pairs sent to OpenAI (16 messages)
TRIM_CONTEXT = True

GPT_MODELS = {
    "GPT4o": "gpt-4o",
    "GPT4o Mini": "gpt-4o-mini",
    # ... other models
}
```

**API Call:**
- Uses OpenAI's chat completions API (SDK v2.x)
- Max tokens: 4000
- Context includes last 16 messages (8 pairs) to stay within token limits
- Full conversation history stored in ChatSession for continuity

### Template System

**Templates location:** `templates/` (root level)
- `chatbot.html` - Main chat interface
- `login.html` - Login page
- `register.html` - Registration page
- `registration_disabled.html` - Shown when registration is disabled

**Custom Template Tags:**
- `markdown_to_html` - Converts markdown to HTML (uses markdown + pymdown-extensions)
- `inline_code_formatting` - Additional formatting for inline code

### Static Files

**Source:** `static/`
**Collected:** `staticfiles/` (via `collectstatic`)

In Docker, NGINX serves `/static/` from `./staticfiles`.

### Environment Variables

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for GPT requests

**Optional:**
- `DJANGO_SECRET_KEY` - Secret key (auto-generated if not set)
- `DJANGO_DEBUG` - Set to string `"True"` to enable debug mode
- `DJANGO_DB_PATH` - Custom path for SQLite database (falls back to `<BASE_DIR>/db.sqlite3`)

### Database Configuration

SQLite database path resolution (config/settings.py:94-105):
1. If `DJANGO_DB_PATH` env var is set and path exists: use `<DJANGO_DB_PATH>/db.sqlite3`
2. Otherwise: use `<BASE_DIR>/db.sqlite3`

### Security Notes

**Current settings (suitable for development only):**
- `ALLOWED_HOSTS = ["*"]`
- `SESSION_COOKIE_SECURE = False`
- `CSRF_COOKIE_SECURE = False`
- `CSRF_TRUSTED_ORIGINS = ['http://localhost:8888']`

**Production deployment requires:**
- Setting appropriate `ALLOWED_HOSTS`
- Enabling secure cookies (HTTPS)
- Configuring proper CSRF trusted origins
- Using environment-based `SECRET_KEY`

### URL Routing

**Main routes (chatbot/urls.py):**
- `/` - Default chatbot (redirects to last opened or first room)
- `/chatroom/<uuid>/` - Specific chat room
- `/create_chat_room/` - Create new room (POST)
- `/archive_chat_room/<uuid>/` - Archive room (POST)
- `/save_chat_name/` - Rename room (POST)
- `/get_chat_rooms/` - Get user's rooms (GET, returns JSON)
- `/login`, `/register`, `/logout` - Authentication

### Docker Deployment

**Services:**
- `django_app` - Django with Gunicorn (port 8000 internal)
- `nginx` - Reverse proxy (port 8888 external)

**Entry point:** `entrypoint.sh`
- Runs migrations if `db.sqlite3` doesn't exist
- Collects static files
- Execs into main container command (Gunicorn)

**Gunicorn config:** `gunicorn.conf.py`
- Log level: error
- Timeout: 120s
- Logs to stdout/stderr

## Development Workflow

### Adding New Features

1. **Model changes:**
   - Edit `chatbot/models.py`
   - Run `python manage.py makemigrations`
   - Run `python manage.py migrate`
   - Update admin.py if models should be admin-accessible

2. **New views:**
   - Add view function to `chatbot/views.py`
   - Add URL pattern to `chatbot/urls.py`
   - Create/update templates in `templates/`

3. **Frontend changes:**
   - Update templates in `templates/`
   - Add static files to `static/`
   - Run `collectstatic` before Docker deployment

### Common Patterns

**Creating a chat room:**
```python
from chatbot.models import ChatRoom
room = ChatRoom.objects.create(name="Room Name", user=user)
```

**Getting chat context:**
```python
session_id = f"{user.id}-{chat_room.id}"
chat_session, created = ChatSession.objects.get_or_create(
    session_id=session_id,
    chat_room=chat_room,
    user=user
)
context = json.loads(chat_session.context) if chat_session.context else []
```

**Saving updated context:**
```python
chat_session.context = json.dumps(context)
chat_session.save()
```

### Testing Considerations

- All tests live in the `chatbot/tests/` package (`test_*.py`), with shared fixtures in `conftest.py` and factory_boy factories in `factories.py` — reuse and extend these.
- DB-touching tests use the `db` fixture or `@pytest.mark.django_db`.
- OpenAI calls are mocked via `@patch("chatbot.views.ask_openai")`; tests never hit the live API.
- Test database uses SQLite for speed (production moves to Postgres in a later phase).

## Known Issues and TODOs

See `docs/ROADMAP.md` for the full refactor plan. Outstanding items:

1. **Registration:** Only available when `DEBUG=True` (in `register()` in views.py)
2. **HTTPS:** NGINX configuration needs SSL directives for production HTTPS deployment
3. **Context Trimming:** `trim_chat_context_if_needed()` reassigns a local without persisting it — effectively dead (addressed in the data-model rework)
4. **Module-global OpenAI key:** `openai.api_key` is set at import time, blocking per-user keys (addressed in the OpenAI-client rework)
5. **Invalid model ids:** `GPT_MODELS` contains placeholder ids (e.g. `gpt-o1`); replaced by a DB-backed model catalog in a later phase
6. **`save_chat_name` ownership:** the rename endpoint lacks an ownership check (IDOR) — fixed in the security-hardening phase

Recently resolved: test-layout collision (single `chatbot/tests/` package under pytest), duplicate `ChatRoom.name` field, bare `except` in register, and ruff/mypy/pre-commit tooling.

## Logging

Logger configured for `chatbot` app with DEBUG level (settings.py:30-35). Logs include:
- OpenAI permission errors
- Generic API errors
- Registration/login issues
- Invalid HTTP methods

Use `logger = logging.getLogger(__name__)` in views to access the logger.
