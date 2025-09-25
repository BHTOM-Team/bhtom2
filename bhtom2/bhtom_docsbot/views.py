# bhtomdocsbot/views.py
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI


def _client():
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def _has_new_surface(c):
    return hasattr(c, "threads") and hasattr(c, "assistants")

@csrf_exempt
def chat_start(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    c = _client()
    th = c.threads.create() if _has_new_surface(c) else c.beta.threads.create()
    return JsonResponse({"thread_id": th.id})

@csrf_exempt
def chat_message(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        body = json.loads(request.body or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    thread_id = body.get("thread_id")
    message = (body.get("message") or "").strip()
    asst_id  = settings.BHTOM_ASSISTANT_ID

    if not thread_id or not message:
        return HttpResponseBadRequest("thread_id and message are required")
    if not asst_id:
        return JsonResponse({"error":"Assistant not configured"}, status=500)

    c = _client()
    if _has_new_surface(c):
        c.threads.messages.create(thread_id=thread_id, role="user", content=message)
        c.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=asst_id)
        msgs = c.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    else:
        c.beta.threads.messages.create(thread_id=thread_id, role="user", content=message)
        c.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=asst_id)
        msgs = c.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)

    # Pull the latest assistant reply + collect file citations
    answer, file_ids = "", []
    if msgs.data:
        m = msgs.data[0]
        for block in getattr(m, "content", []):
            if getattr(block, "type", None) == "text":
                answer += block.text.value
                for ann in getattr(block.text, "annotations", []) or []:
                    if getattr(ann, "type", None) == "file_citation":
                        file_ids.append(ann.file_citation.file_id)

    # Map file_ids -> filenames (best effort)
    names = []
    for fid in file_ids:
        try:
            f = c.files.retrieve(fid)
            names.append(getattr(f, "filename", None) or fid)
        except Exception:
            names.append(fid)

    return JsonResponse({"answer": answer or "(no response)", "citations": names})
