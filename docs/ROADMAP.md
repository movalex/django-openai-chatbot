# django-openai-chatbot — Refactor + Feature Roadmap

## Context

The app is a working Django 4.2.2 + OpenAI chatbot, but it carries accumulated debt that blocks the requested feature set:

- **Duplicated conversation storage** — every turn is stored twice: as a `Chat` row (a `message`+`response` *pair*) and inside `ChatSession.context` (a JSON blob of the whole history). This duplication is the root reason edit/regenerate, per-message token tracking, streaming persistence, and memory notes are currently impossible.
- **Module-global OpenAI key** — `views.py:21-22` sets `openai.api_key` at import time, which blocks per-user API keys.
- **Security holes** — `save_chat_name` (`views.py:221-236`) has `@require_POST` but **no `login_required` and no ownership check**: any caller can rename any room by UUID (IDOR). `register` uses a bare `except:` (`views.py:312`). `settings.py` has `ALLOWED_HOSTS=["*"]`, both `*_COOKIE_SECURE=False`, and `SECRET_KEY` falls back to a *random key on every boot* (`settings.py:15`), silently invalidating all sessions on restart.
- **Model bug** — `ChatRoom.name` is declared twice (`models.py:7` and `:9`); no `Meta` ordering or indexes anywhere.
- **Invalid model catalog** — `GPT_MODELS` (`views.py:27-37`) contains non-existent ids (`gpt-o1`) and maps o3 → o1.
- **Markdown kludge** — server-side `python-markdown` is run, then `inline_code_formatting` (`custom_filters.py:11-22`) runs `markdown()` a *second* time over already-rendered HTML via BeautifulSoup. No LaTeX. `mark_safe` on model content is an XSS surface.
- **No tooling** — no `pyproject.toml`, no ruff/mypy/pre-commit, ~1 test, `entrypoint.sh` is malformed (missing `fi`, migrations only run when the DB is absent).

The goal: harden the foundation, normalize the data model, move to PostgreSQL **without losing chat history**, then layer on the requested features in dependency order — each phase a self-contained, separately-committable change with its own pytest coverage.

## Status update — work merged to `develop` (v0.2.0 → v0.2.1)

A tooling/test pass landed since this plan was first drafted. It completes much of **P0**, but ships its own issues that must be cleaned up before building on it:

**What landed (good):** `pyproject.toml` + `uv.lock` with deps pinned (`openai>=2.8.0`); pytest + pytest-django + pytest-cov + pytest-mock + factory-boy; a real test package `chatbot/tests/` (conftest fixtures, factories, ~1400 lines across `test_models.py`, `test_views.py`, `test_templatetags.py`, `test_smoke.py`); `.python-version` = 3.12; a repo `CLAUDE.md`; `CHANGELOG.md`; rewritten `README.md` + `TESTING.md`.

**Issues introduced (must fix — see revised P0):**
1. **Test-layout import collision.** `chatbot/tests.py` (old, single `FiltersTest`) AND `chatbot/tests/` (new package, has `__init__.py`) both exist → the name `chatbot.tests` is ambiguous. `python manage.py test` (the command the new `CLAUDE.md` tells contributors to use) imports the old module and **does not discover the new suite**; pytest collects by path but the collision is fragile. The merged `CLAUDE.md` documents this as a "known issue" and advises putting tests in `tests.py` — which contradicts where the suite actually lives. Fix: delete `chatbot/tests.py`, keep only the package.
2. **Two competing pytest configs.** `pytest.ini` *and* `[tool.pytest.ini_options]` in `pyproject.toml`. `pytest.ini` wins, so the coverage `addopts`/config in `pyproject.toml` is dead. Consolidate to one (keep pyproject).
3. **No ruff / mypy / pre-commit** anywhere — that part of P0 is still entirely undone.
4. **Two dependency sources** now diverge: `requirements.txt` (unpinned `openai`, dev deps appended) vs `pyproject.toml`/`uv.lock` (pinned). Make pyproject+lock canonical; generate or drop `requirements.txt`.
5. **Known bugs documented but NOT fixed**, and now papered over by passing tests: `ChatRoom.name` double-declaration (`models.py:7,9`) still present; `save_chat_name` IDOR still present and the new `TestSaveChatName` only covers success + 404 (no non-owner test → false confidence); `trim_chat_context_if_needed` (`views.py:186-188`) still reassigns a local it never persists (dead code); `register` bare `except:` still there. `test_special_characters_escaping` (`test_templatetags.py:110`) *asserts XSS passes through* as accepted behavior.
6. **`CLAUDE.md` is authoritative but already partly stale** (documents SQLite, the broken test layout, the unfixed bugs). It must be updated as phases land.

