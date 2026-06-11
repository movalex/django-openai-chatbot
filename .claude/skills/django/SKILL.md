---
name: django
description: >-
  Version-accurate Django 5.2 LTS reference for this repository — models, migrations, settings,
  security, the ORM, views/URLs/forms, CSRF, auth, testing (pytest-django + factory_boy), SSE
  streaming, PostgreSQL features, and the 4.2->5.2 upgrade. Use this skill whenever working on ANY
  Django code or config in this project: writing or reviewing models / fields / Meta / migrations,
  editing settings or hardening security, composing ORM queries or aggregations, adding
  views / URLs / forms, wiring CSRF or auth decorators, writing or reviewing Django tests, building
  streaming responses, adding Postgres search, or planning the Django version upgrade — even when
  the user does not say "Django" explicitly. Its job is to keep guidance and code grounded in the
  ACTUAL Django 5.2 APIs (no invented methods, settings, or defaults) and aligned with this repo's
  conventions (uv, pytest-django, ruff/mypy, settings split). Consult it before asserting any Django
  API, deprecation, default value, or version behavior.
---

# Django 5.2 LTS reference (this repository)

This skill exists for one reason: **Django facts in this repo must be correct and current, not
recalled from memory.** Training data drifts, APIs are renamed, defaults flip between versions, and
this project is mid-upgrade. The `references/` files were distilled from the live
`docs.djangoproject.com/en/5.2/` pages, so treat them as the source of truth over recollection.

## Target version

This repository targets **Django 5.2 LTS** (security support through April 2028). It is being
upgraded from the pinned **4.2.2** (4.2 reached end-of-life April 2026). Runtime is **Python 3.13**,
which 5.2 supports. Ground every API, default, and deprecation claim to 5.2 — not 4.2, not 6.0.

When something is NOT covered by a reference file, do not guess. Verify against:
- the installed source — `.venv/Lib/site-packages/django/` (e.g. `forms/fields.py`, `db/models/`),
- or the docs — `https://docs.djangoproject.com/en/5.2/<path>`.

Currently the venv holds 4.2.2; after the upgrade the installed source becomes authoritative for
5.2. Until then, prefer the 5.2 docs URL for anything version-sensitive.

## Project conventions (how Django work is done here)

- **Python via uv, always**: `uv run python manage.py …`, `uv run pytest`, `uv run ruff …`,
  `uv run mypy chatbot`. Never bare `python`/`pip`/`pytest`.
- **Tests**: pytest + pytest-django + factory_boy, in the `chatbot/tests/` package. DB-touching
  tests use `@pytest.mark.django_db` (or the `db` fixture). OpenAI is mocked at a wrapper seam
  (`@patch("chatbot.views.ask_openai")`) — never hit the live API.
- **Tooling gate**: `uv run ruff check`, `uv run mypy chatbot`, `uv run pytest` all green before a
  commit. ruff selects E/W/F/I/UP/B/DJ.
- **Settings**: moving to a `config/settings/{base,dev,prod}.py` split; secrets and environment
  toggles via `django-environ` reading `.env`. Security hardening keys off environment, never
  hardcoded.
- **Database**: SQLite today, PostgreSQL planned for dev + prod (so FTS/trigram search is testable
  in CI).
- **Commits**: objective voice, imperative subject, body explains *why*. No AI attribution.

## Which reference file to read

Read the one file that matches the task — they are loaded on demand, so pull only what is relevant.

| Task | Reference |
|------|-----------|
| Models, fields, `Meta`, constraints, indexes, relationships, migrations, data backfills | `references/models-and-migrations.md` |
| `settings.py` / settings split, `SECRET_KEY`, `ALLOWED_HOSTS`, `SECURE_*`, cookies, HSTS, `STORAGES`, `check --deploy`, security topics | `references/settings-and-security.md` |
| QuerySets, `filter`/`annotate`/`aggregate`, `F`/`Q`, `select_related`/`prefetch_related`, conditional expressions, `Trunc*` reports, transactions, `select_for_update`, async ORM | `references/orm-and-queries.md` |
| Function views, URLconf/`path()`, `HttpResponse`/`JsonResponse`/`StreamingHttpResponse`, forms/ModelForm, CSRF, `@login_required`/`@require_POST`, the IDOR ownership pattern | `references/views-urls-forms.md` |
| pytest-django markers/fixtures, factory_boy, mocking external APIs, response assertions, timestamp-ordering pitfalls | `references/testing.md` |
| `django.contrib.postgres`: full-text search (`SearchVector`/`SearchRank`/`SearchVectorField`), `GinIndex`, trigram/`pg_trgm`, `ArrayField`/`HStoreField`, extension migrations | `references/postgres.md` |
| Upgrading 4.2.2 -> 5.2: supported Python, the procedure, backwards-incompatible changes, removals, what to check in this app, new features worth adopting | `references/upgrading-4.2-to-5.2.md` |

## Cross-cutting must-knows (the easy things to get wrong)

These are the highest-value 5.2 facts that bite small apps. Each has full detail in its file.

- **`USE_TZ` default flipped `False` -> `True` in 5.0.** If the current `settings.py` does not set it
  explicitly, datetime behavior changes silently on upgrade. Set it explicitly. (upgrading)
- **`DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` were removed in 5.1** — the single `STORAGES`
  dict is canonical (with `"default"` and `"staticfiles"` keys). (settings-and-security, upgrading)
- **`SECRET_KEY` must come from the environment and be stable.** A random key per boot invalidates
  every session, CSRF token, and signed link on restart. Use `SECRET_KEY_FALLBACKS` (5.0+) to
  rotate without breakage. (settings-and-security)
- **IDOR**: never `get_object_or_404(Model, pk=pk)` for user-owned data. Add `@login_required` and
  scope the lookup with `user=request.user` so a non-owner gets a 404. (views-urls-forms)
- **`CSRF_TRUSTED_ORIGINS` entries must include the scheme** (`https://example.com`, not
  `example.com`). Common breakage when leaving `DEBUG=True`. (settings-and-security, views-urls-forms)
- **`auto_now_add` ordering ties**: rows created in the same tick can share a timestamp, so
  `ordering=["created"]` is non-deterministic — add a tiebreaker like `["created", "id"]`. This is
  also the cause of flaky ordering tests. (models-and-migrations, testing)
- **SSE/streaming + nginx**: `StreamingHttpResponse` needs `X-Accel-Buffering: no` on the response
  and `proxy_buffering off;` on the nginx location, or chunks are buffered and the stream stalls.
  (views-urls-forms)
- **`.update()` and `bulk_create()` bypass `save()` and signals** (and `auto_now`). Use `F()` for
  atomic counter increments. (orm-and-queries)
- **`db_index=True` is fully supported** for single-column indexes; it is NOT deprecated.
  `index_together` is the deprecated/removed one — use `Meta.indexes` for composite, conditional, or
  covering indexes. (models-and-migrations)

## Reviewing the operator's code

This is a learning / portfolio repo where the operator writes the production code. When reviewing a
diff, check it against the relevant reference file: flag invented or version-wrong APIs, missing
ownership/auth checks, `save()`-bypassing writes that skip signals, settings that won't pass
`check --deploy`, and 4.2-isms that break on 5.2. Explain the *why* and cite the doc, rather than
just rewriting.
