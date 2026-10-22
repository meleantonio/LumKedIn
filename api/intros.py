from http.server import BaseHTTPRequestHandler
from api._shared import handle
def run(m, b): return {"results": m.intros(max(1, min(int(b.get("k") or 5), 10)))}
class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self, run)
    def do_GET(self): handle(self, run)
