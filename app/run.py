from __future__ import annotations

import argparse
import socket

import uvicorn

from app import __version__


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
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"noteeli {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--host", default=DEFAULT_HOST)
        sub.add_argument("--port", type=int, default=DEFAULT_PORT)
        sub.add_argument(
            "--demo",
            action="store_true",
            help="Read-only public demo mode. Disables auth, refuses every mutation, "
                 "uses a baked demo content root. Equivalent to NOTEELI_DEMO_MODE=1.",
        )

    dev_parser = subparsers.add_parser(
        "dev",
        help="Start in development mode with reload on the first free port.",
    )
    _add_common(dev_parser)

    prod_parser = subparsers.add_parser(
        "prod",
        help="Start in production mode without reload.",
    )
    _add_common(prod_parser)

    return parser


def run_dev(host: str, port: int) -> None:
    selected_port = first_free_port(host, port)
    uvicorn.run("app.main:app", host=host, port=selected_port, reload=True)


def run_prod(host: str, port: int) -> None:
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


def main() -> None:
    import os

    parser = build_parser()
    args = parser.parse_args()

    # The flag has to win before uvicorn imports the app — settings are
    # cached at import time so we set the env var here and let pydantic
    # pick it up. uvicorn forks workers which inherit the environment.
    if getattr(args, "demo", False):
        os.environ["NOTEELI_DEMO_MODE"] = "1"

    if args.command == "dev":
        run_dev(args.host, args.port)
        return

    if args.command == "prod":
        run_prod(args.host, args.port)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
