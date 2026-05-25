# sendit

**Simple file transfer, zero dependencies, works everywhere.**

Share files between devices instantly. The receiver only needs a browser — no app, no install, no account.

## Features

- 📤 **Send files** with a single command
- 📱 **QR code** in terminal — scan with your phone, no typing
- 🌐 **Web UI** — receiver opens the link in any browser
- 📊 **Progress bar** with speed + ETA (both terminal & browser)
- 🔒 **Random token** protects your file
- ⏱️ **Auto-shutdown** after transfer completes
- 💻 No dependencies — pure Python stdlib

## Installation

> 📌 Requires **Python 3.8+** (already installed on most systems).

### Option 1 — Clone & Install (recommended)

```bash
git clone https://github.com/stoktiks/sendit.git
cd sendit
pip install .
```

Or in editable mode (so `git pull` updates without reinstalling):

```bash
pip install -e .
```

### Option 2 — Direct pip from GitHub

```bash
pip install git+https://github.com/stoktiks/sendit.git
```

### Option 3 — Run without installing

```bash
python -m sendit send ./file.zip
```

## Quick Start

**Sender:**
```bash
sendit send ./bigfile.zip
# → 🔗 http://192.168.1.5:9876/a3b2c1
# → 📱 QR code appears here — scan with phone!
```

**Receiver (in browser):**
Just scan the QR or open the link. A clean download page shows the file info + a Download button with real-time progress bar.

**Receiver (CLI):**
```bash
sendit get http://192.168.1.5:9876/a3b2c1
```
Shows a progress bar with speed and ETA:
```
  ██████████████░░░░░░░░  60%  117.3 MB/s  ETA 2s
  ████████████████████████  100%  127.0 MB/s  0.0s
✅ Saved to ./bigfile.zip
```

## Examples

```bash
# Send any file
sendit send ./photo.jpg

# Send on a specific port
sendit send ./video.mp4 --port 8080

# Increase timeout (default 5 min)
sendit send ./huge.zip --timeout 600

# Download via CLI
sendit get http://192.168.1.5:9876/a3b2c1

# Save with custom filename
sendit get http://192.168.1.5:9876/a3b2c1 -o myfile.zip
```

## How It Works

1. **Sender** starts a temporary HTTP server with a random token
2. Shows a **QR code** + URL in the terminal
3. **Receiver** scans the QR or opens the link in any browser
4. **Web UI** shows file info + a Download button with real-time progress bar
5. Server **auto-shuts down** once the transfer completes
6. Pure Python stdlib — no extra dependencies

## Why sendit?

| Tool | Needs install on both sides? | Works across networks? | Progress bar? | QR code? |
|------|------------------------------|------------------------|---------------|----------|
| **sendit** | ❌ (browser works!) | ✅ (with relay) | ✅ | ✅ |
| scp/rsync | ✅ | ✅ | ❌ | ❌ |
| magic-wormhole | ✅ | ✅ | ✅ | ❌ |
| nc | ✅ | ❌ | ❌ | ❌ |

## License

MIT
