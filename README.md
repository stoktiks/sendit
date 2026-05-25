# sendit

**Share files between any devices. Receiver just needs a browser — zero install.**

[![Release](https://img.shields.io/github/v/release/stoktiks/sendit)](https://github.com/stoktiks/sendit/releases)
[![Downloads](https://img.shields.io/github/downloads/stoktiks/sendit/total)](https://github.com/stoktiks/sendit/releases)
[![Platforms](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Android-blue)](https://github.com/stoktiks/sendit/releases)

---

## Quick Start (30 seconds)

```bash
# 1. Download a single binary from Releases
chmod +x sendit-linux-x86_64

# 2. Start the web UI
./sendit-linux-x86_64 web

# 3. Open the URL, drag & drop a file → share the link
```

**Sender installs nothing?** Use the portable `.pyz` — just needs Python:

```bash
python sendit.pyz web
```

---

## How It Works

1. **Sender** starts a tiny HTTP server with a random token
2. A **URL + QR code** appears (terminal or browser UI)
3. **Receiver opens the link** — on any device with a modern browser
4. File downloads with a live **progress bar**
5. Server **auto-shuts down** after transfer completes

---

## Install

### 📦 Binary (easiest — no dependencies)

Download from [Releases](https://github.com/stoktiks/sendit/releases):

| Platform | Binary |
|----------|--------|
| 🐧 Linux x86_64 | `sendit-linux-x86_64` |
| 📱 Linux ARM64 (Android/Termux, RPi) | `sendit-linux-arm64` |
| 🍎 macOS ARM64 | `sendit-darwin-arm64` |
| 🪟 Windows x86_64 | `sendit-windows-x86_64.exe` |
| 🐍 Any OS with Python 3.8+ | `sendit.pyz` (portable) |
| 🤖 Android (native APK) | `sendit-android.apk` |

```bash
# Linux / macOS
chmod +x sendit-linux-x86_64 && ./sendit-linux-x86_64 web

# Windows
sendit-windows-x86_64.exe web

# APK on Android
# Download sendit-android.apk → tap to install → open app → Start
```

### 🐍 Python (from source)

```bash
git clone https://github.com/stoktiks/sendit.git
cd sendit
pip install -e .
sendit web
```

---

## Commands

### `sendit web` — visual drag & drop

```bash
sendit web            # start browser UI on a free port
sendit web 8080       # use a specific port
```

Opens a web page where you drag & drop a file, get a shareable link + QR code. **Perfect for non-technical receivers.**

### `sendit send` — fast terminal sender

```bash
sendit send ./video.mp4              # share any file
sendit send ./file.zip --port 9000   # custom port
```

Shows a QR code + URL in the terminal. Receiver scans with their phone camera.

### `sendit get` — download via CLI

```bash
sendit get http://192.168.1.5:9876/a3b2c1
sendit get http://192.168.1.5:9876/a3b2c1 -o myfile.zip
```

Downloads with a live progress bar showing speed & ETA.

---

## Why sendit?

| | sendit | scp/rsync | magic-wormhole |
|---|---|---|---|
| **Receiver needs install?** | ❌ No (just a browser) | ✅ Yes | ✅ Yes |
| **Visual drag & drop?** | ✅ Yes | ❌ No | ❌ No |
| **Progress bar?** | ✅ Yes | ❌ (scp) / ✅ (rsync) | ✅ Yes |
| **QR code?** | ✅ Yes | ❌ No | ❌ No |
| **Android native?** | ✅ APK | ❌ No | ❌ No |
| **Zero dependencies?** | ✅ Pure stdlib | 🟡 Needs SSH | 🟡 Needs Python |

---

## Features

- **📱 QR codes** — scan with your phone, no typing
- **📊 Progress bars** — speed & ETA in terminal and browser
- **🔒 Random tokens** — each file gets a unique, unguessable URL
- **⏱️ Auto-shutdown** — server stops when the download finishes
- **🔄 Cross-platform** — Linux, macOS, Windows, Android (APK + Termux)
- **📦 Zero-dependency sender** — pure Python stdlib
- **🎯 LAN-optimized** — no internet routing, no cloud, no accounts

---

## License

MIT
