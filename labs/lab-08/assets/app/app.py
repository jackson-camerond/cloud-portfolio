#!/usr/bin/env python3
"""Tiny stdlib-only web app for Lab 08 -- End-to-End CI/CD Pipeline.

No framework, no dependencies. The point of this lab is the pipeline that
builds, scans, and ships this container -- not the app riding inside it.
"""
import json
import os
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_VERSION = os.environ.get("APP_VERSION", "v2")
PORT = int(os.environ.get("PORT", "8080"))


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            # The ALB target group hits this. 200 = healthy, nothing else.
            self._json(200, {"status": "ok"})
            return

        self._json(
            200,
            {
                "message": "shipped by the pipeline, not by hand",
                "version": APP_VERSION,
                "host": socket.gethostname(),
                "time": datetime.now(timezone.utc).isoformat(),
            },
        )

    def log_message(self, fmt, *args):
        # Plain stdout -- the ECS awslogs driver picks this up as-is.
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"listening on :{PORT}, version={APP_VERSION}", flush=True)
    server.serve_forever()
