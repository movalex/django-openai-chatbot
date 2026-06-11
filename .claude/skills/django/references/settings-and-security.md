# Django 5.2 LTS — Settings, Security & Deployment

> Verified against Django 5.2 LTS docs. Source URLs cited per section.

## 1. Settings split (base / dev / prod) with django-environ
Source: https://docs.djangoproject.com/en/5.2/topics/settings/ · https://django-environ.readthedocs.io/

Replace the single `settings.py` with a package. `DJANGO_SETTINGS_MODULE` selects the active module
at process start (defaults to `config.settings` from `manage.py`/`wsgi.py`; override per environment).

```
config/settings/__init__.py
config/settings/base.py     # shared, env-driven, no secrets inline
config/settings/dev.py      # from .base import *  (DEBUG=True, relaxed)
config/settings/prod.py     # from .base import *  (DEBUG=False, hardened)
```

Selection (set in the environment, do not hardcode in code):
```bash
# manage.py / wsgi.py default
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
# override per shell / container
export DJANGO_SETTINGS_MODULE=config.settings.dev
```

`base.py` — django-environ idioms (`env.str/bool/list/db/int`, casts + defaults):
```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(DEBUG=(bool, False))           # type + default per key
environ.Env.read_env(BASE_DIR / ".env")          # load .env (no-op if absent)

SECRET_KEY = env.str("DJANGO_SECRET_KEY")        # no default -> required, raises if unset
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR/'db.sqlite3'}")}
# env.db() parses postgres://user:pass@host:5432/name into the DATABASES dict
```

