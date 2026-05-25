# sendit

**Zero-dependency file transfer. Share files between any devices — the receiver just needs a browser.**

[![Release](https://img.shields.io/github/v/release/stoktiks/sendit)](https://github.com/stoktiks/sendit/releases)
[![Downloads](https://img.shields.io/github/downloads/stoktiks/sendit/total)](https://github.com/stoktiks/sendit/releases)

---

## Install

### 📱 Android (Termux)

```bash
pkg install python git
git clone https://github.com/stoktiks/sendit.git
cd sendit
pip install -e .
```

**Or download the portable `.pyz`** (just needs Python):

```bash
# Download from releases
chmod +x sendit.pyz
./sendit.pyz web
```

### 🐍 Python (any OS)

```bash
git clone https://github.com/stoktiks/sendit.git
cd sendit
pip install -e .
```

### 📦 Standalone binary (no Python required)

Download from [Releases](https://github.com/stoktiks/sendit/releases):

| Platform | Binary |
|----------|--------|
| Linux x86_64 | `sendit-linux-x86_64` |
| **Linux ARM64** (Android/RPi) | **`sendit-linux-arm64`** |
| macOS | `sendit-darwin-arm64` |
| Windows | `sendit-windows-x86_64.exe` |
| **Any device with Python 3.8+** | **`sendit.pyz`** |

```bash
# Linux/macOS
chmod +x sendit-linux-x86_64
./sendit-linux-x86_64 web

# Android/Termux (ARM64)
chmod +x sendit-linux-arm64
./sendit-linux-arm64 web

# Windows
sendit-windows-x86_64.exe web

# Portable (any OS with Python)
python sendit.pyz web
```

---

## 3 Commands at a Glance

```bash
sendit web             # drag & drop in browser → shareable link
sendit send ./file     # terminal + QR code sender
sendit get <url>       # CLI download with progress bar
```

### `sendit web` — visual drag & drop

```bash
sendit web            # share files from your browser
sendit web 8080       # use a specific port
```

Open the URL in your browser, drag & drop a file, and share the generated link. **Receiver opens the link in any browser** — no install needed.

### `sendit send` — fast CLI sender

```bash
sendit send ./video.mp4         # share any file
sendit send ./file.zip --port 9000
```

Shows a QR code + URL in the terminal. Receiver scans or opens the link.

### `sendit get` — download via CLI

```bash
sendit get http://192.168.1.5:9876/a3b2c1
sendit get http://192.168.1.5:9876/a3b2c1 -o myfile.zip
```

Shows a live progress bar with speed & ETA.

---

## Features

- **📱 QR codes** — scan with your phone, no typing
- **📊 Progress bar** — speed & ETA in both terminal and browser
- **🔒 Random token** — protects each file from random access
- **⏱️ Auto-shutdown** — server stops after the transfer
- **📱 Android-ready** — works on Termux via GitHub install, .pyz, or ARM64 binary
- **🔄 Cross-platform** — Linux, macOS, Windows, Android
- **📦 Zero dependencies** — pure Python stdlib

## How it works

1. **Sender** starts a tiny HTTP server with a random token
2. A **QR code** + URL appears (in terminal or browser UI)
3. **Receiver** scans or opens the link — on any device with a browser
4. A clean **download page** shows file info + progress bar
5. Server **auto-shuts down** after the transfer

| Tool | Both sides need install? | Visual sender? | Progress bar? | QR code? | Android? |
|------|:---:|:---:|:---:|:---:|:---:|
| **sendit** | ❌ | ✅ | ✅ | ✅ | ✅ |
| scp/rsync | ✅ | ❌ | ❌ | ❌ | ❌ |
| magic-wormhole | ✅ | ❌ | ✅ | ❌ | ❌ |

---

## License

MIT
