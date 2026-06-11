# Django Testing — pytest-django + factory_boy (Django 5.2)

> This project's tests live in `chatbot/tests/` as a pytest package (conftest fixtures + factory_boy
> factories). Run with `uv run pytest`. OpenAI is mocked at a wrapper seam — never hit the live API.

## 1. pytest-django setup
Source: https://pytest-django.readthedocs.io/en/latest/

`DJANGO_SETTINGS_MODULE` is configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
addopts = "--reuse-db"
```
- **DB access is blocked by default** — tests fail if they touch the DB without opting in. This keeps
  non-DB tests fast and makes DB dependence explicit.
- Opt in with **`@pytest.mark.django_db`** (function or class) or by requesting the `db` /
  `transactional_db` fixture.
- Marker args: `transaction=True` (real transactions, flush between tests),
  `reset_sequences=True` (implies `transaction`), `databases=[...]`, `serialized_rollback=True`.
- DB speed flags: `--reuse-db` (keep test DB between runs), `--create-db` (force recreate after schema
  changes), `--no-migrations` (build schema from model inspection, skip migrations).

## 2. Key fixtures
Source: https://pytest-django.readthedocs.io/en/latest/helpers.html

- **`db`** — transactional DB access (rollback per test). Standard fixture-based opt-in.
- **`transactional_db`** — real transaction support; truncates/flushes between tests (slower). Needed
  to test `transaction.on_commit` or cross-thread visibility (`live_server`).
- **`client`** — `django.test.Client` for HTTP requests.
- **`async_client`** — `django.test.AsyncClient`.
- **`rf`** — `RequestFactory` for building request objects passed directly to views.
- **`django_user_model`** — the active User model (respects `AUTH_USER_MODEL`). Use instead of
  importing `User`.
- **`settings`** — settings handle; mutations auto-revert after the test.
- **`admin_client`** — `Client` logged in as a superuser. **`admin_user`** — a superuser instance.
- **`live_server`**, **`mailoutbox`** — live background server / captured email outbox.

## 3. factory_boy DjangoModelFactory
Source: https://factoryboy.readthedocs.io/en/stable/orms.html

```python
import factory
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = "auth.User"                    # model ref or "app.Model" string
        django_get_or_create = ("username",)   # get-or-create on these fields
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")

class ChatRoomFactory(DjangoModelFactory):
    class Meta:
        model = "chatbot.ChatRoom"
    user = factory.SubFactory(UserFactory)     # nested object, same strategy
    name = factory.Sequence(lambda n: f"Room {n}")

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.members.add(*extracted)
```
- **`Meta.model`** — class or `"app.Model"` string. **`Meta.django_get_or_create`** — get-or-create on
  the listed fields (note: a fetched row is NOT updated with new factory values).
  **`Meta.skip_postgeneration_save`** avoids a duplicate save when a post-gen hook returns a value.
- **`factory.Sequence(lambda n: ...)`** — autoincrementing values (uniqueness).
  **`factory.SubFactory(Other)`** — nested object. **`factory.LazyAttribute(lambda o: ...)`** —
  computed from the object. Also `factory.Faker("name")`, `factory.SelfAttribute("...")`.
- **`@factory.post_generation`** — `(self, create, extracted, **kwargs)`, for M2M/related setup.
- **`build()`** — `__init__` only, NOT saved (no DB). **`create()`** — saved. Batch:
  `build_batch(n)`, `create_batch(n)`.

## 4. Patterns
**Mock external APIs at the wrapper seam** — patch the wrapper the view calls, never SDK internals:
```python
from unittest.mock import patch

@patch("chatbot.views.ask_openai")
def test_send_message(mock_ask, client, django_user_model, db):
    mock_ask.return_value = "mocked reply"
    ...

def test_x(monkeypatch):                       # fixture-style
    monkeypatch.setattr("chatbot.views.ask_openai", lambda *a, **k: "reply")
```
**Parametrize:**
```python
@pytest.mark.parametrize("model_id,expected", [("gpt-4o", 200), ("bad", 400)])
def test_models(model_id, expected, client): ...
```
**Assert on responses** (https://docs.djangoproject.com/en/5.2/topics/testing/tools/):
- `assert response.status_code == 200`
- `assertRedirects(response, "/login/", status_code=302, target_status_code=200)`
- `assertContains(response, text, status_code=200, html=False)` / `assertNotContains`
- `assertTemplateUsed(response, "chatbot.html")`
- `response.json()`, `response.context["..."]`, `response.redirect_chain` (with `follow=True`).
- Client auth: `client.force_login(user)` (skips the backend) or
  `client.login(username=..., password=...)`.

**Avoid `auto_now_add` ordering ties:** rows created in one test can share an identical `created`
timestamp, making `order_by("created")` nondeterministic. Inject explicit, spaced timestamps (set the
field then `obj.save(update_fields=["created"])`, since `auto_now_add` ignores assigned values on
insert) or order by a tiebreaker like `pk`. This is the usual cause of "flaky" ordering tests here.

## 5. Gotchas
- **Forgetting `@pytest.mark.django_db`** (or the `db` fixture) → `Failed: Database access not allowed`.
- **Factory uniqueness collisions** — sequences are per-factory, reset per process; hardcoded unique
  fields cause `IntegrityError`. Use `Sequence`/`LazyAttribute` for unique columns.
- **Test isolation** — `db` rolls back per test (fast, but `on_commit` hooks don't fire);
  `transactional_db` commits/flushes (needed for `on_commit`/cross-thread). Mixing both forces extra
  DB rebuilds.