**Net effect on sequencing:** P0 shrinks to a cleanup phase. More importantly, the merged suite is tightly coupled to the schema this plan replaces (`is_hidden`, `Chat` message/response pairs, `ChatSession` JSON) — so P2/P5/P9/P10 must **rewrite existing tests + factories + fixtures**, not merely add new ones (detailed in those phases). The login/logout/room-CRUD/ownership tests are a reusable safety net for the refactors.

## Confirmed decisions

1. **Data safety first.** Existing chat history must be preserved through the SQLite → Postgres move and the schema redesign. Only *chats* matter (rooms + their message/response history attached to users); transient state (`ChatSession` JSON, last-opened pointers) is discarded.
2. **Streaming = SSE on sync workers.** `StreamingHttpResponse` + Server-Sent Events; keep gunicorn (switch to `gthread` workers) + nginx (`proxy_buffering off` on the stream route). No WebSockets/Channels/Redis, no ASGI migration.
3. **PostgreSQL for both dev and prod.** Operator has Postgres locally; full parity so FTS/search is testable in dev + CI.
4. **First feature cluster after foundation: User control** — DB-backed settings, profile page, real dark/light theme, per-user API keys + tiers.

## Cross-cutting conventions

- **Python**: `uv run <cmd>` for everything (`uv run pytest`, `uv run ruff`, `uv run manage.py ...`). Deps already migrated to `pyproject.toml` + `uv.lock` (`openai>=2.8.0`, supports `stream=True`, `stream_options={"include_usage": True}`, `response.usage`); `.python-version` = 3.12 but `requires-python = ">=3.9.13"` — keep code 3.9-compatible or bump the floor deliberately.
- **Testing**: `pytest` + `pytest-django` + `factory_boy`, already set up in `chatbot/tests/` (conftest fixtures + factories exist — reuse and extend them). Every phase ships tests there. DB-touching tests use `@pytest.mark.django_db`. The merged suite mocks OpenAI via `@patch("chatbot.views.ask_openai")` — keep that seam (a thin monkeypatchable client wrapper) so no live API is hit. **Schema-changing phases (P2/P5/P9/P10) must update the existing fixtures/factories/tests, not just add new ones** — they currently hard-code `is_hidden`, `Chat` pairs, `ChatSession`, and the JSON-context POST contract.
- **Commits**: one phase = one commit, imperative subject, body explains *why*. No AI attribution. Run `uv run ruff` + `uv run pytest` green before each commit.
- **Settings split**: introduce `django_chatbot/settings/{base,dev,prod}.py` in Phase 1 so security toggles key off environment instead of being hardcoded.

---

## Phase roadmap

Legend: **[MIG]** = schema migration, **[DATA]** = touches existing chat data (extra care), **[INFRA]** = deployment/config change.

### Foundation (forced first — most features depend on these)

**P0 — Tooling cleanup (most already merged in v0.2.x; finish the rest).**
Goal: resolve the merged-work issues so the foundation is sound before building on it. Concretely:
- Delete `chatbot/tests.py`; keep only the `chatbot/tests/` package (fold its lone markdown assertion into `test_templatetags.py`, which already supersedes it). Verify `uv run pytest` collects the full suite with no import error.
- Delete `pytest.ini`; keep the single `[tool.pytest.ini_options]` block in `pyproject.toml` (re-enables the dead coverage config).
- Add ruff + mypy config to `pyproject.toml` and a `.pre-commit-config.yaml`; get `uv run ruff check` and `uv run mypy chatbot` green (expect to `# type: ignore`/baseline a few spots, not a full typing pass yet).
- Make `pyproject.toml` + `uv.lock` the canonical dependency source; pin `requirements.txt` to match (Dockerfile still installs from it) so the two stop diverging — full switch to uv in the image is deferred to the Postgres/Docker phase.
- Update `CLAUDE.md`: correct the test-running guidance to pytest + the package layout, and remove the now-false "put tests in tests.py" advice.
Files: `pyproject.toml`, `.pre-commit-config.yaml` (new), `chatbot/tests/`, delete `pytest.ini` + `chatbot/tests.py`, `requirements.txt`, `CLAUDE.md`.
Test: `uv run pytest` discovers and passes the existing suite; `ruff`/`mypy` clean; CI runs all three.

