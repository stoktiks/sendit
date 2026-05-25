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
            """Send a polished web UI for browser download."""
            # Choose an icon based on file type
            ext = os.path.splitext(file_name)[1].lower()
            icon_map = {
                ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
                ".webp": "🖼️", ".svg": "🖼️", ".ico": "🖼️",
                ".mp4": "🎬", ".mov": "🎬", ".avi": "🎬", ".mkv": "🎬",
                ".webm": "🎬",
                ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".ogg": "🎵",
                ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦",
                ".gz": "📦", ".bz2": "📦",
                ".pdf": "📄", ".doc": "📄", ".docx": "📄",
                ".txt": "📝", ".md": "📝",
                ".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨",
                ".exe": "⚙️", ".dmg": "💿", ".apk": "📱",
                ".json": "📋", ".yaml": "📋", ".yml": "📋",
                ".csv": "📊", ".xls": "📊", ".xlsx": "📊",
            }
            icon = icon_map.get(ext, "📦")

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>sendit — {_escape_html(file_name)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1035 40%, #0d1b2a 100%);
  color: #e0e0e0;
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; padding: 20px;
}}
.card {{
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 24px; padding: 48px 44px;
  text-align: center; max-width: 440px; width: 100%;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6);
}}
.icon-wrap {{
  width: 80px; height: 80px; margin: 0 auto 20px;
  background: rgba(67,97,238,0.15); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  animation: float 3s ease-in-out infinite;
}}
.icon-wrap .icon {{ font-size: 36px; line-height: 1; }}
@keyframes float {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-6px); }}
}}
h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
.subtitle {{ color: rgba(255,255,255,0.4); font-size: 13px; margin-bottom: 24px; }}
.file-card {{
  background: rgba(255,255,255,0.04);
  border-radius: 14px; padding: 16px 20px; margin-bottom: 28px;
  border: 1px solid rgba(255,255,255,0.06);
}}
.filename {{ color: #fff; font-size: 16px; font-weight: 500; word-break: break-all; }}
.filesize {{ color: rgba(255,255,255,0.4); font-size: 13px; margin-top: 4px; }}
.btn-wrap {{ position: relative; }}
#dlbtn {{
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; padding: 16px 32px;
  background: linear-gradient(135deg, #4361ee, #7c4dff);
  color: #fff; border-radius: 14px; border: none;
  font-size: 17px; font-weight: 600; cursor: pointer;
  transition: all 0.25s ease; text-decoration: none;
  box-shadow: 0 4px 20px rgba(67,97,238,0.35);
}}
#dlbtn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(67,97,238,0.5); }}
#dlbtn:active {{ transform: translateY(0); }}
#dlbtn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}
#progress-wrap {{ display: none; margin-top: 24px; }}
#progress-bar-bg {{
  width: 100%; height: 6px; background: rgba(255,255,255,0.08);
  border-radius: 3px; overflow: hidden;
}}
#progress-bar {{
  height: 100%; width: 0%; border-radius: 3px;
  background: linear-gradient(90deg, #4361ee, #7c4dff);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  transition: width 0.15s ease;
}}
@keyframes shimmer {{
  0%, 100% {{ background-position: 0% 0; }}
  50% {{ background-position: 100% 0; }}
}}
#progress-text {{ margin-top: 10px; font-size: 14px; color: rgba(255,255,255,0.5);
  font-variant-numeric: tabular-nums; }}
#complete-wrap {{ display: none; margin-top: 24px; }}
.checkmark {{
  width: 56px; height: 56px; margin: 0 auto 12px;
  background: rgba(67,238,144,0.15); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  animation: pop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}
@keyframes pop {{
  0% {{ transform: scale(0); }}
  100% {{ transform: scale(1); }}
}}
.checkmark svg {{ width: 28px; height: 28px; }}
.done-text {{ color: #43ee90; font-size: 15px; font-weight: 500; }}
.auto-note {{ color: rgba(255,255,255,0.3); font-size: 12px; margin-top: 16px; }}
.qr-section {{ margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); }}
.qr-label {{ font-size: 12px; color: rgba(255,255,255,0.3); margin-bottom: 12px; }}
.qr-img {{ display: inline-block; background: #fff; padding: 8px; border-radius: 10px; }}
.qr-img img {{ width: 100px; height: 100px; display: block; }}
.footer {{ margin-top: 24px; color: rgba(255,255,255,0.15); font-size: 11px; }}
@media (max-width: 480px) {{
  .card {{ padding: 32px 24px; }}
  #dlbtn {{ font-size: 15px; padding: 14px 24px; }}
}}
</style>
</head>
<body>
<div class="card">
  <div class="icon-wrap"><span class="icon">{icon}</span></div>
  <h1>Incoming File</h1>
  <p class="subtitle">ready to download</p>

  <div class="file-card">
    <div class="filename">{_escape_html(file_name)}</div>
    <div class="filesize">{_format_size(file_size)}</div>
  </div>

  <button id="dlbtn" onclick="startDownload()">
    <span>⬇</span> Download
  </button>

  <div id="progress-wrap">
    <div id="progress-bar-bg"><div id="progress-bar"></div></div>
    <div id="progress-text">Starting...</div>
  </div>

  <div id="complete-wrap">
    <div class="checkmark">
      <svg viewBox="0 0 24 24" fill="none" stroke="#43ee90" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </div>
    <div class="done-text">Download complete!</div>
  </div>

  <div class="footer">sendit · simple file transfer</div>
</div>
<script>
async function startDownload() {{
  const btn = document.getElementById('dlbtn');
  const wrap = document.getElementById('progress-wrap');
  const cwrap = document.getElementById('complete-wrap');
  const bar = document.getElementById('progress-bar');
  const txt = document.getElementById('progress-text');
  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span> Preparing...';
  wrap.style.display = 'block';
  try {{
    // Fetch via AJAX for progress tracking
    const resp = await fetch('/{token}/download');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const total = parseInt(resp.headers.get('content-length') || '0');
    const reader = resp.body.getReader();
    let loaded = 0;
    const chunks = [];
    while (true) {{
      const {{done, value}} = await reader.read();
      if (done) break;
      chunks.push(value);
      loaded += value.length;
      if (total > 0) {{
        const pct = Math.round(loaded / total * 100);
        bar.style.width = pct + '%';
        txt.textContent = pct + '% — ' + formatSize(loaded) + ' / ' + formatSize(total);
      }} else {{
        txt.textContent = formatSize(loaded) + ' downloaded';
      }}
    }}
    bar.style.width = '100%';
    txt.textContent = '100% — ' + formatSize(total);
    // Save file
    const blob = new Blob(chunks, {{type: resp.headers.get('content-type') || 'application/octet-stream'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{_escape_html(file_name)}';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    // Show completion
    wrap.style.display = 'none';
    cwrap.style.display = 'block';
  }} catch(err) {{
    txt.textContent = '❌ ' + err.message;
    bar.style.width = '0%';
    btn.disabled = false;
    btn.innerHTML = '<span>🔄</span> Retry';
  }}
}}
function formatSize(n) {{
  if (n === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) {{ n /= 1024; i++; }}
  return n.toFixed(i > 0 ? 1 : 0) + ' ' + units[i];
}}
</script>
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
