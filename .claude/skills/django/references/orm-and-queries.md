# Django 5.2 LTS — ORM / QuerySets / Expressions / Transactions

> PostgreSQL is the target DB. Import paths verified against the 5.2 docs.

## 1. Core QuerySet methods
Source: https://docs.djangoproject.com/en/5.2/ref/models/querysets/

**Retrieval**
- `filter(*args, **kwargs)` / `exclude(*args, **kwargs)` — new lazy QuerySet. Multiple kwargs AND-join;
  `exclude` wraps in `NOT(...)`.
- `get(*args, **kwargs)` — single object; raises `Model.DoesNotExist` / `Model.MultipleObjectsReturned`.
- `first()` / `last()`, `exists()`, `count()`, `in_bulk()`, `none()`, `all()`.
- `values(*fields, **expressions)` → dicts; `values_list(*fields, flat=False, named=False)` → tuples.
  **Changed in 5.2:** the generated `SELECT` clause now matches the order of referenced fields/expressions.

**Creating / updating in bulk**
- `create(**kwargs)`, `get_or_create(defaults=None, **kwargs)` → `(obj, created)`.
- `update_or_create(defaults=None, create_defaults=None, **kwargs)` → `(obj, created)`.
  `create_defaults` is **new in 5.0** (distinct field values for create vs update path).
- `bulk_create(objs, batch_size=None, ignore_conflicts=False, update_conflicts=False,
  update_fields=None, unique_fields=None)`. `update_conflicts=True` requires `update_fields`;
  `unique_fields` is the conflict target (Postgres `ON CONFLICT (...) DO UPDATE`). **Bypasses
  `save()` and signals.**
- `bulk_update(objs, fields, batch_size=None)`.
- `update(**kwargs)` — SQL `UPDATE`. **Does not call `save()` or send signals.** Accepts `F()`:
  `Room.objects.update(msg_count=F("msg_count") + 1)` (local fields only, no joins).
- `delete()`.

**Ordering / slicing**
- `order_by(*fields)` — `-` prefix = DESC; supports expressions, `F("x").desc(nulls_last=True)`, `"?"`.
- `reverse()`, `distinct(*fields)` (field-args = Postgres `DISTINCT ON`).
- Slicing returns an unevaluated QuerySet (`LIMIT/OFFSET`) unless a step is used.

**Performance**
- `select_related(*fields)`, `prefetch_related(*lookups)` — see §2.
- `only(*fields)` / `defer(*fields)` — column subset; deferred fields raise `SynchronousOnlyOperation`
  if accessed from async.
- `alias(*args, **kwargs)` — like `annotate()` but not selected (filter/order-only expressions).
- `iterator()`, `explain(...)`.

## 2. select_related vs prefetch_related
Source: https://docs.djangoproject.com/en/5.2/topics/db/optimization/

**N+1 problem:** iterating objects and touching a related object per-iteration issues one query per
row. Fix by fetching related data up front.

- `select_related(*fields)` — **single-valued** relations (FK, O2O). One SQL `JOIN`, follows `__`
  chains: `Chat.objects.select_related("room__owner")`. Use for the chat list (FK to room/user).
- `prefetch_related(*lookups)` — **multi-valued** relations (M2M, reverse FK). Separate query, joined
  in Python.

**Prefetch object** (`from django.db.models import Prefetch`):
```python
Room.objects.prefetch_related(
    Prefetch("chats",
             queryset=Chat.objects.filter(is_hidden=False).select_related("user"),
             to_attr="visible_chats")
)
```
Callable related managers (`obj.chats.all()`) are NOT cached between calls; only non-callable
attributes (e.g. `chat.room`) are.

## 3. F() and Q()
Source: https://docs.djangoproject.com/en/5.2/topics/db/queries/ · ref/models/expressions/

`from django.db.models import F, Q`

**F() — atomic, DB-side field updates** (avoids read-modify-write races):
```python
Room.objects.filter(pk=rid).update(msg_count=F("msg_count") + 1)   # atomic counter
Entry.objects.filter(mod_date__gt=F("pub_date") + timedelta(days=3))
Company.objects.update(is_active=~F("is_active"))                  # negate bool
```
**New in 5.1:** F()/OuterRef() string slicing for text fields: `F("name")[1:5]`.

**Q() — complex OR/AND/NOT:** `|` OR, `&` AND, `~` NOT.
```python
Chat.objects.filter(Q(role="user") | Q(role="system"))
```
When mixing `Q` with keyword args, **positional Q args come before keyword args**:
`Poll.objects.get(Q(a=1) | Q(b=2), question__startswith="Who")`.

## 4. Aggregation
Source: https://docs.djangoproject.com/en/5.2/topics/db/aggregation/

`from django.db.models import Count, Sum, Avg, Min, Max`

- `aggregate(*args, **kwargs)` — **terminal**, dict over the whole queryset:
  `Book.objects.aggregate(Avg("price"))` → `{'price__avg': 34.35}`.
- `annotate(*args, **kwargs)` — **per-object**, returns a QuerySet.

**GROUP BY:** `.values(...).annotate(...)` groups by the `values()` fields:
```python
Chat.objects.values("model_id").annotate(n=Count("id"))
```
**`filter=` (conditional aggregation):**
```python
Room.objects.annotate(user_msgs=Count("chats", filter=Q(chats__role="user")))
```
**`distinct=True`** on `Count`/`Sum` avoids inflation across multiple multi-valued joins.