**P1 — Security hardening (settings). [INFRA]**
Goal: `SECRET_KEY` required from env (fail loud, remove random fallback at `settings.py:15`); `ALLOWED_HOSTS` from env; `SESSION/CSRF_COOKIE_SECURE`, HSTS, `SECURE_*` behind prod flag; split base/dev/prod settings.
Files: `django_chatbot/settings/`, `.env.template`.
Test: `manage.py check --deploy` clean in prod mode; settings-load unit tests.

**P2 — View bug + IDOR fixes (no schema).**
Goal: add `@login_required` + `user=request.user` filter to `save_chat_name`; remove `print()` (`views.py:224,227`); replace bare `except:` in `register`; fix `ChatRoom.name` double-declaration (`models.py:7/9`); add `Meta.ordering` + index on `(user, is_hidden, -created_at)`; fix `trim_chat_context_if_needed` dead-reassignment (`views.py:186-188`); fix malformed `entrypoint.sh`.
Note: **keep the field name `is_hidden`** (drop the earlier `is_archived` rename idea) — the merged suite + factories + fixtures reference `is_hidden` in ~10 places and the rename is pure cosmetics. If "archived" terminology is wanted in the UI/API, expose an `is_archived` `@property` alias instead of migrating the column.
Files: `chatbot/views.py`, `chatbot/models.py` (+ tiny migration for Meta/index), `entrypoint.sh`.
Test: **add** the missing non-owner test — `TestSaveChatName` currently only covers success + 404, so assert a non-owner gets 404 (closing the IDOR); owner still succeeds; register error path returns the template; existing tests stay green.

**P3 — PostgreSQL migration, chat history preserved. [INFRA][DATA]**
Goal: move SQLite → Postgres for dev + prod with **zero chat loss**, keeping the *current* schema first (transform happens in P5).
Steps:
1. Copy `db.sqlite3` to `backup/` (file-level safety net).
2. Durable export: `uv run manage.py dumpdata auth.User chatbot.ChatRoom chatbot.Chat --indent 2 -o backup/chats_export.json` (only users, rooms, chat history — skip `ChatSession`).
3. Add `psycopg[binary]` + `dj-database-url`; `DATABASES` from `DATABASE_URL` env; add `django.contrib.postgres` to `INSTALLED_APPS`; add `db` service to `docker-compose.yml`; fix `entrypoint.sh` migrate logic.
4. Fresh Postgres → run existing migrations (recreates old schema) → `uv run manage.py loaddata backup/chats_export.json`.
5. Verify parity (row counts of User/ChatRoom/Chat match SQLite).
Files: `django_chatbot/settings/base.py`, `docker-compose.yml`, `entrypoint.sh`, `pyproject.toml`.
Test: a `verify_import` management command + pytest comparing pre/post counts; CI spins Postgres and runs the suite.

**P4 — Model catalog + per-request OpenAI client. [MIG]**
Goal: replace hardcoded `GPT_MODELS` with a `ModelCatalog` model (`model_id`, `display_name`, `input_price_per_1k`, `output_price_per_1k`, `is_enabled`, `supports_streaming`); seed valid ids + prices via data migration; move `openai.api_key` module-global to a per-request `OpenAI(api_key=...)` client wrapper (reuse in `ask_openai`, `views.py:49-56`). Resolve the key: per-user (P7) → platform `OPENAI_API_KEY` fallback.
Files: `chatbot/models.py`, `chatbot/openai_client.py` (new), `chatbot/views.py`, `chatbot/admin.py`, migration.
Test: model-list endpoint returns only enabled models; invalid legacy ids gone; client picks correct key.

