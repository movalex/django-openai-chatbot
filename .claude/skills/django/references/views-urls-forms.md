# Django 5.2 LTS — Views, URLs, Forms, CSRF, Auth, HTTP Responses

> Target version: Django 5.2 LTS. This project's views are moving to htmx (return rendered HTML
> fragments) rather than JSON; streaming uses SSE on sync workers.

## 1. Function-based view anatomy
Source: https://docs.djangoproject.com/en/5.2/topics/http/views/ · topics/http/shortcuts/

```python
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

def my_view(request, chat_room_id):          # kwargs come from the URLconf
    if request.method == "POST":
        return redirect("chatbot:room", chat_room_id=chat_room_id)
    return render(request, "chatbot.html", {"room_id": chat_room_id})
```
- `render(request, template_name, context=None, content_type=None, status=None)` → `HttpResponse`.
- `HttpResponse("<h1>Hi</h1>")` / `HttpResponse(status=201)` — raw (good for htmx HTML fragments).
- `JsonResponse({...})` — JSON.
- `redirect(to, *args, permanent=False, preserve_request=False, **kwargs)`.
- `raise Http404("message")`; `get_object_or_404(klass, *args, **kwargs)` (also raises
  `MultipleObjectsReturned` if >1; `klass` may be Model, Manager, or QuerySet).

## 2. URLconf
Source: https://docs.djangoproject.com/en/5.2/topics/http/urls/

`from django.urls import path, re_path, include, reverse, reverse_lazy`

| Converter | Matches | Returns |
|---|---|---|
| `str` (default) | non-empty string, excluding `/` | `str` |
| `int` | zero or positive integer | `int` |
| `slug` | letters/numbers + hyphen/underscore | `str` |
| `uuid` | formatted UUID (lowercase, dashes) | `UUID` |
| `path` | non-empty string **including** `/` | `str` |

```python
path("chatroom/<uuid:chat_room_id>/", views.chatbot, name="room")
re_path(r"^articles/(?P<year>[0-9]{4})/$", views.year_archive)
```
Namespacing — set `app_name` in the included module:
```python
# chatbot/urls.py
app_name = "chatbot"
urlpatterns = [path("", views.chatbot, name="index")]
# config/urls.py
urlpatterns = [path("", include("chatbot.urls"))]
```
- `reverse("chatbot:room", kwargs={"chat_room_id": rid})`; `reverse_lazy(...)` for module/class-body.
- **5.2 new:** `reverse()`/`reverse_lazy()` accept `query=` (dict) and `fragment=`.
- Template tag: `{% url 'chatbot:room' chat_room_id %}`.
- **Trailing slashes:** a pattern ending in `/` matches only the slashed form. `APPEND_SLASH`
  (default `True`, via `CommonMiddleware`) redirects an unslashed URL to the slashed version *only if*
  the slashed form matches. Keep trailing-slash usage consistent.

## 3. HttpResponse family
Source: https://docs.djangoproject.com/en/5.2/ref/request-response/

- `HttpResponse(content=b'', content_type=None, status=200, headers=None)`. Set headers via
  `response["Cache-Control"] = "..."`. **5.2 new:** `response.text` (str view of `content`).
- `JsonResponse(data, encoder=DjangoJSONEncoder, safe=True, **kwargs)` — `safe=True` rejects non-dict
  `data`; pass `safe=False` for a list: `JsonResponse([1,2,3], safe=False)`.
- `StreamingHttpResponse(streaming_content, content_type=None, status=200)` — large files / SSE.
  Iterates over `streaming_content` (sync generator under WSGI). No `.content`/`.text`.

SSE pattern:
```python
def sse(request):
    def event_stream():
        for chunk in produce():
            yield f"data: {chunk}\n\n".encode()
    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"   # disable nginx proxy buffering
    return resp
```
Redirects: `HttpResponseRedirect(redirect_to, preserve_request=False)` — 302 default;
`preserve_request=True` → **307** (keeps method + body). Permanent variant → 301/308.
Status subclasses: `HttpResponseBadRequest` (400), `HttpResponseNotFound` (404),
`HttpResponseForbidden` (403), `HttpResponseNotAllowed` (405), etc. — or `HttpResponse(status=...)`.

`HttpRequest`: `.method`, `.GET`/`.POST` (immutable `QueryDict`; `.get()`, `.getlist()`, `.copy()`),
`.headers` (case-insensitive), `.body` (bytes), `.content_type`, `.user`. **5.2 new:**
`request.get_preferred_type()`.

## 4. Forms & ModelForm
Source: https://docs.djangoproject.com/en/5.2/topics/forms/ · ref/forms/validation/

```python
from django import forms

class ChatNameForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
```
Bound vs unbound: `ChatNameForm()` is unbound; `ChatNameForm(request.POST)` is bound.
```python
def rename(request):
    if request.method == "POST":
        form = ChatNameForm(request.POST)
        if form.is_valid():                       # runs full validation
            name = form.cleaned_data["name"]      # typed, normalized
            return redirect("/done/")
    else:
        form = ChatNameForm()
    return render(request, "rename.html", {"form": form})
```
Validation hooks (`from django.core.exceptions import ValidationError`):
- `clean_<fieldname>(self)` — reads `self.cleaned_data["x"]`, **must return** the cleaned value;
  `raise ValidationError(...)` attaches to that field.
