import os, sys, json, tempfile, time
os.environ.setdefault("KYM_DB", "/tmp/kym.sqlite")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from kym.core import load_members, Matcher  # noqa: E402
SAMPLE = os.path.join(ROOT, "data", "sample_members.csv")
LUMA = os.path.join(ROOT, "data", "private", "luma-eveur09a.csv")  # deploy-only, gitignored, uploaded via vercel CLI
SETS = {"luma": (LUMA, "luma-eveur09a", "Grok Bot London hackathon"),
        "sample": (SAMPLE, "know-your-members-demo", "Generative AI in Economics Teaching CoP (fictional)")}
_cache = {}

def matcher(body):
    """Public demo: fictional sample data by default, or the visitor's own uploaded CSV (never stored)."""
    csv_text = (body.get("csv") or "").strip()
    if csv_text:
        if len(csv_text) > 500_000: raise ValueError("CSV too large (max 500 KB)")
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, dir="/tmp"); f.write(csv_text); f.close()
        os.environ["KYM_DB"] = f.name + ".sqlite"
        try: members = load_members(f.name)
        finally: os.unlink(f.name)
        if not members: raise ValueError("No rows with a 'name' column found")
        os.environ["KYM_COMMUNITY"] = "your community"
        m = Matcher(members, "tfidf"); m.ds = "upload"; m.comm = "your uploaded CSV"; return m  # uploaded data never goes to Cognee
    ds = body.get("dataset") or ("luma" if os.path.exists(LUMA) else "sample")
    if ds not in SETS: ds = "sample"
    path, cds, comm = SETS[ds]
    from kym import cognee_cloud as cc
    cc.set_dataset(cds); os.environ["KYM_COMMUNITY"] = comm
    if ds not in _cache:
        os.environ["KYM_DB"] = f"/tmp/kym-{ds}.sqlite"
        be = "cognee-cloud" if os.getenv("COGNEE_API_URL") and os.getenv("COGNEE_API_KEY") else "tfidf"
        _cache[ds] = Matcher(load_members(path), be); _cache[ds].ds = ds; _cache[ds].comm = comm
    return _cache[ds]

def handle(h, fn):
    try:
        n = int(h.headers.get("content-length") or 0)
        body = json.loads(h.rfile.read(n) or b"{}") if n else {}
        t = time.time(); m = matcher(body)
        out = {"backend": m.backend, "note": m.backend_note, "count": len(m.m), "dataset": getattr(m, "ds", ""), "community": getattr(m, "comm", ""), "members": m.m, **fn(m, body)}
        out["seconds"] = round(time.time() - t, 2); code = 200
    except Exception as e:
        out, code = {"error": str(e)}, 400
    data = json.dumps(out).encode()
    h.send_response(code); h.send_header("Content-Type", "application/json"); h.send_header("Content-Length", str(len(data))); h.end_headers(); h.wfile.write(data)
