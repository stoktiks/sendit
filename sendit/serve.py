"""Visual web UI for the sender — drag & drop files, get shareable links."""

import os
import json
import mimetypes
import shutil
import tempfile
import threading
import http.server
import secrets
import sys

from ._common import find_free_port, get_local_ip, format_size, escape_html, header_safe_filename, icon_for_ext


UPLOAD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>sendit — share files</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1035 40%, #0d1b2a 100%);
  color: #e0e0e0;
  min-height: 100vh; padding: 20px;
  display: flex; align-items: center; justify-content: center;
}
.card {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 24px; padding: 48px 44px;
  text-align: center; max-width: 520px; width: 100%;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6);
}
h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.subtitle { color: rgba(255,255,255,0.4); font-size: 14px; margin-bottom: 32px; }

/* Drop zone */
#dropzone {
  border: 2px dashed rgba(255,255,255,0.15);
  border-radius: 16px; padding: 48px 24px;
  cursor: pointer; transition: all 0.25s ease;
  background: rgba(255,255,255,0.02);
  margin-bottom: 20px;
}
#dropzone:hover, #dropzone.dragover {
  border-color: #4361ee;
  background: rgba(67,97,238,0.08);
}
#dropzone .icon { font-size: 48px; margin-bottom: 12px; }
#dropzone .text { font-size: 16px; font-weight: 500; }
#dropzone .hint { font-size: 13px; color: rgba(255,255,255,0.3); margin-top: 8px; }
#file-input { display: none; }

/* Upload progress */
#upload-section { display: none; margin-top: 12px; }
#upload-bar-bg {
  width: 100%; height: 6px; background: rgba(255,255,255,0.08);
  border-radius: 3px; overflow: hidden; margin-top: 16px;
}
#upload-bar {
  height: 100%; width: 0%; border-radius: 3px;
  background: linear-gradient(90deg, #4361ee, #7c4dff);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  transition: width 0.15s ease;
}
@keyframes shimmer {
  0%, 100% { background-position: 0% 0; }
  50% { background-position: 100% 0; }
}
#upload-text { margin-top: 8px; font-size: 14px; color: rgba(255,255,255,0.5); }

