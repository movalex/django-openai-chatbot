# Django 4.2.2 → 5.2 LTS Upgrade

> All facts verified against `docs.djangoproject.com/en/5.2/` release notes, the install FAQ matrix,
> and the upgrade howto. Django 4.2 security support ended **April 2026**; 5.2 is the next LTS
> (security updates ~3 years, through April 2028). This repo runs Python 3.13.

## 1. Supported Python versions
Source: https://docs.djangoproject.com/en/5.2/faq/install/

| Django | Python | Min |
|--------|--------|-----|
| 5.0 | 3.10, 3.11, 3.12 | 3.10 |
| 5.1 | 3.10–3.12, **3.13** (added 5.1.3) | 3.10 |
| 5.2 (LTS) | 3.10–3.13, 3.14 (added 5.2.8) | 3.10 |

**Python 3.13 is supported on Django 5.2** (FAQ matrix + 5.2 release notes). This repo's interpreter
needs no change. Note 5.0 does NOT support 3.13 — a reason to jump straight to 5.2, not pin an
intermediate 5.0.

## 2. Upgrade procedure (uv-adapted)
Source: https://docs.djangoproject.com/en/5.2/howto/upgrade-version/ — the official deprecation flag
is **`-Wa`** (all warnings), not `-Wd`.

1. **Read the release notes** for 5.0, 5.1, 5.2 — focus on *Backwards incompatible changes* and the
   deprecation timeline.
2. **Resolve deprecation warnings on the CURRENT version first** (still on 4.2.2):
   ```powershell
   $env:PYTHONWARNINGS="always"; uv run pytest      # PowerShell 7
   ```
   ```bash
   PYTHONWARNINGS=always uv run pytest               # POSIX
   ```
   Fix all `DeprecationWarning`s before bumping. Optionally make them fatal with pytest
   `filterwarnings = error`.
3. **Bump the dependency:**
   ```bash
   uv add 'django>=5.2,<5.3'
   uv lock && uv sync
   ```
   Replace the `django==4.2.2` pin. Re-check `django-environ`, `django-stubs`, `pymdown-extensions`
   for 5.2 compatibility.
4. **Re-run the suite with warnings on** under 5.2; fix failures and new warnings.
5. **Migration drift check:** `uv run python manage.py makemigrations --check --dry-run`.
6. **System checks:** `uv run python manage.py check` and `check --deploy`.
7. **Deploy** — the howto warns to **clear caches** after upgrade (pickle compatibility).

## 3. Backwards-incompatible changes likely to bite this app

**5.0** (https://docs.djangoproject.com/en/5.2/releases/5.0/):
- **`USE_TZ` default changed `False` → `True`.** The biggest one. If `settings.py` doesn't set
  `USE_TZ` explicitly, datetime handling becomes timezone-aware after upgrade (affects the
  `Chat`/`ChatRoom` `created` timestamps). Set it explicitly to lock behavior, or audit naive-datetime
  usage.
- **Default form/formset rendering changed to div-based** (table-based default templates removed).
- `BadRequest` raised for non-UTF-8 `application/x-www-form-urlencoded` bodies.
- Minimums: SQLite 3.27.0, asgiref 3.7.0; integer fields validated as 64-bit on SQLite.

**5.1** (https://docs.djangoproject.com/en/5.2/releases/5.1/):
- **`DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` settings REMOVED** — `STORAGES` is canonical.
  Migrate any usage to the `STORAGES` dict (`"default"` + `"staticfiles"`). `get_storage_class()`
  also removed.
- Minimum SQLite raised to 3.31.0; asgiref 3.8.1.
- `index_together` removed (use `Meta.indexes`).

**5.2** (https://docs.djangoproject.com/en/5.2/releases/5.2/):
- **PostgreSQL 13 dropped** (5.2 needs PG 14+) — relevant to the planned Postgres move.
- MySQL connections default to `utf8mb4`.
- `debug()` context processor removed from the default project template.
- Single-arg aggregates (`Avg`, `Count`, `Max`, `Min`, `StdDev`, `Sum`, `Variance`) raise `TypeError`
  on wrong arg count.
- `UniqueConstraint.violation_error_code`/`_message` now always applied.

## 4. Notable removals an app might still use
- **5.0:** `USE_L10N`; `USE_DEPRECATED_PYTZ` and all **pytz** support (`django.utils.timezone.utc`
  alias); `is_dst` arg on `make_aware()`/`Trunc*`; `GET` support in `LogoutView`; `CSRF_COOKIE_MASKED`;
  `PickleSerializer`; `django.utils.baseconv`, `django.utils.datetime_safe`.
- **5.1:** `DEFAULT_FILE_STORAGE`/`STATICFILES_STORAGE` + `get_storage_class()`; `Meta.index_together`;
  `length_is` template filter; `make_random_password()`; `SHA1`/`UnsaltedSHA1`/`UnsaltedMD5` hashers;
  postgres `CICharField`/`CIEmailField`/`CITextField`; `assertFormsetError`, `assertQuerysetEqual`.
- **5.2:** no "Features removed" section — removals in this jump come from 5.0 and 5.1.

## 5. What to check in THIS app
- **`config/settings.py` → `USE_TZ`**: set it explicitly. If absent today (4.2 default `False`), the
  5.0 flip to `True` silently changes datetime behavior. Decide and pin.
- **`STORAGES`**: grep settings for `DEFAULT_FILE_STORAGE` / `STATICFILES_STORAGE`; if present, port to
  a `STORAGES` dict (static is served by NGINX from `staticfiles/`, so the `"staticfiles"` backend
  matters for `collectstatic`).
- **Forms**: any `as_table` rendering / custom form templates change to div-based (5.0) — the
  login/register templates are the likely spots.
- **`CSRF_TRUSTED_ORIGINS`**: already scheme-prefixed (`['http://localhost:8888']`) — correct format;
  just confirm production entries include the scheme.
- **`DEFAULT_AUTO_FIELD`**: confirm it's set (e.g. `BigAutoField`), or `manage.py check` warns
  (`models.W042`).
- **pytest suite**: run with `PYTHONWARNINGS=always` on 4.2 first, then on 5.2. Watch for removed test
  helpers and confirm `@pytest.mark.django_db` usage.
- **SQLite version**: 5.2 needs **SQLite ≥ 3.31.0** — verify the runtime/Docker base.
- **`Model.save()` positional args**: 5.1 deprecated positional args to `save()`/`asave()` — check
  `models.py`/views for `obj.save(force_insert, ...)` positional usage.

## 6. New features worth adopting (post-upgrade)
- **`SECRET_KEY_FALLBACKS`** (5.0) — rotate `SECRET_KEY` without invalidating sessions (see
  settings-and-security).
- **`db_default`** (5.0) — database-level column defaults; **`GeneratedField`** (5.0) — DB-computed
  columns.
- **`LoginRequiredMiddleware`** (5.1) — global auth gate; exempt with `@login_not_required`. Fits the
  "all chat views require login" pattern.
- **`{% querystring %}` template tag** (5.1); PostgreSQL connection pools via `OPTIONS["pool"]` (5.1).
- **`CompositePrimaryKey`** (5.2) — multi-column PKs (could model the `{user_id}-{chat_room_id}`
  identity natively).
- **Async ORM / auth methods** (5.1+5.2) — `acreate`, `aget_or_create`, `aauthenticate`, async session
  store — relevant if the send path moves async.
- **`reverse(query=…, fragment=…)`, `redirect(preserve_request=…)`, `HttpResponse.text`** (5.2) —
  ergonomics for the AJAX/redirect-heavy views.
