import os, json, requests
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from openai import OpenAI

DOC_DIR = Path("bhtom_docs")
STATE_FILE = Path("bhtomdocs_state.json")

# Start with a few key docs (add more URLs as needed)
DOC_URLS = [
    "https://raw.githubusercontent.com/BHTOM-Team/bhtom2/bhtom2-dev/Documentation/DocumentationAPI.md",
    # Add more files here as you grow coverage:
    # "https://raw.githubusercontent.com/BHTOM-Team/bhtom2/bhtom2-dev/Documentation/Installation.md",
    # "https://raw.githubusercontent.com/BHTOM-Team/bhtom2/bhtom2-dev/Documentation/UsageGuide.md",
]

ASSISTANT_INSTRUCTIONS = (
"You are the BHTOM docs assistant."
"- Answer in **Markdown** with short sections, lists, and code fences."
"- Use exact UI field labels in **bold**."
"- When you cite docs, add a final '### Sources' list with filenames."
"- If something isn't documented, say so briefly."
)

class Command(BaseCommand):
    help = "Upload BHTOM docs to a vector store and attach them to the existing Assistant"
    requires_system_checks = []      # or ()  ← both are fine
    requires_migrations_checks = False

    def handle(self, *args, **opts):
        api_key = settings.OPENAI_API_KEY
        asst_id = settings.BHTOM_ASSISTANT_ID
        if not api_key:  # safety checks
            self.stderr.write(self.style.ERROR("OPENAI_API_KEY not set"))
            return
        if not asst_id:
            self.stderr.write(self.style.ERROR("BHTOM_ASSISTANT_ID not set"))
            return

        client = OpenAI(api_key=api_key)
        DOC_DIR.mkdir(exist_ok=True)

        # 1) Download docs
        self.stdout.write("Downloading docs…")
        local_files = []
        for url in DOC_URLS:
            fn = DOC_DIR / url.split("/")[-1]
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            fn.write_bytes(r.content)
            local_files.append(fn)

        # 2) Load saved state if present
        state = {}
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text())

        # 3) Create or reuse vector store
        vector_store_id = state.get("vector_store_id")
        if vector_store_id:
            self.stdout.write(f"Reusing vector store: {vector_store_id}")
        else:
            vs = client.vector_stores.create(name="BHTOM Docs")
            vector_store_id = vs.id
            state["vector_store_id"] = vector_store_id
            self.stdout.write(f"Created vector store: {vector_store_id}")

        # 4) Upload files **directly** to the vector store (no pre-upload to /files)
        self.stdout.write("Uploading files to vector store…")
        file_handles = [open(str(p), "rb") for p in local_files]
        try:
            client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=file_handles,   # <-- pass open file handles here
            )
        finally:
            for fh in file_handles:
                try:
                    fh.close()
                except Exception:
                    pass
                
        # 5) Attach vector store to your existing Assistant + refresh instructions
        client.beta.assistants.update(
            assistant_id=asst_id,
            instructions=ASSISTANT_INSTRUCTIONS,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )


        # 6) Save state & print
        STATE_FILE.write_text(json.dumps(state, indent=2))
        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(self.style.SUCCESS(f"VECTOR_STORE_ID={vector_store_id}"))
        self.stdout.write(self.style.SUCCESS(f"ASSISTANT_ID={asst_id}"))
