#!/usr/bin/env python3
"""Simple HTTP server for Memex architecture visualizations."""
import http.server
import os
import sys

PORT = 5555
DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    with http.server.HTTPServer(("", port), Handler) as httpd:
        print(f"\n  Memex Architecture Visualizations")
        print(f"  http://localhost:{port}\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Shutting down.")
