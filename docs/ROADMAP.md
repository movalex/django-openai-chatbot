# django-openai-chatbot — Roadmap

A phase plan for evolving the app from a working prototype into a maintainable,
feature-complete chatbot. This is a **map, not a manual** — each phase gets its
own concept-first guide in `docs/phases/NN-*.md` with the actual implementation
detail, decisions, and acceptance tests. This file just tracks scope and order.

## Working model

A learning-driven build. Phases land one at a time, human-reviewed:

- Each phase has a guide in `docs/phases/` that explains the concepts first, then
  the task, with decisions laid out as options + a recommendation.
- The author implements; commits and code stay theirs. One phase ≈ one focused commit.
- `uv run ruff check`, `uv run mypy chatbot`, and `uv run pytest` must be green
  before each commit.

## Key decisions

- **Data safety first** — chat history is preserved through the Postgres move and
  the schema redesign; transient state (session blobs) is disposable.
- **Streaming via SSE** on sync workers (no WebSockets/Channels/ASGI migration).
- **PostgreSQL** in dev and prod (parity so full-text search is testable locally).
- **First feature cluster: user control** — DB-backed settings, profile, real
  light/dark theme, per-user API keys + tiers.

## Phases

Tags: **[MIG]** schema migration · **[DATA]** touches existing chat data · **[INFRA]** deploy/config.

### Foundation

- **P0 — Tooling baseline** ✅ *done* — uv, ruff, mypy, pre-commit, pytest layout.
- **P1 — Code cleanup / refactor for clarity** — remove dead code and tangled
  control flow (no schema change, no new features); fix the two latent bugs.
- **P2 — Security & settings hardening** [INFRA] — env-driven `SECRET_KEY`/`ALLOWED_HOSTS`,
  secure-cookie/HSTS prod flags, split `settings/`, ownership check on rename (IDOR).
- **P3 — PostgreSQL migration** [INFRA][DATA] — SQLite → Postgres with zero chat loss.
- **P4 — Model catalog + per-request OpenAI client** [MIG] — DB-backed models + prices;
  drop the module-global API key.
- **P5 — Normalized `Message` model** [MIG][DATA] — replace the `Chat`-pair + `ChatSession`-blob
  duplication with one ordered message table; migrate existing history.
- **P6 — Settings infrastructure** [MIG] — global / per-user / per-room preferences with a
  resolver (room → user → global).

### Cluster 1 — User control

- **P7 — Encrypted per-user API keys + user tiers** [MIG].
- **P8 — Settings UI + profile page + real light/dark theme**.

### Cluster 2 — Chat UX

- **P9 — Streaming responses (SSE)** [INFRA].
- **P10 — Client-side markdown + LaTeX** (markdown-it + KaTeX + DOMPurify).
- **P11 — Edit a message + regenerate** (truncate later context).

### Cluster 3 — Cost visibility

- **P12 — Usage ledger + per-chat cost + weekly/monthly reports** [MIG].
- **P13 — Chatroom header + share/export**.

### Cluster 4 — Organization & memory

- **P14 — Auto-titles + rolling Memory Note + history compression**.
- **P15 — Archived-chat management + interest profile + caching**.
- **P16 — Search + filters** [MIG] (Postgres full-text + trigram).

## Per-phase verification

Each guide ends with acceptance tests. Extra care on the data phases (P3, P5):
keep a backup/export before destructive steps and verify row counts before
dropping anything. Migrations and schema-changing phases must also update the
existing fixtures/factories/tests, not just add new ones.
