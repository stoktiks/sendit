"""Entry point for the web-only version — auto-starts the web UI, no args needed.

Run: python sendit-web.pyz
     ./sendit-web [port]
"""

import sys
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
