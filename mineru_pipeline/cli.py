"""
mineru_pipeline.cli
~~~~~~~~~~~~~~~~~~~
Command-line entry points:
  mineru-export  — convert local MinerU output to per-chapter Markdown
  mineru-fetch   — upload PDFs to MinerU cloud API, then export
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from .core import export
from .loader import load_book_config


def _do_fetch(config, api_cfg) -> None:
    """Upload PDFs via MinerU API and populate mineru_root."""
    from .api_client import MinerUClient

    kwargs = {}
    if api_cfg.token:
        kwargs["token"] = api_cfg.token

    client = MinerUClient(
        enable_formula=api_cfg.enable_formula,
        enable_table=api_cfg.enable_table,
        model_version=api_cfg.model_version,
        **kwargs,
    )

    if not api_cfg.sources:
        raise ValueError(
            "api.sources is empty. "
            "Add volume_uid -> pdf_path entries under 'api.sources' in book.yml."
        )

    config.mineru_root.mkdir(parents=True, exist_ok=True)
    for uid, pdf_str in api_cfg.sources.items():
        pdf_path = Path(pdf_str)
        if not pdf_path.exists():
            raise FileNotFoundError(f"API source PDF not found: {pdf_path}")
        out_dirs = client.fetch(pdf_path=pdf_path, dest=config.mineru_root)
        if not out_dirs:
            raise RuntimeError(f"MinerU fetch returned no output directories for {pdf_path}")
        # Rename every fetched segment so core.export can discover all parts by
        # the logical volume_uid prefix used by book.yml chapters.
        out_dir_resolved = {p.resolve() for p in out_dirs}
        _clear_existing_uid_outputs(config.mineru_root, uid, out_dir_resolved)
        for i, out_dir in enumerate(out_dirs, 1):
            suffix = f"part{i}" if len(out_dirs) > 1 else "full"
            target = config.mineru_root / f"{uid}_{suffix}"
            if out_dir.resolve() == target.resolve():
                continue
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            out_dir.rename(target)
            print(f"  [api] renamed -> {target.name}")


def _clear_existing_uid_outputs(
    mineru_root: Path,
    uid: str,
    keep: set[Path],
) -> None:
    part_pattern = re.compile(rf"^{re.escape(uid)}_part\d+$")
    for path in mineru_root.iterdir():
        if path.resolve() in keep:
            continue
        if path.name != f"{uid}_full" and not part_pattern.match(path.name):
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mineru-export",
        description="Export MinerU content_list.json to per-chapter Markdown.",
    )
    parser.add_argument(
        "book_yml",
        nargs="?",
        default="book.yml",
        help="Path to book.yml (default: book.yml)",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Upload PDFs via MinerU cloud API before exporting (requires api: block in book.yml)",
    )
    parser.add_argument(
        "--allow-missing-boundaries",
        action="store_true",
        help="Warn instead of failing when a configured chapter boundary is not found.",
    )
    args = parser.parse_args()

    book_yml = Path(args.book_yml)
    if not book_yml.exists():
        print(f"Error: {book_yml} not found.", file=sys.stderr)
        sys.exit(1)

    config, plugins, api_cfg = load_book_config(book_yml)
    if args.allow_missing_boundaries:
        config.allow_missing_boundaries = True
    print(f"Loaded: {len(config.chapters)} chapters, {len(plugins)} plugins")

    if args.fetch:
        if api_cfg is None:
            print(
                "Error: --fetch requires an 'api:' block in book.yml.",
                file=sys.stderr,
            )
            sys.exit(1)
        _do_fetch(config, api_cfg)

    export(config, plugins)


def fetch_main() -> None:
    """Entry point for `mineru-fetch`: fetch then export."""
    parser = argparse.ArgumentParser(
        prog="mineru-fetch",
        description="Upload PDFs to MinerU cloud API, then export to Markdown.",
    )
    parser.add_argument(
        "book_yml",
        nargs="?",
        default="book.yml",
        help="Path to book.yml (default: book.yml)",
    )
    parser.add_argument(
        "--allow-missing-boundaries",
        action="store_true",
        help="Warn instead of failing when a configured chapter boundary is not found.",
    )
    args = parser.parse_args()

    book_yml = Path(args.book_yml)
    if not book_yml.exists():
        print(f"Error: {book_yml} not found.", file=sys.stderr)
        sys.exit(1)

    config, plugins, api_cfg = load_book_config(book_yml)
    if args.allow_missing_boundaries:
        config.allow_missing_boundaries = True
    print(f"Loaded: {len(config.chapters)} chapters, {len(plugins)} plugins")

    if api_cfg is None:
        print(
            "Error: book.yml has no 'api:' block. "
            "Add api.token and api.sources to use mineru-fetch.",
            file=sys.stderr,
        )
        sys.exit(1)

    _do_fetch(config, api_cfg)
    export(config, plugins)


if __name__ == "__main__":
    main()
