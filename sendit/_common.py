"""Shared utility functions for sendit — avoids duplication between server.py and serve.py."""

import os
import socket


def find_free_port(preferred=0):
    """Find an available TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", preferred))
        port = s.getsockname()[1]
        return port
    finally:
        s.close()


def get_local_ip():
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


def format_size(n):
    """Format byte count as human-readable string (B/KB/MB/GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            decimals = 0 if unit == "B" else 1
            return f"{n:.{decimals}f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def escape_html(s):
    """Escape text for safe embedding in HTML."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def header_safe_filename(name):
    """Escape a filename for safe use in Content-Disposition HTTP header.
    Strips control chars and backslash-escapes quotes (prevents header injection)."""
    name = "".join(c for c in name if c not in ("\r", "\n") and ord(c) >= 32)
    name = name.replace("\\", "\\\\")
    name = name.replace('"', '\\"')
    return name


# Icon map for file extensions (shared by both sender and receiver UI)
FILE_ICONS = {
    ".jpg": "\U0001f5bc\ufe0f", ".jpeg": "\U0001f5bc\ufe0f", ".png": "\U0001f5bc\ufe0f", ".gif": "\U0001f5bc\ufe0f",
    ".webp": "\U0001f5bc\ufe0f", ".svg": "\U0001f5bc\ufe0f", ".ico": "\U0001f5bc\ufe0f",
    ".mp4": "\U0001f3ac", ".mov": "\U0001f3ac", ".avi": "\U0001f3ac", ".mkv": "\U0001f3ac",
    ".webm": "\U0001f3ac",
    ".mp3": "\U0001f3b5", ".wav": "\U0001f3b5", ".flac": "\U0001f3b5", ".ogg": "\U0001f3b5",
    ".zip": "\U0001f4e6", ".rar": "\U0001f4e6", ".7z": "\U0001f4e6", ".tar": "\U0001f4e6",
    ".gz": "\U0001f4e6", ".bz2": "\U0001f4e6",
    ".pdf": "\U0001f4c4", ".doc": "\U0001f4c4", ".docx": "\U0001f4c4",
    ".txt": "\U0001f4dd", ".md": "\U0001f4dd",
    ".py": "\U0001f40d", ".js": "\U0001f4dc", ".html": "\U0001f310", ".css": "\U0001f3a8",
    ".exe": "\u2699\ufe0f", ".dmg": "\U0001f4bf", ".apk": "\U0001f4f1",
    ".json": "\U0001f4cb", ".yaml": "\U0001f4cb", ".yml": "\U0001f4cb",
    ".csv": "\U0001f4ca", ".xls": "\U0001f4ca", ".xlsx": "\U0001f4ca",
}


def icon_for_ext(ext):
    """Get the emoji icon for a file extension."""
    return FILE_ICONS.get(ext.lower(), "\U0001f4e6")
