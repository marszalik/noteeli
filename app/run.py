from __future__ import annotations

import argparse
import socket

import uvicorn


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_PORT = 65535


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex((host, port)) != 0


def first_free_port(host: str, start_port: int) -> int:
    for port in range(start_port, MAX_PORT + 1):
        if is_port_free(host, port):
            return port
    raise RuntimeError(f"No free port found in range {start_port}-{MAX_PORT}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Noteeli with uvicorn.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dev_parser = subparsers.add_parser(
        "dev",
        help="Start in development mode with reload on the first free port.",
    )
    dev_parser.add_argument("--host", default=DEFAULT_HOST)
    dev_parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    prod_parser = subparsers.add_parser(
        "prod",
        help="Start in production mode without reload.",
    )
    prod_parser.add_argument("--host", default=DEFAULT_HOST)
    prod_parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    return parser


def run_dev(host: str, port: int) -> None:
    selected_port = first_free_port(host, port)
    uvicorn.run("app.main:app", host=host, port=selected_port, reload=True)


def run_prod(host: str, port: int) -> None:
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "dev":
        run_dev(args.host, args.port)
        return

    if args.command == "prod":
        run_prod(args.host, args.port)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
