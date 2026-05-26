"""Entry point for the web-only version — auto-starts the web UI, no args needed.

Run: python sendit-web.pyz
     ./sendit-web [port]

Bundles qrcode inside the .pyz for offline QR generation.
"""

import os
import sys


# When running from a .pyz, bundled vendor packages live next to this file
if hasattr(sys, "frozen") or "__compressed__" in globals():
    _root = os.path.dirname(os.path.abspath(__file__))
else:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_vendor = os.path.join(_root, "_vendor")
if os.path.isdir(_vendor):
    sys.path.insert(0, _vendor)


from .serve import run_web_server


def main():
    port = 0
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Usage: sendit-web [port]")
            sys.exit(1)
    run_web_server(port=port)


if __name__ == "__main__":
    main()