**P5 — Normalized `Message` model + transform from `Chat`. [MIG][DATA]**
Goal: introduce one normalized `Message` model and migrate existing chat history into it; retire `ChatSession`.
`Message` fields: `chat_room` FK (`related_name="messages"`), `role` (user/assistant/system), `content` TextField, `sequence` PositiveInteger (unique per room), `model`, `prompt_tokens`/`completion_tokens` (null), `cost_usd` Decimal(10,6) null, `created_at`, `is_active` bool (edit/regenerate soft-truncate), `edited_from` self-FK null. `Meta`: `ordering=["sequence"]`, `UniqueConstraint(chat_room, sequence)`, index `(chat_room, is_active, sequence)`.
`ChatRoom` additions: keep `is_hidden`; add `updated_at` (auto_now), `title_is_auto` bool, `memory_note` + `memory_note_enabled`, `summary` + `summary_through_seq`, `message_count` (denormalized), `total_prompt_tokens`/`total_completion_tokens`.
**Transform (data-safe):** an idempotent `backfill_messages` management command (skips rooms that already have messages, so it's re-runnable) converts each `Chat` row, ordered by `created_at` within a room, into two `Message` rows — user (`sequence=2k`) and assistant (`sequence=2k+1`, `model="legacy"`). The transform lives in a **command, not a `RunPython`**, so it is pytest-testable and re-runnable; `backup/chats_export.json` is the rollback net. Keep the `Chat` table until verified, drop it in a follow-up migration. Rewrite read/write paths (`views.py:112-205`) and the template loop (`chatbot.html:84-99`) to use `Message`; context is reconstructed by querying `Message` ordered by `sequence`, not from a JSON blob.
Files: `chatbot/models.py`, `chatbot/management/commands/backfill_messages.py` (new), `chatbot/views.py`, `templates/chatbot.html`, migrations.
Test: round-trip (send → persist → reload reconstructs ordered context); backfill maps N `Chat` rows → 2N ordered `Message` rows and is idempotent on second run. **Rewrite the coupled tests**: `test_models.py::TestChatSessionModel` (gone) + `TestChatModel` (→ `Message`), `test_views.py::TestChatContext` (no more `ChatSession.context`) + the POST-context assertions, and the `chat_session`/`chat_message` conftest fixtures + `ChatSessionFactory`/`ChatFactory`.

**P6 — Settings infrastructure (global / user / room + resolver). [MIG]**
Goal: an abstract `BasePreferences` (chat_model, summarization_model, temperature, max_tokens, max_history_count, font_size, theme, summarize_threshold_tokens, send_summary_each_request — all nullable) subclassed by `GlobalSettings` (singleton, all-non-null defaults: chat_model `gpt-4.1-mini`, summarization_model `gpt-4o-mini`, max_history_count 10), `UserSettings` (OneToOne user), `ChatRoomPreferences` (OneToOne room). `resolve(room, field)` returns first non-null up the chain **room → user → global**; null = inherit. Cache `GlobalSettings`, invalidate on save.
Files: `chatbot/models.py`, `chatbot/preferences.py` (new resolver), `chatbot/admin.py`, migration.
Test: resolver precedence room>user>global; null inherits; singleton enforced.

### Cluster 1 — User control (chosen first)

**P7 — Encrypted per-user API keys + user tiers. [MIG]**
Goal: `EncryptedTextField` (Fernet via `cryptography`, key from `settings.FIELD_ENCRYPTION_KEY` env, distinct from `SECRET_KEY`) for `UserSettings.api_key`; `UserTier` model (`name`, `is_admin`, `allowed_models` JSON, `can_use_own_api_key`, `monthly_token_quota` null); extend `UserProfile` with `tier`, `avatar` (ImageField), `interest_profile` text (populated in P15). `get_available_models(user)` intersects `ModelCatalog.is_enabled` with the tier's `allowed_models` (admin = all). Key never returned to client — expose masked `sk-…last4` + set/clear only; gated by `can_use_own_api_key`.
Files: `chatbot/fields.py` (new), `chatbot/models.py`, `chatbot/preferences.py`, `settings/base.py`, migration.
Test: key round-trips but raw DB value ≠ plaintext; tier gates model list; non-permitted tier can't set a key.

**P8 — Settings UI + profile page + real dark/light theme.**
Goal: build out the right-sidebar offcanvas (`chatbot.html:60-76` currently only a model `<select>`) into the full per-user/per-room settings panel (model, temperature, max tokens, max history count, font size, theme, masked API key, export/import chats JSON, summarization toggles); add a profile page (username, email, password, avatar, preferred chat + summarization models, max history cutout); implement **real dark/light theme** by undoing the forced-dark in `color-modes.js:26` and the hardcoded `data-bs-theme="dark"` in `base.html:3`, persisting `theme` as a resolved user setting and applying it to sidebars, main chat, and chatrooms via CSS variables (`variables.css`). Chat export/import = JSON round-trip endpoints.
Files: `templates/chatbot.html`, `templates/profile.html` (new), `chatbot/views.py`, `chatbot/urls.py`, `static/js/color-modes.js`, `static/css/variables.css`, `static/css/custom.css`.
Test: settings persist + resolve correctly; theme toggles and persists per user; export→import round-trips a chat to identical messages.
Note: the theme *toggle* alone is low-risk and independent — can land as an early standalone commit within this phase if a quick visible win is wanted.

### Cluster 2 — Chat UX

**P9 — Streaming (SSE, sync workers). [INFRA]**
Goal: SSE endpoint returning `StreamingHttpResponse(gen(), content_type="text/event-stream")` with `X-Accel-Buffering: no` + `Cache-Control: no-cache`; call `client.chat.completions.create(stream=True, stream_options={"include_usage": True})`; accumulate chunks and in `finally` persist the assistant `Message` + usage. gunicorn → `gthread` workers (`gunicorn.conf.py`); nginx `proxy_buffering off` on the stream location (`nginx/default.conf:11-19` currently buffers). Rework `form.js` `fetchBotResponse` (`form.js:174-199`) to consume the stream.
Files: `chatbot/views.py`, `chatbot/urls.py`, `gunicorn.conf.py`, `nginx/default.conf`, `static/js/form.js`.
Test: endpoint yields multiple SSE chunks (mocked client); final usage persisted; tiktoken estimate fallback when `usage` absent. **Rewrite** `test_views.py::TestChatbotView::test_chatbot_post_request` — the JSON `{message, response}` contract becomes an SSE stream; assert on streamed chunks + final persistence instead.

**P10 — Client-side markdown + LaTeX.**
Goal: replace server-side markdown with client render: `markdown-it` + KaTeX + highlight.js + DOMPurify. Store **raw markdown** in `Message.content` (enables raw-md export + re-render on theme change). Incremental render during stream (re-render buffer on a throttled tick); run highlight + KaTeX on final flush only. Remove the `custom_filters.py` double-parse and the `markdown_to_html` call in `chatbot.html:96`.
Files: `templates/chatbot.html`, `static/js/render.js` (new), `static/js/form.js`, remove `chatbot/templatetags/custom_filters.py` usage, rewrite the markdown test.
Test: render+sanitize snapshot; an XSS payload is neutralized by DOMPurify; a LaTeX expression renders to KaTeX markup. **Remove/replace** `test_templatetags.py` (261 lines, tied to the deleted `custom_filters.py`) — including `test_special_characters_escaping`, which currently *asserts XSS passes through*; the new client-side path must instead assert it is sanitized.

**P11 — Edit user message + regenerate (truncate later context).**
Goal: edit any user message at `sequence=N`; set `is_active=False` on all rows with `sequence > N` in one `transaction.atomic()` `update()`; regenerate from active rows ≤ N with the current model; UI drops DOM nodes after the edited one. Hard delete reserved for archive management; usage ledger (P12) keeps inactive rows so reports stay accurate.
Files: `chatbot/views.py`, `chatbot/urls.py`, `static/js/form.js`, `templates/chatbot.html`.
Test: edit at N deactivates later rows transactionally; regenerate uses only active ≤ N.

### Cluster 3 — Cost visibility

**P12 — Usage ledger + per-chat cost + reports. [MIG]**
Goal: append-only `UsageRecord` (`user`, `chat_room` SET_NULL, `message` SET_NULL, `model`, prompt/completion tokens, `cost_usd`, `created_at` indexed); write one record per completion (sync + streaming paths); per-chat cost from `ChatRoom.total_*` denorm × `ModelCatalog` prices; weekly/monthly report view via `TruncWeek`/`TruncMonth` aggregation. Token estimation + price preview before send.
Files: `chatbot/models.py`, `chatbot/usage.py` (new), `chatbot/views.py`, `templates/` report page, migration.
Test: completion writes exactly one record; weekly/monthly sums correct; cost = price × tokens.

**P13 — Chatroom header + share/export.**
Goal: header showing room name with manual-edit, refresh-auto-rename button, a message-count status line (uses `ChatRoom.message_count`), and a share/export control (raw markdown now; image export as a follow-up). Per-chat cost surfaced here.
Files: `templates/chatbot.html`, `chatbot/views.py`, `static/js/`, header partial.
Test: rename persists and flips `title_is_auto`; export returns raw markdown; counter accurate.

### Cluster 4 — Organization + memory

**P14 — Auto-titles + Memory Note + history compression + send-summary.**
Goal: summarization-model-driven auto room titles (respect `title_is_auto` so manual names aren't overwritten); rolling `memory_note` updated each turn; compress history past `summarize_threshold_tokens` by writing `summary` + `summary_through_seq` (messages ≤ that seq are represented by the summary in assembled context — rows are never deleted); per-room/user toggle to send the summary with each request.
Files: `chatbot/summarization.py` (new), `chatbot/views.py`, `chatbot/models.py`.
Test: threshold triggers compression; summarized prefix replaces old turns in assembled context; manual title preserved.

**P15 — Archived-chat management + interest profile + caching.**
Goal: archived view with multi-select restore + **hard delete** (cascades `Message`); cross-room "interest profile" auto-collected into `UserProfile.interest_profile` via a management command / scheduled task, optionally injected as context; server-side caching (Django cache for `GlobalSettings`, room list) + browser-side caching of the chatroom list (`localStorage` with invalidation on create/rename/archive).
Files: `chatbot/views.py`, `templates/`, `chatbot/management/commands/update_interest_profiles.py` (new), `settings/base.py` (`CACHES`), `static/js/sidebar.js`.
Test: hard delete removes room + messages; restore flips `is_hidden`; cached room list invalidates correctly.

**P16 — Search + filters. [MIG]**
Goal: Postgres full-text search via `django.contrib.postgres.search` — `SearchVectorField` on `Message` (maintained on save) + `GinIndex`; `pg_trgm` + trigram `GinIndex` for room-name search; search bar (FTS over message bodies ranked by `SearchRank`, trigram over names); filters by date / name / message-count (the last uses the denormalized `ChatRoom.message_count`).
Files: `chatbot/models.py`, migration (adds extension + GIN index), `chatbot/views.py`, `chatbot/urls.py`, `templates/`, `static/js/sidebar.js`.
Test: FTS finds message substrings ranked; trigram name search; filters compose.

---

## Critical files

- `chatbot/models.py`
- `chatbot/views.py`
- `django_chatbot/settings.py` (→ split into `settings/`)
- `chatbot/templatetags/custom_filters.py` (removed in P10)
- `templates/chatbot.html`
- `static/js/form.js`
- `nginx/default.conf`
- `entrypoint.sh`
- `docker-compose.yml`

## Verification

- **Per phase**: `uv run ruff check`, `uv run mypy`, `uv run pytest` all green before committing. Each phase adds focused tests (see per-phase "Test").
- **P3/P5 data safety** (most important): before any destructive step, confirm `backup/chats_export.json` exists and `backup/db.sqlite3` is copied. After Postgres load, run the `verify_import` command and assert User/ChatRoom/Chat counts match the SQLite source. After `backfill_messages`, assert `Message` count == 2 × `Chat` count and ordering is contiguous per room. Keep the `Chat` table until P5 verification passes.
- **End-to-end smoke** (Playwright MCP available): after P8 — toggle theme, change a setting, reload, confirm persistence. After P9 — send a message, observe tokens streaming incrementally. After P16 — search a known phrase, confirm the right room surfaces.
- **Deploy check**: `uv run manage.py check --deploy` clean under prod settings after P1; SSE verified through nginx (not buffered) after P9.

## Suggested first commit

P0 (tooling cleanup) — fix the test-layout collision, the dual pytest config, and add ruff/mypy/pre-commit so the merged suite actually runs under the documented command and every later phase has a trustworthy green baseline. Non-breaking, small, and it de-risks everything built on top.
