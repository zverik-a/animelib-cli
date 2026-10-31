"""Backward-compatible entry point; use ``python main.py`` for the CLI."""

from main import main


if __name__ == "__main__":
    raise SystemExit(main())
