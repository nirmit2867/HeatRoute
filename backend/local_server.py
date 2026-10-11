"""Local dev server: serves the frontend and runs the Lambda handlers at /api/*. Usage: python backend/local_server.py"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "lambda"))
from explain_route.handler import lambda_handler as explain  # noqa: E402
from route_score.handler import lambda_handler as route  # noqa: E402

ROUTES = {"/api/route": route, "/api/explain": explain}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(ROOT, "..", "frontend", "public"), **k)

    def do_POST(self):
        fn = ROUTES.get(self.path)
        if not fn:
            return self.send_error(404)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        r = fn({"body": body}, None)
        data = r["body"].encode()
        self.send_response(r["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print("HeatRoute running at http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
