# Django 5.2 LTS — Models, Fields, Meta, Migrations

> Target: Django 5.2 LTS (supports Python 3.10–3.14). Notes flag what changed since 4.2.
> Source pages cited per section. Verify anything not here against the installed source
> (`site-packages/django/db/models/`) or `https://docs.djangoproject.com/en/5.2/`.

## 1. Field types
Source: https://docs.djangoproject.com/en/5.2/ref/models/fields/

| Field | Stores | Key args |
|---|---|---|
| `CharField(max_length=None, **opts)` | Short/medium strings | `max_length` (required except SQLite in 5.2+); `db_collation` |
| `TextField(**opts)` | Large text | `max_length` (form-only, not enforced at DB) |
| `IntegerField` / `BigIntegerField` / `SmallIntegerField` | Signed ints (32/64/16-bit) | — |
| `PositiveIntegerField` / `PositiveBigIntegerField` / `PositiveSmallIntegerField` | ints ≥ 0 | — |
| `BooleanField(**opts)` | True/False | default value is `None` if unset |
| `DateField(auto_now=False, auto_now_add=False, **opts)` | `datetime.date` | see §3 |
| `DateTimeField(auto_now=False, auto_now_add=False, **opts)` | `datetime.datetime` | see §3 |
| `UUIDField(**opts)` | UUID | use `default=uuid.uuid4` (callable, no parens). Native `uuid` on PostgreSQL / MariaDB 10.7+, else `char(32)` |
| `DecimalField(max_digits=None, decimal_places=None, **opts)` | `Decimal`, fixed precision | both `max_digits` + `decimal_places` required |
| `JSONField(encoder=None, decoder=None, **opts)` | JSON (dict/list/scalar) | use callable `default` to avoid shared mutable; SQLite needs JSON1 |
| `FileField(upload_to='', storage=None, max_length=100, **opts)` | Path to uploaded file | `upload_to` (str strftime or callable); `storage` (obj or callable) |
| `ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, **opts)` | Validated image | requires Pillow |
| `ForeignKey` / `OneToOneField` / `ManyToManyField` | Relations | see §6 |
| `EmailField(max_length=254)` / `URLField(max_length=200)` / `SlugField(max_length=50, allow_unicode=False)` | Validated CharField variants | `SlugField` implies `db_index=True` |
| `AutoField` / `BigAutoField` / `SmallAutoField` | Auto-increment PK | auto-added unless PK declared; type via `DEFAULT_AUTO_FIELD` |
| `DurationField` / `BinaryField` / `FloatField` / `FilePathField` | timedelta / bytes / float / fs path | `BinaryField` defaults `editable=False` |
| `GeneratedField(...)` | DB-computed column | NEW 5.0 — see §5 |
| `CompositePrimaryKey(*field_names)` | Multi-field PK | NEW 5.2 — see §5 |

## 2. Common field arguments
Source: https://docs.djangoproject.com/en/5.2/ref/models/fields/

- **`null`** (default `False`) — DB-level, stores `NULL`. Avoid on string fields (convention = empty
  string `""`). Purely database; does not affect form validation.
- **`blank`** (default `False`) — validation/form-level: whether the field may be empty in forms.
  **`null` ≠ `blank`**: `null` is the DB, `blank` is validation. Independent.
- **`default`** — Python-side default; value or callable (invoked per new object). Must NOT be a
  mutable instance (list/dict/set/model) — wrap in a callable (`default=list`, `default=dict`).
  Lambdas are not migration-serializable.
- **`db_default`** — NEW 5.0 — database-computed default (literal or DB function, e.g.
  `db_default=Now()`). Cannot reference other fields (`F("start")+50` is invalid). If both `default`
  and `db_default` are set, `default` wins in Python, `db_default` at the DB level.
- **`db_index`** (default `False`) — creates a single-column index. **Fully supported, not
  deprecated.** Use it for simple single-column indexes; use `Meta.indexes` for composite,
  conditional (`condition=`), or covering (`include=`) indexes. (`index_together` is the deprecated
  one — see §4.)
- **`unique`** (default `False`) — enforced at DB + model validation; raises `IntegrityError`.
  Implies an index (no need for `db_index=True`). Not valid on M2M.
- **`choices`** — accepts (NEW forms in 5.0):
  1. sequence of 2-tuples `[("FR","Freshman"), ...]`
  2. **mapping/dict** `{"FR":"Freshman", ...}` (nested dict for option groups)
  3. **callable** returning either of the above (invoked each form instantiation)
  4. **enumeration type** passed directly: `choices=YearInSchool` (`.choices` no longer required).
     Use `models.TextChoices` / `IntegerChoices`; gives `.label/.choices/.labels/.values/.names`
     and model `get_FOO_display()`.
