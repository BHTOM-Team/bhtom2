from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
import inspect, functools
from pathlib import Path

OUT = Path("docs/tech/urls.md")

def first_line(text: str) -> str:
    text = (text or "").strip()
    return text.splitlines()[0] if text else ""

def unwrap(func):
    # peel decorators (csrf_exempt, login_required, etc.)
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func

def view_info(cb):
    """
    Return (display_name, docline, extra) for a URL callback.
    Handles function views, class-based views, DRF viewsets (router).
    """
    extra = ""
    # DRF router endpoints often have .cls and .actions
    cls = getattr(cb, "cls", None)
    actions = getattr(cb, "actions", None)

    # Class-based view via as_view(): callback.view_class exists
    if hasattr(cb, "view_class"):
        cls = getattr(cb, "view_class")

    if cls:
        name = f"{cls.__module__}.{cls.__name__}"
        docline = first_line(inspect.getdoc(cls))
        if actions:  # e.g. {'get': 'list', 'post': 'create'}
            extra = f"[actions: {', '.join(f'{m}->{a}' for m,a in actions.items())}]"
        return name, docline, extra

    # Function-based view
    func = unwrap(cb)
    mod = inspect.getmodule(func)
    modname = mod.__name__ if mod else "(unknown)"
    name = f"{modname}.{getattr(func, '__name__', str(func))}"
    docline = first_line(inspect.getdoc(func))
    return name, docline, extra

class Command(BaseCommand):
    help = "Generate URL map documentation (Markdown)"
    requires_system_checks = []   # don't force full checks
    requires_migrations_checks = False

    def handle(self, *args, **opts):
        lines = ["# URL Map", ""]
        resolver = get_resolver()

        def walk(res, prefix=""):
            for p in res.url_patterns:
                try:
                    if isinstance(p, URLPattern):
                        cb = p.callback
                        name, docline, extra = view_info(cb)
                        route = prefix + str(p.pattern)
                        route_name = p.name or ""
                        ns = getattr(p, "namespace", "") or ""
                        meta = " ".join(x for x in [f"(name: {route_name})" if route_name else "", f"(ns: {ns})" if ns else "", extra] if x)
                        lines.append(f"- `{route}` → **{name}** {meta} — {docline}".rstrip())
                    elif isinstance(p, URLResolver):
                        walk(p, prefix + str(p.pattern))
                except Exception as e:
                    # Never die on a single bad pattern; record it and continue
                    lines.append(f"- `{prefix}{p.pattern}` → *(error reading view: {e})*")

        walk(resolver)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {OUT}"))

