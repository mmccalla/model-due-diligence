"""CLI entry point for the mdd-ui local dashboard."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mdd-ui",
        description="Launch the local Model Due Diligence dashboard API.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765, help="Bind port. Default: 8765")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for local development.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        import uvicorn
    except ImportError:
        print(
            "ERROR: mdd-ui requires optional UI dependencies. "
            "Install with: python -m pip install 'model-due-diligence[ui]'",
            file=sys.stderr,
        )
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    uvicorn.run(
        "model_due_diligence.ui.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
