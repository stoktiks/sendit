# sendit

**Simple file transfer, zero dependencies, works everywhere.**

Share files between devices instantly. The receiver only needs a browser — no app, no install, no account.

## Features

- 📤 **`sendit send`** — Send files from command line
- 🕸️ **`sendit web`** — Drag & drop visual UI in browser
- 📱 **QR code** — Scan with your phone, no typing
- 📊 **Progress bar** with speed + ETA (both terminal & browser)
- 🔒 **Random token** protects your file
- ⏱️ **Auto-shutdown** after transfer completes
- 💻 No dependencies — pure Python stdlib

## Installation

> 📌 Requires **Python 3.8+** (already installed on most systems).

```bash
git clone https://github.com/stoktiks/sendit.git
cd sendit
pip install -e .
```

## Quick Start

### 🕸️ Visual mode (drag & drop)

```bash
sendit web
# → http://192.168.1.5:34137  (open in browser)
```

Opens a beautiful web page. Drag & drop any file → instantly get a shareable link + QR code.

### 📤 Command-line sender

```bash
sendit send ./bigfile.zip
# → 🔗 http://192.168.1.5:9876/a3b2c1
# → 📱 QR code in terminal
```

### 📥 Receiver (browser)

Scan the QR or open the link. Beautiful download page with real-time progress bar.

### 📥 Receiver (CLI)

```bash
sendit get http://192.168.1.5:9876/a3b2c1
```

Shows a progress bar with speed & ETA:
```
  ██████████████░░░░░░░░  60%  117.3 MB/s  ETA 2s
  ████████████████████████  100%  127.0 MB/s  0.0s
✅ Saved to ./bigfile.zip
```

## Usage

```bash
# Sender: visual mode (drag & drop in browser)
sendit web

# Sender: CLI mode
sendit send ./photo.jpg

# Receiver: browser
# Just scan the QR code or open the link

# Receiver: CLI
sendit get http://192.168.1.5:9876/a3b2c1
sendit get http://192.168.1.5:9876/a3b2c1 -o myfile.zip
```

## How It Works

1. **Sender** starts a temporary HTTP server
2. **CLI mode**: a QR code + URL appear in the terminal
3. **Web mode**: a beautiful drag & drop page opens in browser
4. **Receiver** scans the QR or opens the link — no app needed
5. **Progress bar** shows real-time speed & ETA
6. Server **auto-shuts down** after transfer

## Why sendit?

| Tool | Needs install on both sides? | Visual sender? | Progress bar? | QR code? |
|------|------------------------------|----------------|---------------|----------|
| **sendit** | ❌ (browser works!) | ✅ (drag & drop) | ✅ | ✅ |
| scp/rsync | ✅ | ❌ | ❌ | ❌ |
| magic-wormhole | ✅ | ❌ | ✅ | ❌ |

## License

MIT
