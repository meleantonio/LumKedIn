from http.server import BaseHTTPRequestHandler
from api._shared import handle
def run(m, b): return {}
class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self, run)
    def do_GET(self): handle(self, run)