What goes where:
- **base**: `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, `STORAGES`, `DEFAULT_AUTO_FIELD`, `LOGGING`,
  anything read from env with safe defaults.
- **dev**: `DEBUG=True`, `ALLOWED_HOSTS=["localhost","127.0.0.1"]`, console email, insecure cookie
  defaults (no HTTPS locally).
- **prod**: `DEBUG=False`, explicit `ALLOWED_HOSTS`, all security toggles below on. Secrets via env only.

Never derive `SECRET_KEY` or `ALLOWED_HOSTS` from `DEBUG`. Keep hardened values in `prod.py` (or gate
in `base.py` with `if not DEBUG:`).

## 2. Security-critical settings — safe prod values (full `check --deploy` set)
Source: https://docs.djangoproject.com/en/5.2/ref/settings/ · https://docs.djangoproject.com/en/5.2/topics/security/

| Setting | Default | Safe prod value | Why |
|---|---|---|---|
| `SECRET_KEY` | `''` | large random from env | Signs sessions, CSRF, password-reset. Django refuses to start if empty. |
| `SECRET_KEY_FALLBACKS` | `[]` | `[old_key]` during rotation | Validates old signatures while rotating `SECRET_KEY`. |
| `DEBUG` | `False` | `False` | `True` leaks tracebacks, settings, SQL. |
| `ALLOWED_HOSTS` | `[]` | explicit domain list | Host-header validation. `['*']` defeats it. |
| `CSRF_TRUSTED_ORIGINS` | `[]` | `['https://example.com']` | Origins trusted for unsafe methods. **Must include scheme** (§7). |
| `SESSION_COOKIE_SECURE` | `False` | `True` | Session cookie HTTPS-only. |
| `CSRF_COOKIE_SECURE` | `False` | `True` | CSRF cookie HTTPS-only. |
| `SECURE_SSL_REDIRECT` | `False` | `True` | `SecurityMiddleware` redirects HTTP→HTTPS. |
| `SECURE_HSTS_SECONDS` | `0` | e.g. `31536000` | Sends HSTS; browser refuses plaintext for the duration. Ramp up. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | `True` (only if all subdomains HTTPS) | Adds `includeSubDomains`. Needs `SECURE_HSTS_SECONDS > 0`. |
| `SECURE_HSTS_PRELOAD` | `False` | `True` (only when committed) | Adds `preload`. Needs `SECURE_HSTS_SECONDS > 0`. See §7. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | `True` | `X-Content-Type-Options: nosniff`. |
| `SECURE_PROXY_SSL_HEADER` | `None` | `("HTTP_X_FORWARDED_PROTO", "https")` | Tells Django the request is HTTPS behind a TLS proxy. Misconfig is dangerous — §7. |
| `X_FRAME_OPTIONS` | `'DENY'` | `'DENY'` | Clickjacking protection. |

Also configured for prod (not all hard-fail in `check --deploy`): `DATABASES` (protect password,
backups), `CACHES` (prod params), `EMAIL_BACKEND` + sender, `ADMINS`/`MANAGERS`, `LOGGING`,
`MEDIA_ROOT`/`MEDIA_URL` (web server must not execute uploads).

Built-in protections (no extra config): **SQL injection** — querysets parameterize SQL (beware
`extra()`, `RawSQL()`, raw queries); **XSS** — template autoescaping (beware `mark_safe()`, `|safe`,
`{% autoescape off %}`, DB-stored HTML); **CSRF** — `CsrfViewMiddleware` (avoid `csrf_exempt`);
**clickjacking** — `XFrameOptionsMiddleware`.

## 3. SECRET_KEY handling
Source: https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key · howto/deployment/checklist/

Required-from-env (fail fast, no insecure fallback):
```python
SECRET_KEY = env.str("DJANGO_SECRET_KEY")        # no default => ImproperlyConfigured if unset
```

Rotation without invalidating live sessions/signatures:
```python
SECRET_KEY = env.str("DJANGO_SECRET_KEY")                                  # new key
SECRET_KEY_FALLBACKS = env.list("DJANGO_SECRET_KEY_FALLBACKS", default=[])  # [previous key]
```
On rotation move the old key into `SECRET_KEY_FALLBACKS`, set a fresh `SECRET_KEY`. Django signs with
the current key but validates against fallbacks, so existing sessions/signed cookies/reset tokens
survive. Drop the fallback after the relevant max-age elapses.

**Why random-per-boot is wrong** (the current repo behavior): `SECRET_KEY` keys all signing.
Regenerating it each boot invalidates every active session, CSRF token, signed cookie, and
password-reset link on restart, and breaks multi-worker deployments where each process holds a
different key. Generate once, store in env/secret manager, keep stable.

## 4. STORAGES (5.x canonical form)
Source: https://docs.djangoproject.com/en/5.2/ref/settings/#storages · howto/static-files/

Single dict for file + static storage. Exact 5.2 default:
```python
STORAGES = {
    "default":     {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```
Prod with hashed/manifested static files (cache-busting):
```python
STORAGES = {
    "default":     {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
```
Defining only one key resets the other to its default — always specify both.

**Deprecation/removal**: `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` were **deprecated in 5.0**
and **removed in 5.1** (with `get_storage_class()`). On 5.2 they no longer exist — use `STORAGES`.

Static recap (5.2): `STATIC_URL = "static/"`, `STATIC_ROOT` = collectstatic target,
`STATICFILES_DIRS` = extra source dirs, `django.contrib.staticfiles` in `INSTALLED_APPS`, then
`manage.py collectstatic`.

## 5. `manage.py check --deploy`
Source: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

```bash
# run against PRODUCTION settings
uv run python manage.py check --deploy --settings=config.settings.prod
```
Runs the `security` check tag and warns for: `DEBUG=True`; weak/empty `SECRET_KEY`;
empty/permissive `ALLOWED_HOSTS`; `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` not `True`;
`SECURE_SSL_REDIRECT` not `True`; `SECURE_HSTS_SECONDS == 0`; `SECURE_CONTENT_TYPE_NOSNIFF` off;
`X_FRAME_OPTIONS` not `DENY`. Warnings are advisory — wire it into CI for prod settings.

## 6. Changed since 4.2 (project upgrades from 4.2.2)
Verified against 5.0/5.1/5.2 release notes.

- **STORAGES is canonical** — old storage settings removed in 5.1 (see §4). Migrate before upgrading.
- **`FORMS_URLFIELD_ASSUME_HTTPS`** — transitional setting added in 5.0 (with `URLField.assume_scheme`).
  `forms.URLField` default scheme changes `"http"`→`"https"` in **Django 6.0**; set this `True` during
  the 5.x cycle to opt in early.
- **`debug()` context processor dropped from the default project template (5.2)** — only matters if
  regenerating settings from the template.
- **`SafeExceptionReporterFilter.hidden_settings`** now also masks names containing `AUTH` (5.2).
- **Password hashing hardened** (not setting renames): PBKDF2 iterations 720k→870k (5.1) →1,000,000
  (5.2); Scrypt `parallelism` 1→5 (5.1). Hashes upgrade transparently on next login.
- **`LoginRequiredMiddleware`** added (5.1) — opt-in global auth gate.
- `SECRET_KEY_FALLBACKS` and scheme-required `CSRF_TRUSTED_ORIGINS` already exist in 4.2 — adopt them.

## 7. Gotchas
Source: topics/security/ · ref/settings (CSRF_TRUSTED_ORIGINS, SECURE_PROXY_SSL_HEADER, SECURE_HSTS_PRELOAD)

- **`CSRF_TRUSTED_ORIGINS` must include the scheme.** `'example.com'` is invalid; use
  `'https://example.com'`. Wildcard: `'https://*.example.com'`. Common breakage moving off `DEBUG=True`.
- **`SECURE_PROXY_SSL_HEADER` behind nginx.** Only set `("HTTP_X_FORWARDED_PROTO", "https")` when the
  proxy *always* sets/overwrites that header and strips any client-supplied copy. Docs: *"Failure to
  do this can result in CSRF vulnerabilities, and failure to do it correctly can also be dangerous!"*
  Ensure nginx sets `proxy_set_header X-Forwarded-Proto $scheme;`.
- **HSTS preload danger.** HSTS + `INCLUDE_SUBDOMAINS` + `PRELOAD` make browsers refuse plaintext for
  the full duration and (with preload) hard-code the domain into browser source. If HTTPS later
  breaks on any subdomain, those clients cannot reach the site until the TTL expires. Roll out
  incrementally (300 → 86400 → 31536000) and only enable subdomains/preload once every subdomain is
  permanently HTTPS.
- Both HSTS directive settings are no-ops unless `SECURE_HSTS_SECONDS > 0`.
- `ALLOWED_HOSTS` validation only fires through `HttpRequest.get_host()`; reading
  `request.META['HTTP_HOST']` directly bypasses it.
