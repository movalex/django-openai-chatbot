# Django-OpenAI Chatbot

This project is a Django-based web application that integrates with OpenAI to provide a chatbot experience through a browser UI.

The app runs as a standard Django project (`django_chatbot`) with a `chatbot` app, served by Gunicorn behind NGINX in Docker. Static files are collected into `staticfiles` and served directly by NGINX.

The repository includes:
- A Dockerfile for building the Django application image (dependencies installed with [uv](https://docs.astral.sh/uv/))
- A `docker-compose.yml` stack with a Django/Gunicorn container and an NGINX reverse proxy
- Basic NGINX configuration under `./nginx`

To enable HTTPS support, you will need to extend the NGINX configuration with SSL directives and provide certificates (see [HTTPS / TLS](#https--tls)).

> **Note**
> Some operational details (for example, advanced deployment guidance) are intentionally left as TODOs where they are not explicitly configured in this repository.

---

## Tech stack

- **Language:** Python 3.13
- **Web framework:** Django 4.2.2 (`django_chatbot` project, `chatbot` app)
- **WSGI server:** Gunicorn
- **Reverse proxy / static:** NGINX
- **Database:** SQLite (file `db.sqlite3`, configurable via `DJANGO_DB_PATH`)
- **OpenAI integration:** `openai` Python SDK (v2.x)
- **Markdown rendering:** `markdown` + `pymdown-extensions`
- **Containerization:** Docker + docker-compose
- **Dependency management:** [uv](https://docs.astral.sh/uv/) — dependencies declared in `pyproject.toml`, pinned in `uv.lock`
- **Tooling:** ruff (lint + format), mypy (django-stubs), pytest (pytest-django), pre-commit

---

## Requirements

**Local (no Docker)**
- [uv](https://docs.astral.sh/uv/) — manages the Python toolchain and the virtual environment

**Docker**
- Docker
- docker-compose

uv installs and pins the project's Python version (3.13), so a preinstalled system Python is not required.

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/yourgithubusername/django-openai-chatbot.git
cd django-openai-chatbot
```

### 2. Configure environment

Copy the template and set your key:

```bash
cp .env.template .env
```

Edit `.env`:

```dotenv
OPENAI_API_KEY=sk-...      # required to call the OpenAI API
DJANGO_DEBUG=True          # enable Django debug mode for local development
```

The project loads `.env` automatically at startup via `django-environ` (see `django_chatbot/settings.py`). Real environment variables take precedence over the file. The full list is in [Environment variables](#environment-variables).

---

## Running locally (without Docker)

### 1. Install dependencies

```bash
uv sync
```

This creates a virtual environment and installs the runtime dependencies plus the `dev` dependency group (included by default) from `uv.lock`. Use `uv sync --no-dev` for a runtime-only install.

### 2. Initialize the database and collect static files

```bash
uv run python manage.py migrate
uv run python manage.py collectstatic --no-input
```

### 3. Run the development server

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

Open your browser at http://localhost:8000

---

## Running with Docker and docker-compose

The recommended way to run the full stack (Django via Gunicorn behind NGINX) is via `docker-compose`. Dependencies are installed inside the image with uv from `uv.lock`.

### 1. Set required environment

Make sure `.env` contains your `OPENAI_API_KEY` (compose reads it for variable substitution), or export it in your shell:

```bash
export OPENAI_API_KEY=sk-...
```

### 2. Build and start the services

```bash
docker compose up --build
```

This will:

- Build the `django_app` image using the provided Dockerfile
- Start `django_app` with Gunicorn using `/app/gunicorn.conf.py`
- Start an `nginx` container listening on port `8888`
- Mount `./staticfiles` into the NGINX container for static assets

Once the containers are up, access the application via NGINX at http://localhost:8888

> **TODO:** Provide a dedicated `docker-compose.override.yml` example for running Django's development server inside the container.

---

## Entry points and scripts

- **Django management:** `uv run python manage.py <command>` (e.g. `uv run python manage.py runserver 0.0.0.0:8000`)
- **Gunicorn (Docker):** defined in `docker-compose.yml`:
  ```bash
  gunicorn -c /app/gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000
  ```
- **Container entrypoint:** `entrypoint.sh` — collects static files, applies migrations, then execs the container command.
- **Local Gunicorn:**
  ```bash
  uv run gunicorn -c ./gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000 --workers 3
  ```

---

## Environment variables

The following environment variables are read by the project (see `django_chatbot/settings.py` and `docker-compose.yml`). They can be placed in `.env`, which is loaded automatically.

- `OPENAI_API_KEY`
  - Required to make outbound OpenAI requests.
  - Passed into the Django container in `docker-compose.yml`.

- `DJANGO_DEBUG`
  - Set to the string `True` to enable Django DEBUG mode.

- `DJANGO_SECRET_KEY`
  - Secret key for Django.
  - If not set, a random key is generated at startup (suitable for local development only).

- `DJANGO_DB_PATH`
  - Optional; directory path for the SQLite database.
  - If set, Django uses `<DJANGO_DB_PATH>/db.sqlite3` if it exists; otherwise it falls back to `<BASE_DIR>/db.sqlite3`.

---

## Tests

Tests run under pytest (pytest-django). The suite lives in the `chatbot/tests/` package, with shared fixtures in `conftest.py` and factory_boy factories in `factories.py`.

```bash
# Run the whole suite (coverage is configured in pyproject.toml)
uv run pytest

# Run a file, class, single test, or by keyword
uv run pytest chatbot/tests/test_models.py
uv run pytest chatbot/tests/test_views.py::TestLoginView
uv run pytest -k markdown

# Filter by marker
uv run pytest -m unit
```

The test database uses SQLite for speed. OpenAI calls are mocked, so the suite never hits the live API. See `chatbot/tests/README.md` for guidelines on fixtures, factories, and conventions.

### Linting, formatting, type-checking

```bash
uv run ruff check .      # lint
uv run ruff format       # format
uv run mypy chatbot      # type-check (django-stubs)
```

Pre-commit hooks (ruff + mypy + basic file checks) are defined in `.pre-commit-config.yaml`; enable them with `uv run pre-commit install`.

---

## Project structure

High-level layout (non-exhaustive):

```text
django-openai-chatbot/
├── chatbot/                  # Django app: views, models, templates, tests
│   ├── management/           # Custom management commands
│   ├── migrations/           # Django migrations
│   ├── templatetags/         # Custom template tags/filters (e.g. markdown_to_html)
│   └── tests/                # pytest suite (conftest fixtures, factories, test modules)
├── django_chatbot/           # Django project configuration (settings, URLs, WSGI/ASGI)
├── docs/                     # Project documentation (roadmap, phase guides)
├── templates/                # HTML templates
├── static/                   # Source static assets (CSS, JS, images)
├── staticfiles/              # Collected static files (built via collectstatic)
├── nginx/                    # NGINX configuration
├── Dockerfile                # Django application image (uv-based)
├── docker-compose.yml        # Multi-container stack (Django + NGINX)
├── gunicorn.conf.py          # Gunicorn configuration
├── entrypoint.sh             # Container entrypoint script
├── start_gunicorn.sh         # Helper script for running Gunicorn locally
├── manage.py                 # Django management script
├── pyproject.toml            # Project metadata, dependencies, and tool config
├── uv.lock                   # Locked dependency versions
├── .python-version           # Pinned Python version (3.13)
├── LICENSE                   # MIT license
└── README.md                 # This file
```

> **TODO:** Document key Django views, URL routes, and templates once the chatbot UI and API surface are finalized.

---

## Static files, Gunicorn, and NGINX

- **Static files**
  - `STATIC_URL = '/static/'`
  - `STATIC_ROOT = BASE_DIR / 'staticfiles'`
  - `STATICFILES_DIRS = [ BASE_DIR / 'static' ]`
  - In the Docker stack, NGINX serves `/static/` from `/app/staticfiles`, which is mapped to `./staticfiles` on the host.

- **Gunicorn**
  - Started in Docker with:
    ```bash
    gunicorn -c /app/gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000
    ```
  - Logging: access and error logs go to stdout/stderr; log level is `error` by default; timeout is 120s.

- **NGINX**
  - Listens on port `8888`, proxies to `django_app:8000`.
  - Static location `/static/` is mapped to `/app/staticfiles`.

---

## HTTPS / TLS

To enable HTTPS support with NGINX you will need to:

1. Obtain TLS certificates (for example via Let's Encrypt or another CA).
2. Mount the certificates into the NGINX container (e.g., under `/etc/letsencrypt`).
3. Update the NGINX configuration in `nginx/default.conf` to include directives such as:

   ```nginx
   ssl_certificate /path/to/fullchain.pem;
   ssl_certificate_key /path/to/privkey.pem;
   ```

4. Enable the SSL server block and redirect HTTP to HTTPS as required.

Consult the official NGINX documentation for detailed SSL/TLS configuration options.

> **TODO:** Provide a concrete example `default.conf` with SSL blocks enabled and documented volume mounts for certificates.

---

## Contributing

Contributions are welcome. A typical workflow is:

1. Fork this repository.
2. Create a new branch: `git checkout -b feature/my-feature`.
3. Make your changes and add tests where appropriate.
4. Run the checks: `uv run ruff check . && uv run pytest`.
5. Commit with a descriptive message.
6. Push to your fork and open a Pull Request.

For more details, see GitHub's documentation on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2024 Alexey Bogomolov