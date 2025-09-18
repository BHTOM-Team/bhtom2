# bhtomdocsbot/management/commands/gen_docs_forms.py
from django.core.management.base import BaseCommand
from importlib import import_module
from pathlib import Path
from django import forms
from django.contrib.auth import get_user_model

OUT_DIR = Path("docs/ui")

# 👉 Fill this with dotted paths and titles you want documented
FORMS = [
    ("bhtom2.bhtom_dataproducts.forms.DataProductUploadForm", "Upload Data Products"),
    # Add more, e.g. ("bhtom2.bhtom_targets.forms.TargetCreateForm", "Create a Target"),
]

class Command(BaseCommand):
    help = "Generate Markdown tables for listed forms"
    requires_system_checks = []  # keep it lightweight
    requires_migrations_checks = False

    def _instantiate(self, cls):
        """
        Try common instantiation patterns used in BHTOM forms.
        """
        # First try bare
        try:
            return cls()
        except Exception:
            pass

        # If it needs initial user/users (e.g., DataProductUploadForm)
        try:
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_active=True).first()
            users = User.objects.filter(is_active=True)
            if user is not None:
                return cls(initial={"user": user, "users": users})
        except Exception:
            pass

        # Last resort: empty initial
        try:
            return cls(initial={})
        except Exception as e:
            raise e

    def handle(self, *args, **opts):
        if not FORMS:
            self.stdout.write(self.style.WARNING("FORMS list is empty — nothing to generate."))
            return

        OUT_DIR.mkdir(parents=True, exist_ok=True)

        for dotted, title in FORMS:
            try:
                mod_path, cls_name = dotted.rsplit(".", 1)
                cls = getattr(import_module(mod_path), cls_name)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Import failed {dotted}: {e}"))
                continue

            try:
                form = self._instantiate(cls)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Could not instantiate {dotted}: {e}"))
                continue

            lines = [
                f"# {title}",
                "",
                f"*Form class:* `{dotted}`",
                "",
                "| Field | Type | Required | Choices | Help |",
                "|------|------|----------|---------|------|",
            ]

            for name, field in form.fields.items():
                ftype = field.__class__.__name__
                req = "yes" if field.required else "no"
                help_txt = (field.help_text or "").replace("|", "\\|").replace("\n", " ")
                choices = ""
                if getattr(field, "choices", None):
                    ch = list(field.choices)
                    # show up to 6 human-friendly labels
                    labels = []
                    for c in ch[:6]:
                        if isinstance(c, (list, tuple)) and len(c) >= 2:
                            labels.append(str(c[1]))
                        else:
                            labels.append(str(getattr(c, "label", c)))
                    choices = ", ".join(labels)
                    if len(ch) > 6:
                        choices += " …"
                    choices = choices.replace("|", "\\|")
                lines.append(f"| **{name}** | {ftype} | {req} | {choices} | {help_txt} |")

            out = OUT_DIR / (cls_name + ".md")
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {out}"))

        self.stdout.write(self.style.SUCCESS("Done."))