**Order matters:** `.filter().annotate()` constrains what the aggregate counts;
`.annotate().filter()` constrains which rows return.

**Null-safe:** `Sum("age", default=0)` or `Coalesce(Sum("age"), 0)`. **5.2:** single-arg aggregates
(`Avg`, `Count`, `Max`, `Min`, `StdDev`, `Sum`, `Variance`) raise `TypeError` on wrong arg count.

## 5. Conditional expressions
Source: https://docs.djangoproject.com/en/5.2/ref/models/expressions/

`from django.db.models import Case, When, Value, F`
```python
Room.objects.annotate(
    size=Case(
        When(msg_count__lt=10, then=Value("small")),
        When(msg_count__lt=100, then=Value("medium")),
        default=Value("large"),
        output_field=CharField(),
    )
)
```
`Subquery` / `OuterRef` / `Exists` (`from django.db.models import Subquery, OuterRef, Exists`):
```python
newest = Chat.objects.filter(room=OuterRef("pk")).order_by("-created")
Room.objects.annotate(last_msg=Subquery(newest.values("message")[:1]))
Room.objects.filter(Exists(Chat.objects.filter(room=OuterRef("pk"))))   # ~Exists() to negate
```
Window: `Window(expression=..., partition_by=[F(...)], order_by=..., frame=...)`.

## 6. Date functions (time-bucketed reports)
Source: https://docs.djangoproject.com/en/5.2/ref/models/database-functions/

Import: `from django.db.models.functions import Trunc, TruncWeek, TruncMonth, TruncYear, TruncDay,
Coalesce, Concat, Now`

- `Trunc(expression, kind, output_field=None, tzinfo=None)` — `kind` ∈ `"year"|"month"|"week"|"day"|…`.
- `TruncWeek(...)` truncates to midnight Monday; `TruncMonth(...)` to the first of the month.

Weekly / monthly usage report:
```python
from django.db.models import Count
from django.db.models.functions import TruncWeek

Chat.objects.annotate(week=TruncWeek("created")).values("week") \
    .annotate(n=Count("id")).order_by("week")
```
`Coalesce(*exprs)` — first non-null. `Now()` — DB `CURRENT_TIMESTAMP`.

## 7. Transactions
Source: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

`from django.db import transaction`
```python
@transaction.atomic
def regenerate(request): ...

with transaction.atomic():
    Chat.objects.filter(room=room, created__gt=ts).delete()   # truncate-on-edit
    create_new_response()
```
- `atomic(using="default", savepoint=True, durable=False)`.
- **`durable=True`** — guarantees the outermost atomic block; raises `RuntimeError` if nested.
- **Nested `atomic()` → savepoints.** Inner rollback only undoes inner work.
- **Never catch DB exceptions inside an atomic block** — catch around it.
- `transaction.on_commit(func, robust=False)` — run after commit (skipped on rollback).
- **`select_for_update(nowait=False, skip_locked=False, of=(), no_key=False)`** — `SELECT … FOR
  UPDATE` row lock; must run inside an atomic block. Lock a room row before read-then-update of a
  denormalized counter.
- **Per-request transactions:** `"ATOMIC_REQUESTS": True` in the DB config wraps each view; opt out
  with `@transaction.non_atomic_requests`.

## 8. Async ORM methods in 5.2
Source: ref/models/querysets/ · releases/5.0, /5.2

`a`-prefixed coroutine equivalents exist for I/O methods. QuerySet-building methods stay sync (no DB
hit until awaited):
`aget`, `acreate`, `aget_or_create`, `aupdate_or_create`, `abulk_create`, `abulk_update`, `aupdate`,
`adelete`, `acount`, `aexists`, `afirst`, `alast`, `aaggregate`, `ain_bulk`, `acontains`, `aexplain`,
`aiterator`. **5.0** added `aget_object_or_404()`, `aget_list_or_404()`,
`aprefetch_related_objects()`. Async iteration: `async for obj in qs:`.

## 9. Gotchas
- **QuerySets are lazy** — no DB hit until evaluated (iteration, `list()`, `len()`, `bool()`,
  slicing-with-step, `repr()`). Chained `filter()`s build one query.
- **Results are cached** after evaluation; re-running `.all()` or a callable related manager
  re-queries. If you need both the data and a count, evaluate once and use `len()`/`in` against the
  cached list rather than `count()`/`exists()`.
- **`.update()` bypasses `Model.save()` and `pre_save`/`post_save` signals** (and `auto_now`). Use
  `F()` for atomic increments.
- **`bulk_create()`/`bulk_update()` bypass `save()`** and signals.
- **`count()` vs `len()`** — `count()` (SQL `COUNT`) when you only need the number; `len()` only on an
  already-evaluated QuerySet. **`exists()` vs `bool()`** — `exists()` for a pure existence check.
- **`only()`/`defer()`** — accessing a deferred field triggers a per-object query (re-introduces N+1).
- **Templates evaluate QuerySets** — prefetch in the view, not the template.
- **5.2 `values()`/`values_list()` SELECT ordering changed** — output column order now follows arg
  order; code combining querysets on the old order may behave differently.
