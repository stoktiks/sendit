"""Entry point for standalone web-only binary — uses absolute imports."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sendit.cli_web import main

if __name__ == "__main__":
    main()
