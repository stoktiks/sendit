# sendit

**Simple file transfer, zero dependencies, works everywhere.**

Share files between devices instantly. The receiver only needs a browser — no app, no install, no account.

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

From the cloned directory:

```bash
python -m sendit send ./file.zip
```

## Quick Start

**Sender:**
```bash
sendit send ./bigfile.zip
# → 🔗 http://192.168.1.5:9876/a3b2c1
```

**Receiver (in browser):**
Just open the link! Works on any device — phone, tablet, laptop, smart TV. No app needed.

**Receiver (CLI):**
```bash
sendit get http://192.168.1.5:9876/a3b2c1
```

## How It Works

1. **Sender** starts a temporary HTTP server
2. A random token protects your file from random access
3. The server auto-shuts down once the transfer completes
4. Pure Python stdlib — no dependencies to install

## Why sendit?

| Tool | Needs install on both sides? | Works across networks? | Zero deps? |
|------|------------------------------|------------------------|------------|
| **sendit** | ❌ (browser works!) | ✅ (with relay) | ✅ |
| scp/rsync | ✅ | ✅ | ❌ (needs SSH) |
| magic-wormhole | ✅ | ✅ | ❌ |
| nc | ✅ | ❌ | ✅ |

## License

MIT
