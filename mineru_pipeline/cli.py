"""
mineru_pipeline.cli
~~~~~~~~~~~~~~~~~~~
Command-line entry point: mineru-export
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import export
from .loader import load_book_config


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mineru-export",
        description="Export MinerU content_list.json to per-chapter Markdown.",
    )
    parser.add_argument(
        "book_yml",
        nargs="?",
        default="book.yml",
        help="Path to book.yml configuration file (default: book.yml)",
    )
    args = parser.parse_args()

    book_yml = Path(args.book_yml)
    if not book_yml.exists():
        print(f"Error: {book_yml} not found.", file=sys.stderr)
        sys.exit(1)

    config, plugins = load_book_config(book_yml)
    print(f"Loaded: {len(config.chapters)} chapters, {len(plugins)} plugins")
    export(config, plugins)


if __name__ == "__main__":
    main()
