"""Run python3 app.py, then open http://127.0.0.1:8765."""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from core import read_csv, process, export

ROOT = Path(__file__).parent

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log article contents, titles, URLs or prompts.

    def send(self, status, body, mime):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:8765', 'localhost:8765'):
            return self.send(403, 'Invalid host', 'text/plain')
        if self.path == '/':
            self.send(200, (ROOT / 'index.html').read_text(), 'text/html')
        elif self.path == '/sample.csv':
            self.send(200, (ROOT / 'data/readings.csv').read_text(), 'text/csv')
        else:
            self.send(404, 'Not found', 'text/plain')

    def do_POST(self):
        if self.headers.get('Origin') not in ('http://127.0.0.1:8765', 'http://localhost:8765') or self.headers.get('Host') not in ('127.0.0.1:8765', 'localhost:8765'):
            return self.send(403, 'Local same-origin requests required', 'text/plain')
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 2_000_000:
                raise ValueError('Upload must be under 2 MB.')
            request = json.loads(self.rfile.read(length))
            if self.path == '/summarize':
                rows = read_csv(request['csv'])
                if request.get('demo') and any(not r['text'] for r in rows):
                    raise ValueError('Demo needs text in every row. Use the built-in dataset.')
                results = process(rows, request.get('model') or 'llama3.2:3b',
                                  request.get('fetch') is True, request.get('demo') is True)
                self.send(200, json.dumps({'results': results, 'markdown': export(results),
                                          'html': export(results, 'html')}), 'application/json')
            else:
                self.send(404, 'Not found', 'text/plain')
        except (ValueError, KeyError, TypeError):
            self.send(400, json.dumps({'error': 'Invalid input. Use CSV with a url column, 1–25 readings, under 2 MB. Demo requires text.'}), 'application/json')

if __name__ == '__main__':
    print('Article Study Flow: http://127.0.0.1:8765 — Ctrl+C to stop')
    HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