- **`primary_key`** (default `False`) — implies `null=False, unique=True`; one per model (or
  `CompositePrimaryKey`). Read-only after save.
- **`editable`** (default `True`) — `False` hides from admin/ModelForm and skips model validation.
- **`validators`**, **`help_text`**, **`verbose_name`**, **`error_messages`**, **`db_column`**,
  **`db_comment`**, **`db_tablespace`**.

## 3. auto_now / auto_now_add
Source: https://docs.djangoproject.com/en/5.2/ref/models/fields/

- `auto_now=True` — set to now on **every** `Model.save()`. Not applied on `QuerySet.update()`.
  Sets `editable=False, blank=True`.
- `auto_now_add=True` — set to now **only on creation**; a passed value is ignored.
- `auto_now`, `auto_now_add`, `default` are **mutually exclusive**.
- For an editable creation timestamp use `default=timezone.now` (datetime) / `default=date.today`
  (date) instead of `auto_now_add`.

## 4. Meta options
Source: https://docs.djangoproject.com/en/5.2/ref/models/options/

```python
class Meta:
    ordering = ["-pub_date", "author"]   # "-" desc, "?" random; supports F() e.g. F("author").asc(nulls_last=True)
    constraints = [...]                  # list of Constraint objects (see §4a)
    indexes = [...]                      # list of Index objects (see §4b)
    db_table = "music_album"             # override auto table name app_model
    verbose_name = "pizza"
    verbose_name_plural = "stories"      # defaults to verbose_name + "s"
    default_related_name = "..."         # default reverse-relation + related_query_name (default <model>_set)
    get_latest_by = ["-priority", "order_date"]
    permissions = [("can_x", "Can X")]
    managed = True                       # False = Django won't create/alter/drop the table
    abstract = True                      # abstract base class
    app_label = "myapp"
```
- **`unique_together`** is soft-deprecated (docs: use `UniqueConstraint`). **`index_together` is
  deprecated and removed in 5.1** — use `indexes`.

### 4a. Constraints
Source: https://docs.djangoproject.com/en/5.2/ref/models/constraints/

```python
class CheckConstraint(*, condition, name, violation_error_code=None, violation_error_message=None)
```
- **`condition`** is the current param (Q object or boolean Expression). The old **`check`** kwarg is
  **deprecated since 5.1** — use `condition`.

```python
class UniqueConstraint(*expressions, fields=(), name=None, condition=None, deferrable=None,
                       include=None, opclasses=(), nulls_distinct=None,
                       violation_error_code=None, violation_error_message=None)
```
- `*expressions` → functional unique constraints. `condition=` (Q) → partial/conditional unique.
  `nulls_distinct` (NEW 5.0, PostgreSQL 15+). `deferrable`/`include`/`opclasses` are PostgreSQL-only.
- **5.2 change**: `violation_error_code`/`violation_error_message` are now **always used when
  provided** (previously ignored when `fields` set without `condition`).

### 4b. Indexes
Source: https://docs.djangoproject.com/en/5.2/ref/models/indexes/

```python
class Index(*expressions, fields=(), name=None, db_tablespace=None,
            opclasses=(), condition=None, include=None)
```
- `fields=["last_name", "first_name"]` standard; `*expressions` → functional indexes, e.g.
  `Index(Lower("title").desc(), "pub_date", name="...")`.
- `name` is **required** when using `expressions`, `opclasses`, `condition`, or `include`.
- `condition=` (Q) → partial index (PostgreSQL, SQLite; ignored on MySQL/MariaDB).

## 5. New in 5.0 / 5.1 / 5.2 (model layer)
Sources: release notes /5.0/, /5.1/, /5.2/

**5.0**
- `GeneratedField(expression, output_field, db_persist=None, **kwargs)` — DB-generated column
  (`GENERATED ALWAYS`). `db_persist=True` stored / `False` virtual. Cannot reference other generated
  fields; reload via `refresh_from_db()` after save.
- `Field.db_default` — database-computed default (see §2).
- `Field.choices` expanded: mappings, callables, enums passed directly.
- `UniqueConstraint.nulls_distinct` (PostgreSQL 15+).
- `violation_error_code` on `BaseConstraint`/`CheckConstraint`/`UniqueConstraint`.

**5.1**
- `CheckConstraint.check` kwarg deprecated → renamed `condition`.
- `index_together` removed.
- `Operation.category`; `makemigrations` shows per-operation symbols.

**5.2**
- `CompositePrimaryKey(*field_names)` — multi-field primary key; assigned to the model's `pk`.
- `GeneratedField` supports validation of model constraints that use it.
- `CharField.max_length` no longer required on SQLite.
- `UniqueConstraint.violation_error_code`/`_message` now always used when provided.
- New migration op `AlterConstraint` (no-op alter, avoids drop/recreate).
- New `JSONArray` DB function.

