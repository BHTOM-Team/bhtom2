# bhtomdocsbot/management/commands/gen_docs_models.py
from django.core.management.base import BaseCommand
from django.apps import apps
from pathlib import Path
from django.db.models.fields import NOT_PROVIDED

OUT = Path("docs/tech/models.md")

# Only include your apps (adjust as needed)
INCLUDE_PREFIXES = ("bhtom2.", "bhtom_base.", "bhtom_custom_registration.")

def safe(s):
    try:
        return ("" if s is None else str(s)).replace("|", "\\|").replace("\n", " ")
    except Exception:
        return ""

def field_type(f):
    try:
        return getattr(f, "get_internal_type", lambda: f.__class__.__name__)()
    except Exception:
        return f.__class__.__name__

def is_reverse(f):
    # reverse relations are auto_created and not concrete
    return getattr(f, "auto_created", False) and not getattr(f, "concrete", True)

def field_row(f):
    try:
        name = f.name
    except Exception:
        name = getattr(f, "attname", "<unknown>")

    ftype = field_type(f)
    null  = getattr(f, "null", "")
    blank = getattr(f, "blank", "")
    unique = getattr(f, "unique", "")
    db_index = getattr(f, "db_index", "")

    # default value display
    default = getattr(f, "default", NOT_PROVIDED)
    if default is NOT_PROVIDED:
        default = ""
    elif callable(default):
        default = "<callable>"
    default = safe(default)

    # choices summary
    choices = ""
    try:
        ch = getattr(f, "choices", None)
        if ch:
            labels = []
            for c in list(ch)[:6]:
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    labels.append(str(c[1]))
                else:
                    labels.append(str(c))
            choices = ", ".join(labels) + (" …" if len(list(ch)) > 6 else "")
    except Exception:
        pass

    help_txt = safe(getattr(f, "help_text", ""))

    # relations
    rel = ""
    try:
        if getattr(f, "is_relation", False) and getattr(f, "remote_field", None):
            target = f.remote_field.model
            target_label = getattr(target, "_meta", None) and target._meta.label or str(target)
            rel = f"→ {target_label}"
            if getattr(f, "many_to_many", False):
                rel = "M2M " + rel
            elif getattr(f, "many_to_one", False):
                rel = "FK " + rel
            elif getattr(f, "one_to_one", False):
                rel = "O2O " + rel
    except Exception:
        pass

    return [
        f"**{name}**",
        ftype,
        safe(rel),
        str(null),
        str(blank),
        str(unique),
        str(db_index),
        default,
        safe(choices),
        help_txt,
    ]

class Command(BaseCommand):
    help = "Generate models overview (Markdown) for BHTOM apps"
    requires_system_checks = []
    requires_migrations_checks = False

    def handle(self, *args, **opts):
        lines = [
            "# Models",
            "",
            "_Auto-generated from Django models. Only concrete (non-reverse) fields are listed._",
            "",
        ]

        for model in apps.get_models():
            mod = model.__module__
            if not mod.startswith(INCLUDE_PREFIXES):
                continue

            try:
                label = model._meta.label
            except Exception:
                continue

            lines.append(f"## {label}")
            doc = safe(getattr(model, "__doc__", "")).strip()
            if doc:
                lines.append(doc)
            lines += [
                "",
                "| Field | Type | Relation | Null | Blank | Unique | Indexed | Default | Choices | Help |",
                "|------|------|----------|------|-------|--------|---------|---------|---------|------|",
            ]

            for f in model._meta.get_fields():
                # skip reverse/auto-created and private fields
                if is_reverse(f) or getattr(f, "private_only", False):
                    continue
                try:
                    lines.append("| " + " | ".join(field_row(f)) + " |")
                except Exception as e:
                    lines.append(f"| _(error on field)_ | {safe(f)} |  |  |  |  |  |  |  | {safe(e)} |")

            lines.append("")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {OUT}"))

