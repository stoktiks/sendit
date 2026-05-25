import argparse
import sys
from .server import run_server
from .client import run_client
from .serve import run_web_server


def main():
    parser = argparse.ArgumentParser(
        prog="sendit",
        description="Simple P2P file transfer — zero deps, works everywhere.",
    )
    sub = parser.add_subparsers(dest="command")

    # send
    send_p = sub.add_parser("send", help="Send a file (start a temp server)")
    send_p.add_argument("file", help="Path to the file to send")
    send_p.add_argument("--port", type=int, default=0,
                        help="Port to listen on (default: random available)")
    send_p.add_argument("--timeout", type=int, default=300,
                        help="Max seconds before server shuts down (default: 300)")

    # web
    web_p = sub.add_parser("web", help="Start a visual web UI for sending files")
    web_p.add_argument("port", nargs="?", type=int, default=0,
                       help="Port to listen on (default: random available)")

    # get
    get_p = sub.add_parser("get", help="Download a file from a sendit link")
    get_p.add_argument("url", help="URL or code from the sender")
    get_p.add_argument("--output", "-o", help="Output filename (default: auto)")

    args = parser.parse_args()

    if args.command == "send":
        run_server(args.file, port=args.port, timeout=args.timeout)
    elif args.command == "web":
        run_web_server(port=args.port)
    elif args.command == "get":
        run_client(args.url, output=args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