## 6. Relationships
Source: https://docs.djangoproject.com/en/5.2/topics/db/models/

```python
ForeignKey(to, on_delete, related_name=None, related_query_name=None,
           to_field=None, db_constraint=True, **kwargs)         # on_delete REQUIRED
OneToOneField(to, on_delete, parent_link=False, **kwargs)
ManyToManyField(to, through=None, through_fields=None, symmetrical=True,
                related_name=None, db_table=None, **kwargs)
```
- **`on_delete`** (required for FK/O2O): `CASCADE`, `PROTECT` (→ `ProtectedError`), `RESTRICT`,
  `SET_NULL` (needs `null=True`), `SET_DEFAULT`, `SET(value_or_callable)`, `DO_NOTHING`.
- **`related_name`** = reverse-accessor name (default `<model>_set`); **`related_query_name`** = name
  in reverse filter lookups.
- Abstract-base placeholders in `related_name`/`related_query_name`: `%(class)s`, `%(app_label)s`.
- **M2M `through`**: intermediary needs exactly one FK to each side (or specify `through_fields`).
  Enforce pair uniqueness with a `UniqueConstraint`.

### Inheritance
- **Abstract base** (`Meta.abstract=True`): not a table. Child inherits parent `Meta` if it defines
  none (Django resets `abstract=False` on the child).
- **Multi-table inheritance**: each model gets its own table linked by an auto `OneToOneField`. Child
  does NOT inherit parent `Meta` (only `ordering`/`get_latest_by` carry over if unset).
- **Proxy** (`Meta.proxy=True`): same table; may change default manager/ordering.

## 7. Migrations workflow
Source: https://docs.djangoproject.com/en/5.2/topics/migrations/

Commands (run via `uv run python manage.py …`):
- `makemigrations [app_label]` — generate from model changes. `--name`, `--empty` (scaffold a data
  migration), `--check --dry-run` (CI drift check).
- `migrate [app_label] [migration_name]` — apply/unapply. `--fake`, `--fake-initial`, `--prune`.
- `sqlmigrate app_label name` — print SQL, don't run. `showmigrations`. `squashmigrations myapp 0004`.

Migration file:
```python
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True                                   # optional
    atomic = True                                    # False = no wrapping transaction
    dependencies = [("app", "0001_initial")]         # (app_label, migration_name) tuples
    operations = [...]                               # CreateModel, AddField, RunPython, RunSQL, ...
```

Data migration with `RunPython`:
```python
def forwards(apps, schema_editor):
    Person = apps.get_model("yourapp", "Person")     # historical model — NOT a direct import
    for p in Person.objects.all():
        p.name = f"{p.first_name} {p.last_name}"
        p.save()

migrations.RunPython(forwards, migrations.RunPython.noop)   # 2nd arg = reverse_code
```
- Signature is always `def fn(apps, schema_editor)`. `apps.get_model()` returns historical models
  (fields/managers only, **no custom methods/`save()` overrides**).
- Omitting `reverse_code` makes it irreversible; pass `RunPython.noop` for a no-op reverse.
- **This project's preference**: for non-trivial backfills, prefer an **idempotent management
  command** over baking logic into `RunPython` — it runs against real models, is unit-testable, and
  is re-runnable. Keep `RunPython` for simple, deterministic in-migration transforms.

Dependencies & squashing:
- A migration adding an FK to another app must depend on that app's migration; for the swappable
  user model use `swappable_dependency(settings.AUTH_USER_MODEL)`.
- Squash creates `0001_squashed_0004_*` with `replaces=[...]`; old + new coexist until every
  environment passes the squash point, then delete originals and remove `replaces`.

## 8. Gotchas
- **FK `on_delete` is required** — omitting it is a `TypeError`.
- **`auto_now_add` + ordering ties**: same-tick rows share a timestamp, so `ordering=["created"]` is
  non-deterministic for ties — add a tiebreaker (`["created", "id"]`). Also the cause of flaky
  ordering tests.
- **`auto_now`/`auto_now_add` ignore `QuerySet.update()`** and `bulk_*` — only fire on `Model.save()`.
- **Mutable defaults**: `default=[]`/`{}` shares one object — use `default=list`/`default=dict`.
- **`db_default` can't reference other fields** — use `GeneratedField` for computed-from-columns.
- **Migration ordering** is by `dependencies`, not filename — a missing cross-app dependency makes
  `apps.get_model()` raise `LookupError`.
- **SQLite** has no native ALTER (emulated by create-copy-drop-rename); some index features
  (`condition`/`include`/`opclasses`) are PostgreSQL-only.
