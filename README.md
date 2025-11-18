### Django‑OpenAI Chatbot

This project is a Django‑based web application that integrates with OpenAI to provide a chatbot experience through a browser UI.

The app runs as a standard Django project (`django_chatbot`) with a `chatbot` app, served by Gunicorn behind NGINX in Docker. Static files are collected into `staticfiles` and served directly by NGINX.

The repository includes:
- A Dockerfile for building the Django application image
- A `docker-compose.yml` stack with a Django/Gunicorn container and an NGINX reverse proxy
- Basic NGINX configuration under `./nginx`

To enable HTTPS support, you will need to extend the NGINX configuration with SSL directives and provide certificates (see [HTTPS / TLS](#https--tls)).

![](https://i.imgur.com/cNTCTFA.png)

> **Note**
> Some operational details (for example, exact OpenAI model names or advanced deployment guidance) are intentionally left as TODOs where they are not explicitly configured in this repository.

---

### Tech stack

- **Language:** Python 3.11 (Docker base image); supports Python `>=3.9.13` per `pyproject.toml`
- **Web framework:** Django 4.2.2 (`django_chatbot` project, `chatbot` app)
- **ASGI/WSGI server:** Gunicorn
- **Reverse proxy / static:** NGINX
- **Database:** SQLite (file `db.sqlite3`, configurable via `DJANGO_DB_PATH`)
- **OpenAI integration:** `openai` Python SDK (v2.x)
- **Markdown rendering:** `markdown` + `pymdown-extensions`
- **Containerization:** Docker + docker‑compose
- **Dependency management:**
  - `requirements.txt` for runtime
  - `pyproject.toml` (PEP 621 metadata, alternative dependency declaration)

---

### Requirements

**Local (no Docker)**

- Python 3.11 (recommended; matches Docker image)
- pip
- (Optional but recommended) virtualenv (`python -m venv`)

**Docker setup**

- Docker
- docker‑compose

---

### Getting started

#### 1. Clone the repository

```bash
git clone https://github.com/yourgithubusername/django-openai-chatbot.git
cd django-openai-chatbot
```

You can rename the Git remote/URL to your fork as needed.

---

### Running locally (without Docker)

#### 1. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure environment

At minimum for development:

```bash
export DJANGO_DEBUG=True
export OPENAI_API_KEY=sk-...  # required if you want to call the OpenAI API
```

Optional environment variables are described in [Environment variables](#environment-variables).

You can set these in your shell profile (`.bashrc`, `.zshrc`, etc.) or use a `.env` loader of your choice (not provided by default).

#### 4. Initialize the database and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

#### 5. Run the development server

```bash
python manage.py runserver 0.0.0.0:8000
```

Open your browser at:

- http://localhost:8000

---

### Running with Docker and docker‑compose

The recommended way to run the full stack (Django via Gunicorn behind NGINX) is via `docker-compose`.

#### 1. Set required environment

```bash
export OPENAI_API_KEY=sk-...
```

You may also export `DJANGO_DEBUG=True` if you want debug settings inside the container, but this is not strictly required for basic usage.

#### 2. Build and start the services

```bash
docker-compose up --build
```

This will:

- Build the `django_app` image using the provided Dockerfile
- Start `django_app` with Gunicorn using `/app/gunicorn.conf.py`
- Start an `nginx` container listening on port `8888`
- Mount `./staticfiles` into the NGINX container for static assets

Once containers are up, access the application via NGINX at:

- http://localhost:8888

#### 3. Development server via Docker (optional)

For development, you may want to run Django’s development server instead of Gunicorn inside the `django_app` container. One option is to temporarily override the command in `docker-compose.yml`:

```yaml
services:
  django_app:
    command: python manage.py runserver 0.0.0.0:8000
```

Then start the stack:

```bash
docker-compose up
```

> **TODO:** Provide a dedicated `docker-compose.override.yml` example for dev mode.

---

### Entry points and scripts

- **Django management:** `manage.py`
  - Example: `python manage.py runserver 0.0.0.0:8000`
- **Gunicorn (Docker):**
  - Defined in `docker-compose.yml`:
    ```bash
    gunicorn -c /app/gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000
    ```
- **Container entrypoint:** `entrypoint.sh`
  - Collects static files and runs migrations the first time `db.sqlite3` is absent, then execs the container command.
- **Local Gunicorn helper script:** `start_gunicorn.sh`
  - Activates a local virtualenv (`.venv`) and starts Gunicorn with
    ```bash
    gunicorn -c ./gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000 --workers 3
    ```
  - This script assumes a particular directory layout and shell configuration; adjust it to your environment or treat it as an example.

---

### Environment variables

The following environment variables are read by the project (see `django_chatbot/settings.py` and `docker-compose.yml`):

- `DJANGO_SECRET_KEY`
  - Secret key for Django.
  - If not set, a random key is generated at startup (suitable for local development only).

- `DJANGO_DEBUG`
  - Set to the string `True` to enable Django DEBUG mode.
  - Example: `export DJANGO_DEBUG=True`

- `DJANGO_DB_PATH`
  - Optional; directory path for the SQLite database.
  - If set, Django uses `<DJANGO_DB_PATH>/db.sqlite3` if it exists; otherwise it falls back to `<BASE_DIR>/db.sqlite3`.

- `OPENAI_API_KEY`
  - Required to make outbound OpenAI requests.
  - Passed into the Django container in `docker-compose.yml`.

> **TODO:** Document any additional OpenAI‑specific settings (e.g., default model, temperature) if configuration is added in the codebase.

---

### Tests

The project uses Django’s built‑in test runner (no pytest).

#### Running all tests

```bash
python manage.py test -v 2
```

At the time of writing, there is a single test class in `chatbot/tests.py`:

- `FiltersTest.test_markdown_output` — checks the HTML produced by the `markdown_to_html` template filter.

> **Known issue:** This test is currently failing due to strict HTML expectations that may not match the exact output of the Markdown renderer. See `chatbot/tests.py` and `chatbot/templatetags/custom_filters.py` before relying on it as a regression test.

#### Running a specific test

```bash
python manage.py test chatbot.tests.FiltersTest -v 2
python manage.py test chatbot.tests.FiltersTest.test_markdown_output -v 2
```

#### Tests and package layout

- There is both a module `chatbot/tests.py` and a package directory `chatbot/tests/`.
- In Python, the module `chatbot.tests` shadows the package `chatbot/tests/`, so Django will not discover tests inside `chatbot/tests/` via labels like `chatbot.tests.test_smoke`.

Current recommendations for adding tests:

- Add new tests to `chatbot/tests.py` **or** create new top‑level modules such as `chatbot/test_*.py`.
- Run them with labels like:
  ```bash
  python manage.py test chatbot.test_example -v 2
  ```

> **TODO:** Refactor the tests layout (for example, rename `chatbot/tests.py` to `chatbot/test_filters.py`) so that `chatbot/tests/` can be used as a proper package.

#### Running tests in Docker

Inside the Django app container:

```bash
docker-compose run --rm django_app python manage.py test -v 2
docker-compose run --rm django_app python manage.py test chatbot.tests.FiltersTest -v 2
```

The test database uses SQLite (in memory by default) for speed.

---

### Project structure

High‑level layout (non‑exhaustive):

```text
django-openai-chatbot/
├── chatbot/                  # Django app with chatbot views, models, templates, tests
│   ├── management/           # Custom management commands (if any)
│   ├── migrations/           # Django migrations
│   ├── templatetags/         # Custom template tags/filters (e.g., markdown_to_html)
│   ├── tests.py              # Main test module (currently shadows chatbot/tests/)
│   └── tests/                # Additional tests (not fully wired due to module name clash)
├── django_chatbot/           # Django project configuration (settings, URLs, WSGI)
├── templates/                # HTML templates
├── static/                   # Source static assets (CSS, JS, images)
├── staticfiles/              # Collected static files (built via collectstatic)
├── nginx/                    # NGINX configuration
├── certs/                    # Certificate-related directories (hooks; certs not included)
├── Dockerfile                # Django application image definition
├── docker-compose.yml        # Multi‑container stack (Django + NGINX)
├── gunicorn.conf.py          # Gunicorn configuration
├── entrypoint.sh             # Container entrypoint script
├── start_gunicorn.sh         # Helper script for running Gunicorn locally
├── manage.py                 # Django management script
├── requirements.txt          # Runtime dependencies
├── pyproject.toml            # Project metadata and dependencies
├── LICENSE                   # MIT license
└── README.md                 # This file
```

> **TODO:** Document key Django views, URL routes, and templates once the chatbot UI and API surface are finalized.

---

### Static files, Gunicorn, and NGINX

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

### HTTPS / TLS

To enable HTTPS support with NGINX you will need to:

1. Obtain TLS certificates (for example via Let’s Encrypt or another CA).
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

### Contributing

Contributions are welcome. A typical workflow is:

1. Fork this repository.
2. Create a new branch: `git checkout -b feature/my-feature`.
3. Make your changes and add tests where appropriate.
4. Run the test suite: `python manage.py test -v 2` (or the relevant subset).
5. Commit with a descriptive message: `git commit -m "Describe your change"`.
6. Push to your fork: `git push origin feature/my-feature`.
7. Open a Pull Request against the main repository.

For more details, see GitHub’s documentation on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

---

### License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2024 Alexey Bogomolov