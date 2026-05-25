# sendit

**Simple file transfer, zero dependencies, works everywhere.**

```
pip install sendit
```

## Quick Start

**Sender:**
```bash
sendit send ./bigfile.zip
# → 🔗 http://192.168.1.5:9876/a3b2c1
```

**Receiver (in browser):**
Just open the link! Works on any device with a browser.

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
