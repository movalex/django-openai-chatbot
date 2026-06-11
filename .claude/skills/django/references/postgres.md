# Django 5.2 LTS — PostgreSQL features (`django.contrib.postgres`)

> Requirement for everything below: **`"django.contrib.postgres"` in `INSTALLED_APPS`**, and
> extensions enabled via a migration operation. Roadmap P16 builds full-text search +
> trigram room-name search on this.

## 1. Full-text search
Source: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/search/
Import: `from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline, SearchVectorField`

- **`SearchVector(*expressions, config=None, weight=None)`** — build a searchable vector across
  fields. Combine with `+`; weights `A`/`B`/`C`/`D`.
- **`SearchQuery(value, config=None, search_type="plain")`** — `search_type` ∈ `"plain"`, `"phrase"`,
  `"raw"`, `"websearch"`. Combine with `&` (AND), `|` (OR), `~` (NOT).
- **`SearchRank(vector, query, weights=None, normalization=None, cover_density=False)`** — relevance
  score for `order_by("-rank")`. Default weights `[0.1, 0.2, 0.4, 1.0]` (D,C,B,A).
- **`SearchHeadline(expression, query, start_sel=..., stop_sel=...)`** — highlighted snippets.
- **`__search` lookup** — quick path: `Entry.objects.filter(body_text__search="Cheese")`.
- **`SearchVectorField`** — denormalized stored column for performance. **Not auto-maintained** —
  populate it (in `save()`, via `F()` update, or a DB trigger), then filter directly:
  `Model.objects.filter(search_vector="cheese")`.

```python
Entry.objects.annotate(
    search=SearchVector("body_text", weight="A") + SearchVector("title", weight="B"),
    rank=SearchRank("search", SearchQuery("cheese")),
).filter(search=SearchQuery("cheese")).order_by("-rank")
```

## 2. Indexes
Source: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/indexes/
Import: `from django.contrib.postgres.indexes import GinIndex, BTreeIndex, BrinIndex, GistIndex, OpClass`

- **`GinIndex(fields=[...], name=..., fastupdate=True)`** — the index for **`SearchVectorField` and
  trigram** lookups.
- For GIN on a non-default operator class (trigram `gin_trgm_ops`), use **`OpClass`**:
```python
from django.db.models import F
class Meta:
    indexes = [
        GinIndex(fields=["search_vector"], name="entry_search_gin"),
        GinIndex(OpClass(F("name"), name="gin_trgm_ops"), name="room_name_trgm_gin"),
    ]
```

## 3. Trigram (pg_trgm)
Source: ref/contrib/postgres/operations/ · ref/contrib/postgres/lookups/

Enable in a migration:
```python
from django.contrib.postgres.operations import TrigramExtension
class Migration(migrations.Migration):
    operations = [TrigramExtension(), ...]      # or CreateExtension("pg_trgm")
```
- Lookups: **`__trigram_similar`**, **`__trigram_word_similar`**, **`__trigram_strict_word_similar`**:
  `ChatRoom.objects.filter(name__trigram_similar="Mddlesborough")`.
- Ranking/threshold functions (annotate then filter/order): **`TrigramSimilarity`**,
  **`TrigramWordSimilarity`**, **`TrigramDistance`** from `django.contrib.postgres.search`.

## 4. Fields
Source: ref/contrib/postgres/fields/ · ref/models/fields/
Import: `from django.contrib.postgres.fields import ArrayField, HStoreField` (+ range fields).

- **`ArrayField(base_field, size=None)`** — Postgres native array.
- **`HStoreField()`** — key/value strings; requires the `hstore` extension (`HStoreExtension()`).
- **`JSONField` is core, not postgres-specific.** Use **`django.db.models.JSONField`** (works on
  PostgreSQL, MySQL/MariaDB, Oracle, SQLite). The old
  `django.contrib.postgres.fields.JSONField` was superseded in Django 3.1 and is gone — import from
  `django.db.models`.

## 5. Extension operations
Source: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/operations/
`from django.contrib.postgres.operations import CreateExtension, TrigramExtension, BtreeGinExtension,
CITextExtension, HStoreExtension, UnaccentExtension`

Each is a `migrations.Operation` added to a migration's `operations`; idempotent (skips if present).
`CreateExtension(name)` is the generic form.

## 6. Gotchas
- **`SearchVectorField` is not maintained automatically** — repopulate it on every write (override
  `save()`, `post_save` + `F()` update, or a Postgres trigger), or searches go stale. P16's
  "maintained on save" = do this in the model's `save()`.
- **GIN index is required for performance** — without it, FTS/trigram queries do full table scans.
  Trigram GIN needs the `gin_trgm_ops` opclass (via `OpClass`).
- **Extension migration ordering** — the extension op must run in a migration applied *before* any
  migration that creates a trigram GIN index or uses the field. The DB role needs privilege to
  `CREATE EXTENSION` (superuser, or pre-install the extension). Put the op in an early migration with
  the right `dependencies`.
- **5.2 requires PostgreSQL 14+** (PG13 was dropped in 5.2).
