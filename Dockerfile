# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Environment:
# - unbuffered output, no .pyc files
# - put the uv-managed virtualenv outside /app so a dev bind-mount of the
#   project directory cannot shadow it, and put its bin dir on PATH so bare
#   `python` / `gunicorn` resolve to it.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# uv: single dependency manager, copied from its official image (no curl needed).
COPY --from=ghcr.io/astral-sh/uv:0.10.11 /uv /uvx /bin/

WORKDIR /app

# Install dependencies first so this layer is cached until the lock changes.
# --no-dev: skip the dev dependency group (tests/lint) in the runtime image.
# --no-install-project: the app runs from copied source, not as a built package.
COPY uv.lock pyproject.toml /app/
RUN uv sync --frozen --no-install-project --no-dev

# Copy the application source.
COPY . /app

# Entrypoint: collect static, migrate, then exec the container command.
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
