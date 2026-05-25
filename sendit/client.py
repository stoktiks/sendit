import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from .progress import Progress


def _format_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _parse_url(url):
    """Parse a sendit URL and return (base_url, token)."""
    url = url.strip().rstrip("/")

    # If just a token was given, error out (need full URL for now)
    if re.match(r"^[a-zA-Z0-9_-]{8,16}$", url):
        print("❌ Provide the full URL, not just the token.")
        print("   Ask the sender for the full URL like: http://192.168.1.5:9876/token")
        sys.exit(1)

    # Normalize: add http:// if missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    # Remove trailing /download if present
    if url.endswith("/download"):
        url = url[:-9]

    return url


def run_client(url, output=None):
    """Download a file from a sendit URL."""
    base = _parse_url(url)
    download_url = base + "/download"

    # HEAD request to get file info
    try:
        req = urllib.request.Request(download_url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        content_length = resp.headers.get("Content-Length")
        content_disposition = resp.headers.get("Content-Disposition", "")
        file_size = int(content_length) if content_length else 0

        # Extract filename from Content-Disposition
        # Prefer filename* (RFC 5987 UTF-8), fall back to filename=
        file_name = None
        if content_disposition:
            # Try filename*=UTF-8''<encoded>
            m = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition, re.I)
            if m:
                file_name = urllib.parse.unquote(m.group(1))
            else:
                m = re.search(r'filename="?([^";\n]+)"?', content_disposition)
                if m:
                    file_name = m.group(1)
    except urllib.error.HTTPError as e:
        print(f"❌ Server returned {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Could not connect: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    if not file_name:
        file_name = output or "downloaded_file"

    if output:
        file_name = output

    # Download
    print(f"📥 Receiving: {file_name}")
    if file_size:
        print(f"📏 Size: {_format_size(file_size)}")

    try:
        req = urllib.request.Request(download_url)
        resp = urllib.request.urlopen(req, timeout=300)
        total = 0
        prog = Progress(file_size) if file_size else None
        with open(file_name, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
                if prog:
                    prog.update(total)
        if prog:
            prog.done()
        print(f"✅ Saved to ./{file_name}")
    except urllib.error.HTTPError as e:
        print(f"\n❌ Server returned {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n❌ Connection lost: {e.reason}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🚫 Cancelled.")
        sys.exit(1)
