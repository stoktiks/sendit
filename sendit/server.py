import http.server
import json
import mimetypes
import os
import secrets
import socket
import sys
import threading
import time
import urllib.parse

from .qr import print_qr


def _find_free_port(preferred=0):
    """Find an available TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", preferred))
        port = s.getsockname()[1]
        return port
    finally:
        s.close()


def _get_local_ip():
    """Get the local IP address (the one used for LAN connectivity)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't actually connect
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _format_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _make_handler(file_path, file_size, file_name, token, shutdown_event):
    """Create a custom HTTP request handler class."""

    class SenditHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # quieter logging
            pass

        def _send_json(self, code, data):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_ui(self):
            """Send a minimal web UI for browser download."""
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>sendit</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f0f0f; color: #e0e0e0;
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
}}
.card {{
  background: #1a1a2e; border-radius: 16px; padding: 48px 40px;
  text-align: center; max-width: 420px; width: 90%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}
.icon {{ font-size: 48px; margin-bottom: 16px; }}
h1 {{ font-size: 24px; margin-bottom: 8px; }}
.filename {{ color: #888; font-size: 16px; margin-bottom: 24px; word-break: break-all; }}
.size {{ color: #666; font-size: 14px; margin-bottom: 32px; }}
a.button {{
  display: inline-block; background: #4361ee; color: #fff;
  padding: 14px 48px; border-radius: 10px; text-decoration: none;
  font-size: 16px; font-weight: 600;
  transition: background 0.2s;
}}
a.button:hover {{ background: #3a56d4; }}
.footer {{ margin-top: 24px; color: #555; font-size: 12px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">📦</div>
  <h1>Incoming File</h1>
  <div class="filename">{_escape_html(file_name)}</div>
  <div class="size">{_format_size(file_size)}</div>
  <a class="button" href="/{token}/download">Download</a>
  <div class="footer">sendit · simple file transfer</div>
</div>
</body>
</html>"""
            body = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path == f"/{token}":
                self._send_ui()
            elif path == f"/{token}/download":
                self._serve_file()
            elif path == "/status":
                self._send_json(200, {"status": "active", "file": file_name})
            else:
                self._send_json(404, {"error": "not found"})

            # Shutdown after delivering the file
            if path == f"/{token}/download":
                shutdown_event.set()

        def _serve_file(self):
            try:
                fsize = os.path.getsize(file_path)
                self.send_response(200)
                guessed, _ = mimetypes.guess_type(file_name)
                self.send_header("Content-Type", guessed or "application/octet-stream")
                self.send_header("Content-Length", str(fsize))
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{_escape_html(file_name)}"')
                self.end_headers()
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        def do_HEAD(self):
            if self.path == f"/{token}/download":
                try:
                    fsize = os.path.getsize(file_path)
                    self.send_response(200)
                    guessed, _ = mimetypes.guess_type(file_name)
                    self.send_header("Content-Type", guessed or "application/octet-stream")
                    self.send_header("Content-Length", str(fsize))
                    self.end_headers()
                except Exception:
                    self._send_json(404, {"error": "file not found"})
            else:
                self._send_json(404, {"error": "not found"})

    return SenditHandler


def _escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def run_server(file_path, port=0, timeout=300):
    """
    Start a temporary HTTP server to serve a single file.
    Returns when the transfer completes or timeout expires.
    """
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    token = secrets.token_urlsafe(8)  # 11-char random token

    shutdown_event = threading.Event()
    handler = _make_handler(file_path, file_size, file_name, token, shutdown_event)

    listen_port = _find_free_port(port)
    server = http.server.HTTPServer(("0.0.0.0", listen_port), handler)
    server.timeout = 1.0  # check shutdown every second

    local_ip = _get_local_ip()
    url = f"http://{local_ip}:{listen_port}/{token}"

    print(f"📦 sendit — {file_name}")
    print(f"📏 Size: {_format_size(file_size)}")
    print()
    print(f"🔗 {url}")
    print_qr(url)
    print(f"Receiver opens that link in their browser, or runs:")
    print(f"   sendit get {url}")
    print()
    print("⏳ Waiting for download... (Ctrl+C to cancel)")

    start = time.time()
    try:
        while not shutdown_event.is_set():
            server.handle_request()
            if time.time() - start > timeout:
                print("\n⏰ Timed out waiting for transfer.")
                break
    except KeyboardInterrupt:
        print("\n🚫 Cancelled.")
    finally:
        server.server_close()

    if shutdown_event.is_set():
        elapsed = time.time() - start
        print(f"\n✅ Sent! ({elapsed:.1f}s)")