/* Share section */
#share-section { display: none; margin-top: 4px; }
.share-icon { font-size: 40px; margin-bottom: 8px; }
.share-file { font-size: 15px; font-weight: 500; color: #fff; }
.share-size { font-size: 13px; color: rgba(255,255,255,0.4); margin-bottom: 20px; }
.share-link-wrap {
  display: flex; gap: 8px; margin-bottom: 20px;
}
.share-link-wrap input {
  flex: 1; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05); color: #fff; font-size: 14px;
  font-family: 'SF Mono', 'Fira Code', monospace; outline: none;
}
.share-link-wrap input:focus { border-color: #4361ee; }
.share-link-wrap button {
  padding: 12px 20px; border-radius: 10px; border: none;
  background: #4361ee; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.2s; white-space: nowrap;
}
.share-link-wrap button:hover { background: #3a56d4; }
.share-link-wrap button.copied { background: #43ee90; color: #000; }
.qr-section { margin-bottom: 20px; }
.qr-section img { background: #fff; padding: 8px; border-radius: 10px; width: 120px; height: 120px; }
.share-actions { display: flex; gap: 8px; justify-content: center; }
.share-actions button {
  padding: 10px 24px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.6);
  font-size: 13px; cursor: pointer; transition: all 0.2s;
}
.share-actions button:hover { background: rgba(255,255,255,0.1); color: #fff; }
/* QR code inline (server-side rendered after upload) */
.footer { margin-top: 24px; color: rgba(255,255,255,0.12); font-size: 11px; }
@media (max-width: 480px) {
  .card { padding: 32px 20px; }
  #dropzone { padding: 32px 16px; }
  .share-link-wrap { flex-direction: column; }
}
</style>
</head>
<body>
<div class="card">
  <h1>📤 sendit</h1>
  <p class="subtitle">Drop a file to get a shareable link</p>

  <div id="dropzone" onclick="document.getElementById('file-input').click()">
    <div class="icon">📁</div>
    <div class="text">Drop file here</div>
    <div class="hint">or click to browse</div>
  </div>
  <input type="file" id="file-input" onchange="uploadFile(this.files[0])">

  <div id="upload-section">
    <div id="upload-text">Uploading...</div>
    <div id="upload-bar-bg"><div id="upload-bar"></div></div>
  </div>

  <div id="share-section">
    <div class="share-icon" id="share-icon">📦</div>
    <div class="share-file" id="share-filename"></div>
    <div class="share-size" id="share-filesize"></div>
    <div class="share-link-wrap">
      <input type="text" id="share-url" readonly onclick="this.select()">
      <button id="copy-btn" onclick="copyLink()">Copy</button>
    </div>
    <div class="qr-section" id="qr-section"></div>
    <div class="share-actions">
      <button onclick="resetPage()">📤 Send another</button>
    </div>
  </div>

  <div class="footer">sendit · simple file transfer</div>
</div>

<script>
let uploadXhr = null;

// Drag & drop handlers
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover', function(e) { e.preventDefault(); this.classList.add('dragover'); });
dz.addEventListener('dragleave', function(e) { this.classList.remove('dragover'); });
dz.addEventListener('drop', function(e) {
  e.preventDefault(); this.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

function uploadFile(file) {
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  const section = document.getElementById('upload-section');
  const bar = document.getElementById('upload-bar');
  const txt = document.getElementById('upload-text');
  section.style.display = 'block';
  bar.style.width = '0%';
  txt.textContent = 'Uploading ' + file.name + '...';

  uploadXhr = new XMLHttpRequest();
  uploadXhr.open('POST', '/upload', true);
  uploadXhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      const pct = Math.round(e.loaded / e.total * 100);
      bar.style.width = pct + '%';
      txt.textContent = pct + '% — ' + formatSize(e.loaded) + ' / ' + formatSize(e.total);
    }
  };
  uploadXhr.onload = function() {
    if (uploadXhr.status === 200) {
      const data = JSON.parse(uploadXhr.responseText);
      showShare(file.name, file.size, data.url, data.qr);
    } else {
      txt.textContent = '❌ Upload failed';
    }
  };
  uploadXhr.onerror = function() { txt.textContent = '❌ Upload failed'; };
  uploadXhr.send(form);
}

function showShare(name, size, url, qrDataUrl) {
  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('dropzone').style.display = 'none';
  const sec = document.getElementById('share-section');
  sec.style.display = 'block';

  // Detect icon
  const ext = name.split('.').pop().toLowerCase();
  const icons = {
    jpg:'🖼️',jpeg:'🖼️',png:'🖼️',gif:'🖼️',webp:'🖼️',svg:'🖼️',
    mp4:'🎬',mov:'🎬',avi:'🎬',mkv:'🎬',webm:'🎬',
    mp3:'🎵',wav:'🎵',flac:'🎵',ogg:'🎵',
    zip:'📦',rar:'📦','7z':'📦',tar:'📦',gz:'📦',bz2:'📦',
    pdf:'📄',doc:'📄',docx:'📄',txt:'📝',md:'📝',
    py:'🐍',js:'📜',html:'🌐',css:'🎨',
    exe:'⚙️',dmg:'💿',apk:'📱'
  };
  document.getElementById('share-icon').textContent = icons[ext] || '📦';
  document.getElementById('share-filename').textContent = name;
  document.getElementById('share-filesize').textContent = formatSize(size);
  document.getElementById('share-url').value = url;

  if (qrDataUrl) {
    document.getElementById('qr-section').innerHTML = '<img src="' + qrDataUrl + '" alt="QR">';
  }
}

function copyLink() {
  const input = document.getElementById('share-url');
  const btn = document.getElementById('copy-btn');
  input.select(); navigator.clipboard.writeText(input.value);
  btn.textContent = '✅ Copied!';
  btn.classList.add('copied');
  setTimeout(function() { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
}

function resetPage() {
  document.getElementById('share-section').style.display = 'none';
  document.getElementById('dropzone').style.display = 'block';
  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('upload-bar').style.width = '0%';
  document.getElementById('file-input').value = '';
  document.getElementById('qr-section').innerHTML = '';
}

function formatSize(n) {
  if (n === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(i > 0 ? 1 : 0) + ' ' + units[i];
}
</script>
</body>
</html>"""


def run_web_server(port=0, storage_dir=None):
    """Start a visual web server for uploading and sharing files."""

    if storage_dir is None:
        storage_dir = tempfile.mkdtemp(prefix="sendit_")

    files = {}  # token -> {"path": ..., "name": ..., "size": ...}

    class SenditWebHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send_json(self, code, data):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, code, html_text):
            body = html_text.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _process_upload_stream(self, boundary):
            """Stream multipart upload to a temp file — O(1) memory for the file body.
            Returns (filename, temp_path) or (None, None) on failure.
            """
            boundary_bytes = f"--{boundary}".encode()
            delim = b"\r\n" + boundary_bytes

            buf = bytearray()
            filename = None
            temp = None
            temp_path = None
            state = "header"

            while state != "done":
                chunk = self.rfile.read(65536)
                if chunk:
                    buf.extend(chunk)

                if state == "header":
                    # Find \r\n\r\n — headers are always small, safe to buffer
                    idx = buf.find(b"\r\n\r\n")
                    if idx == -1:
                        if len(buf) > 65536:
                            return None, None  # pathological header, bail
                        if not chunk:
                            return None, None  # connection closed prematurely
                        continue

                    # Parse headers for filename
                    header_block = buf[:idx].decode("utf-8", errors="replace")
                    for line in header_block.split("\r\n"):
                        if 'name="file"' in line and "filename=" in line:
                            fn_start = line.find('filename="')
                            if fn_start != -1:
                                fn_end = line.find('"', fn_start + 10)
                                if fn_end != -1:
                                    filename = line[fn_start + 10:fn_end]
                            break

                    if not filename:
                        return None, None

                    safe_name = os.path.basename(filename)
                    temp = tempfile.NamedTemporaryFile(
                        prefix=f"sendit_", suffix=f"_{safe_name}",
                        dir=storage_dir, delete=False
                    )
                    temp_path = temp.name

                    # Body starts after \r\n\r\n (idx + 4)
                    buf = buf[idx + 4:]
                    state = "body"

                if state == "body":
                    # How many trailing bytes could be part of the boundary marker?
                    # Longest: \r\n--<boundary>--  (boundary up to ~70 chars)
                    max_trail = len(delim) + 2

                    # Look for the closing boundary
                    for end_marker in (delim + b"--", delim):
                        eidx = buf.find(end_marker)
                        if eidx != -1:
                            temp.write(buf[:eidx])
                            temp.close()
                            state = "done"
                            break

                    if state == "done":
                        break

                    # No boundary found yet — write everything except trailing bytes
                    if len(buf) > max_trail:
                        safe = len(buf) - max_trail
                        temp.write(bytearray(buf[:safe]))
                        buf = buf[safe:]

                    if not chunk:
                        # Stream exhausted without finding closing boundary
                        # Write remaining buffer and close
                        temp.write(buf)
                        temp.close()
                        state = "done"
                        break

            if filename and temp_path:
                return filename, temp_path
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            return None, None

        def _read_post_data(self):
            length = int(self.headers.get("Content-Length", 0))
            return self.rfile.read(length)

        def _guess_content_type(self, name):
            guessed, _ = mimetypes.guess_type(name)
            return guessed or "application/octet-stream"

        def _process_upload(self, post_data, boundary):
            """Naive multipart parser — extracts first file."""
            boundary_bytes = b"--" + boundary.encode()
            parts = post_data.split(boundary_bytes)
            for part in parts:
                if b"Content-Disposition" not in part:
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                headers_raw = part[:header_end].decode("utf-8", errors="replace")
                body = part[header_end + 4:]
                # Remove trailing \r\n--
                if body.endswith(b"\r\n"):
                    body = body[:-2]
                if body.endswith(b"--"):
                    body = body[:-2]
                if body.endswith(b"\r\n"):
                    body = body[:-2]

                # Extract filename
                filename = None
                for line in headers_raw.split("\r\n"):
                    if 'name="file"' in line and "filename=" in line:
                        idx = line.find('filename="')
                        if idx != -1:
                            end = line.find('"', idx + 10)
                            filename = line[idx + 10:end]
                        break

                if filename and body:
                    return filename, body
            return None, None

        def _serve_download_page(self, token, info):
            fname = info["name"]
            fsize = info["size"]
            ext = os.path.splitext(fname)[1].lower()
            icon = icon_for_ext(ext)

            html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>sendit — {escape_html(fname)}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1035 40%, #0d1b2a 100%);
  color: #e0e0e0; display:flex; align-items:center; justify-content:center;
  min-height:100vh; padding:20px;
}}
.card {{
  background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
  border:1px solid rgba(255,255,255,0.08); border-radius:24px;
  padding:48px 44px; text-align:center; max-width:440px; width:100%;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6);
}}
.icon-wrap {{ width:80px;height:80px;margin:0 auto 20px;
  background:rgba(67,97,238,0.15);border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  animation:float 3s ease-in-out infinite; }}
.icon-wrap span {{ font-size:36px;line-height:1; }}
@keyframes float {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-6px)}} }}
h1 {{ font-size:22px;font-weight:700;margin-bottom:4px; }}
.subtitle {{ color:rgba(255,255,255,0.4);font-size:13px;margin-bottom:24px; }}
.file-card {{
  background:rgba(255,255,255,0.04);border-radius:14px;padding:16px 20px;margin-bottom:28px;
  border:1px solid rgba(255,255,255,0.06);
}}
.filename {{ color:#fff;font-size:16px;font-weight:500;word-break:break-all; }}
.filesize {{ color:rgba(255,255,255,0.4);font-size:13px;margin-top:4px; }}
#dlbtn {{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;width:100%;
  padding:16px 32px;background:linear-gradient(135deg,#4361ee,#7c4dff);
  color:#fff;border-radius:14px;border:none;font-size:17px;font-weight:600;
  cursor:pointer;transition:all 0.25s ease;
  box-shadow: 0 4px 20px rgba(67,97,238,0.35);
}}
#dlbtn:hover {{ transform:translateY(-2px);box-shadow:0 8px 30px rgba(67,97,238,0.5); }}
#dlbtn:disabled {{ opacity:0.5;cursor:not-allowed;transform:none; }}
#progress-wrap {{ display:none;margin-top:24px; }}
#progress-bar-bg {{ width:100%;height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden; }}
#progress-bar {{ height:100%;width:0%;border-radius:3px;
  background:linear-gradient(90deg,#4361ee,#7c4dff);background-size:200% 100%;
  animation:shimmer 1.5s ease-in-out infinite;transition:width 0.15s ease; }}
@keyframes shimmer {{ 0%,100%{{background-position:0% 0}} 50%{{background-position:100% 0}} }}
#progress-text {{ margin-top:10px;font-size:14px;color:rgba(255,255,255,0.5);
  font-variant-numeric:tabular-nums; }}
#complete-wrap {{ display:none;margin-top:24px; }}
.checkmark {{ width:56px;height:56px;margin:0 auto 12px;
  background:rgba(67,238,144,0.15);border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  animation:pop 0.4s cubic-bezier(0.175,0.885,0.32,1.275); }}
@keyframes pop {{ 0%{{transform:scale(0)}} 100%{{transform:scale(1)}} }}
.checkmark svg {{ width:28px;height:28px; }}
.done-text {{ color:#43ee90;font-size:15px;font-weight:500; }}
.footer {{ margin-top:24px;color:rgba(255,255,255,0.15);font-size:11px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon-wrap"><span>{icon}</span></div>
  <h1>Incoming File</h1>
  <p class="subtitle">ready to download</p>
  <div class="file-card"><div class="filename">{escape_html(fname)}</div><div class="filesize">{format_size(fsize)}</div></div>
  <button id="dlbtn" onclick="startDownload()"><span>⬇</span> Download</button>
  <div id="progress-wrap"><div id="progress-bar-bg"><div id="progress-bar"></div></div><div id="progress-text">Starting...</div></div>
  <div id="complete-wrap"><div class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="#43ee90" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div><div class="done-text">Download complete!</div></div>
  <div class="footer">sendit · simple file transfer</div>
</div>
<script>
async function startDownload() {{
  const btn=document.getElementById('dlbtn');const wrap=document.getElementById('progress-wrap');
  const cw=document.getElementById('complete-wrap');const bar=document.getElementById('progress-bar');
  const txt=document.getElementById('progress-text');
  btn.disabled=true;btn.innerHTML='<span>⏳</span> Preparing...';wrap.style.display='block';
  try {{
    const resp=await fetch('/{token}/download');
    if(!resp.ok) throw new Error('HTTP '+resp.status);
    const total=parseInt(resp.headers.get('content-length')||'0');
    const reader=resp.body.getReader();let loaded=0;const chunks=[];
    while(true){{const {{done,value}}=await reader.read();if(done)break;chunks.push(value);loaded+=value.length;
      if(total>0){{const pct=Math.round(loaded/total*100);bar.style.width=pct+'%';txt.textContent=pct+'% — '+formatSize(loaded)+' / '+formatSize(total);}}
      else{{txt.textContent=formatSize(loaded)+' downloaded';}}
    }}
    bar.style.width='100%';txt.textContent='100% — '+formatSize(total);
    const blob=new Blob(chunks,{{type:resp.headers.get('content-type')||'application/octet-stream'}});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='{escape_html(fname)}';
    document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(a.href);
    wrap.style.display='none';cw.style.display='block';
  }} catch(err){{txt.textContent='❌ '+err.message;bar.style.width='0%';btn.disabled=false;btn.innerHTML='<span>🔄</span> Retry';}}
}}
function formatSize(n){{if(n===0)return'0 B';const units=['B','KB','MB','GB'];let i=0;while(n>=1024&&i<units.length-1){{n/=1024;i++}}return n.toFixed(i>0?1:0)+' '+units[i];}}
</script>
</body>
</html>"""
            self._send_html(200, html_page)

        def do_HEAD(self):
            parsed_path = self.path.strip("/")
            if parsed_path == "":
                # Root path — confirm the page exists
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(UPLOAD_PAGE.encode())))
                self.end_headers()
                return

            parts = parsed_path.split("/")
            token = parts[0]
            path_rest = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""
            is_download = "/download" in path_rest

            if token in files and is_download:
                info = files[token]
                fpath = info["path"]
                try:
                    fsize = os.path.getsize(fpath)
                    self.send_response(200)
                    self.send_header("Content-Type", self._guess_content_type(info["name"]))
                    self.send_header("Content-Length", str(fsize))
                    safe_name = header_safe_filename(info["name"])
                    safe_quoted = urllib.parse.quote(info["name"], safe='')
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{safe_name}"; filename*=UTF-8\x27\x27{safe_quoted}')
                    self.end_headers()
                except Exception:
                    self._send_json(404, {"error": "file not found"})
            else:
                self._send_json(404, {"error": "not found"})

        def do_GET_download(self, token):
            if token not in files:
                self._send_json(404, {"error": "not found"})
                return
            info = files[token]
            fpath = info["path"]
            fname = info["name"]
            try:
                fsize = os.path.getsize(fpath)
                self.send_response(200)
                self.send_header("Content-Type", self._guess_content_type(fname))
                self.send_header("Content-Length", str(fsize))
                safe_name = header_safe_filename(fname)
                safe_quoted = urllib.parse.quote(fname, safe='')
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{safe_name}"; filename*=UTF-8\x27\x27{safe_quoted}')
                self.end_headers()
                with open(fpath, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        def do_GET(self):
            parsed_path = self.path.rstrip("/")
            if parsed_path == "":
                self._send_html(200, UPLOAD_PAGE)
                return

            # /{token} or /{token}/download
            parts = parsed_path.lstrip("/").split("/")
            token = parts[0]
            is_download = len(parts) > 1 and parts[1] == "download"

            if token not in files:
                self._send_json(404, {"error": "file not found"})
                return

            if is_download:
                self.do_GET_download(token)
            else:
                self._serve_download_page(token, files[token])

        def do_POST(self):
            if self.path == "/upload":
                ctype = self.headers.get("Content-Type", "")
                if "boundary=" not in ctype:
                    self._send_json(400, {"error": "missing boundary"})
                    return
                boundary = ctype.split("boundary=")[1].split(";")[0].strip()
                filename, temp_path = self._process_upload_stream(boundary)
                if not filename or not temp_path:
                    self._send_json(400, {"error": "no file received"})
                    return

                # Get file size from temp file
                fsize = os.path.getsize(temp_path)

                safe_name = os.path.basename(filename)
                token = secrets.token_urlsafe(8)
                # Move temp file to final location
                dest = os.path.join(storage_dir, token + "_" + safe_name)
                shutil.move(temp_path, dest)

                files[token] = {
                    "path": dest,
                    "name": safe_name,
                    "size": fsize,
                }

                local_ip = get_local_ip()
                port = self.server.server_address[1]
                dl_url = f"http://{local_ip}:{port}/{token}"

                # Generate QR code data URL
                qr_data_url = ""
                try:
                    import qrcode
                    from io import BytesIO
                    import base64
                    qr = qrcode.QRCode(border=2, box_size=5)
                    qr.add_data(dl_url)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="#4361ee", back_color="#fff")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    qr_data_url = "data:image/png;base64," + b64
                except ImportError:
                    pass

                self._send_json(200, {"url": dl_url, "qr": qr_data_url, "name": safe_name})
            else:
                self._send_json(404, {"error": "not found"})

    listen_port = find_free_port(port)
    server = http.server.HTTPServer(("0.0.0.0", listen_port), SenditWebHandler)

    local_ip = get_local_ip()
    url = f"http://{local_ip}:{listen_port}"

    print(f"\U0001f310 sendit web \u2014 visual file sharing")
    print()
    print(f"\U0001f517 {url}")
    print()
    print(f"Open the link in your browser, drag & drop a file,")
    print(f"and share the generated download link!")
    print()
    print("\u23f3 Server running... (Ctrl+C to stop)")

    # Print QR for the server URL
    try:
        from .qr import print_qr
        print_qr(url)
    except ImportError:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\U0001f44b Stopped.")
    finally:
        server.server_close()
        # Cleanup temp files
        shutil.rmtree(storage_dir, ignore_errors=True)