- `clean(self)` — call `super().clean()`, do cross-field checks; a `ValidationError` here is a
  non-field error (`__all__`). `self.add_error("field", msg)` targets a specific field.

ModelForm:
```python
from django.forms import ModelForm
class ChatRoomForm(ModelForm):
    class Meta:
        model = ChatRoom
        fields = ["name"]            # or "__all__"; also exclude=, widgets=, labels=
```
**Why forms over manual `request.POST` parsing:** automatic validation + type coercion
(`cleaned_data` gives `int`/`bool`/`datetime`, not raw strings), sanitization, consistent error
re-render. `request.POST["x"]` is an unvalidated arbitrary string.

Rendering: default style is **div-based** (5.0+). `{{ form.as_div }}` / `as_p` / `as_table`;
per-field `{{ form.name }}`, `{{ form.name.errors }}`. `{{ form.name.as_field_group }}` (5.0) renders
label + widget + help + errors together.

## 5. CSRF
Source: https://docs.djangoproject.com/en/5.2/ref/csrf/

`CsrfViewMiddleware` validates a token on unsafe methods (POST/PUT/PATCH/DELETE); safe methods
(GET/HEAD/OPTIONS/TRACE) are never checked. The token is masked per-response.

Templates: `{% csrf_token %}` inside every POST `<form>`.

AJAX / fetch / htmx — send the token in the `X-CSRFToken` header:
```javascript
function getCookie(name) {
  for (const c of document.cookie.split(';')) {
    const t = c.trim();
    if (t.startsWith(name + '=')) return decodeURIComponent(t.slice(name.length + 1));
  }
  return null;
}
fetch('/save_chat_name/', {
  method: 'POST',
  headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
```
htmx: `<body hx-headers='{"X-CSRFToken": "<token>"}'>`. Use `@ensure_csrf_cookie` on the page view so
the cookie exists for the first AJAX call. Decorators
(`django.views.decorators.csrf`): `csrf_exempt`, `csrf_protect`, `requires_csrf_token`,
`ensure_csrf_cookie`. Avoid `@csrf_exempt` on state-changing endpoints.
`CSRF_TRUSTED_ORIGINS` **must include the scheme** (`https://example.com`).

## 6. Auth decorators & the IDOR pattern
Source: https://docs.djangoproject.com/en/5.2/topics/auth/default/ · topics/http/decorators/

```python
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth import authenticate, login, logout
```
- `@login_required(login_url=None, redirect_field_name="next")` — unauthenticated → `settings.LOGIN_URL`
  with `?next=`.
- `@permission_required("app.codename", raise_exception=False)` — `raise_exception=True` → 403.
- HTTP method decorators return **405** on mismatch: `@require_POST`, `@require_GET`, `@require_safe`,
  `@require_http_methods([...])`.
- `request.user.is_authenticated` to gate.

**IDOR fix** (the `save_chat_name` case — missing `@login_required` + missing owner filter): require
auth **and** scope every lookup to the current user.
```python
@login_required
@require_POST
def save_chat_name(request, chat_room_id):
    room = get_object_or_404(ChatRoom, pk=chat_room_id, user=request.user)  # owner filter
    ...
```
Filtering by `user=request.user` makes a mismatched owner return **404** (not 403), avoiding
object-existence leakage. Put `@login_required` outermost.

## 7. New since 4.2
Sources: releases/5.0, /5.1, /5.2

- **Div-based form rendering is the default (5.0)** — table-based default templates removed.
- **Field groups (5.0):** `{{ form.name.as_field_group }}`; fields gained `aria-describedby`/`aria-invalid`.
- **`forms.URLField.assume_scheme` (5.0)** — default scheme `http`→`https` deferred to 6.0;
  opt in early with `FORMS_URLFIELD_ASSUME_HTTPS=True`.
- **Async decorators:** 5.0 for csrf/http-method/cache; 5.1 for `login_required`, `permission_required`,
  `user_passes_test`.
- **`LoginRequiredMiddleware` (5.1)** — `django.contrib.auth.middleware.LoginRequiredMiddleware`
  redirects all unauthenticated requests; exempt with `@login_not_required`.
- **`HttpResponse.text` (5.2)**; `reverse()`/`reverse_lazy()` `query=`/`fragment=` (5.2);
  `redirect(..., preserve_request=...)` → 307/308 (5.2); `HttpRequest.get_preferred_type()` (5.2);
  new widgets `ColorInput`/`SearchInput`/`TelInput`.

## 8. Gotchas
- **CSRF with AJAX/htmx**: a POST without `{% csrf_token %}` or the `X-CSRFToken` header → 403. Read
  the token from the `csrftoken` cookie (or a fresh DOM node), not a cached copy.
- **`JsonResponse` lists** require `safe=False`. Returning HTML fragments for htmx sidesteps this — use
  plain `HttpResponse`/`render`.
- **`StreamingHttpResponse` + nginx**: nginx buffers proxied responses and breaks SSE. Set
  `X-Accel-Buffering: no` on the response and `proxy_buffering off;` on the nginx location.
- **`CSRF_TRUSTED_ORIGINS`** without a scheme is invalid.
- **IDOR**: never `get_object_or_404(Model, pk=pk)` for user-owned data — always `user=request.user`
  + `@login_required`.
- **`@require_POST` returns 405**, not 403/404 — distinct from auth failures.
