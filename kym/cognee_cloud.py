"""Hosted Cognee Cloud backend (REST). Docs: https://docs.cognee.ai/cognee-cloud/http-api
Env: COGNEE_API_KEY (required), COGNEE_API_URL (tenant base URL, e.g. https://your-tenant.aws.cognee.ai),
optional COGNEE_TENANT_ID, KYM_COGNEE_DATASET (default know-your-members-demo)."""
import json, os, urllib.request
DATASET = os.getenv("KYM_COGNEE_DATASET", "know-your-members-demo")

def available():
    return bool(os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_API_URL"))

def _post(path, body, timeout=60):
    url = os.environ["COGNEE_API_URL"].rstrip("/")
    if not url.endswith("/api/v1"): url += "/api/v1"
    h = {"X-Api-Key": os.environ["COGNEE_API_KEY"], "Content-Type": "application/json"}
    if os.getenv("COGNEE_TENANT_ID"): h["X-Tenant-Id"] = os.environ["COGNEE_TENANT_ID"]
    req = urllib.request.Request(url + path, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")

def _flatten(x):
    """Pull answer text out of whatever result shape the API returns."""
    if x is None: return ""
    if isinstance(x, str): return x
    if isinstance(x, list): return "\n".join(filter(None, (_flatten(i) for i in x)))
    if isinstance(x, dict):
        for k in ("search_result", "result", "answer", "text", "content", "results"):
            if k in x: return _flatten(x[k])
        return json.dumps(x)
    return str(x)

def recall(query):
    ans = _flatten(_post("/recall", {"query": query, "datasets": [DATASET], "include_references": False}))
    return ans.split("Evidence:")[0].strip()

def check():
    recall("ping"); return True

import re, unicodedata
def norm(t):
    """Cloud answers use narrow no-break spaces, ** markdown, and non-ASCII dashes; normalise them."""
    t = unicodedata.normalize("NFKC", t).replace("*", "")
    t = re.sub(r"[\u2010-\u2015]", "-", t)
    return re.sub(r"\s+", " ", t)

def rank_speakers(members, theme, k):
    """Return (ordered member indices, {index: cloud reason})."""
    ans = recall(f"Who could speak on {theme}? List full names, best first, with one reason each.")
    lines = [norm(l) for l in ans.splitlines() if l.strip()]
    flat = norm(ans); pos = {i: flat.find(norm(m["name"])) for i, m in enumerate(members)}
    hits = sorted([i for i, p in pos.items() if p >= 0], key=lambda i: pos[i])[:k]
    reasons = {}
    for i in hits:
        n = norm(members[i]["name"])
        for l in lines:
            if n in l:
                r = l.split(n, 1)[1].strip(" -:,.\u2013")
                if r: reasons[i] = r[0].upper() + r[1:]
                break
    return hits, reasons

def pair_context(a, b):
    return norm(recall(f"Why should {a['name']} and {b['name']} meet, and what could each learn from the other? One sentence."))
