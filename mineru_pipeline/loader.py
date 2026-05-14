"""
mineru_pipeline.loader
~~~~~~~~~~~~~~~~~~~~~~
Load a book.yml file into a BookConfig + plugin list.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .core import BookConfig, ChapterConfig
from .plugins.base import ExportPlugin


def load_book_config(book_yml: Path) -> tuple[BookConfig, list[ExportPlugin]]:
    """
    Parse a book.yml file and return (BookConfig, [plugins]).

    book.yml schema
    ---------------
    mineru_root: resources/mineru          # optional, default shown
    docs_out: docs                         # optional
    toc_max_page: 10                       # optional

    plugins:                               # optional list
      - qr_filter                          # built-in name
      - cjk_spacing                        # built-in name
      # - mypackage.MyPlugin               # dotted import path

    chapters:
      - slug: ch01-overview
        title: 第1章 概述
        volume_uid: 73d5b3e7
        start_pattern: "^第\\s*1\\s*章\\s*概述"
      ...
    """
    with open(book_yml, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    chapters = [
        ChapterConfig(
            slug=ch["slug"],
            title=ch["title"],
            volume_uid=ch["volume_uid"],
            start_pattern=ch["start_pattern"],
        )
        for ch in raw["chapters"]
    ]

    config = BookConfig(
        chapters=chapters,
        mineru_root=Path(raw.get("mineru_root", "resources/mineru")),
        docs_out=Path(raw.get("docs_out", "docs")),
        toc_max_page=int(raw.get("toc_max_page", 10)),
    )

    plugins = _load_plugins(raw.get("plugins", []))
    return config, plugins


_BUILTIN_PLUGINS: dict[str, str] = {
    "qr_filter":   "mineru_pipeline.plugins.qr_filter.QRFilterPlugin",
    "cjk_spacing": "mineru_pipeline.plugins.cjk_spacing.CJKSpacingPlugin",
}


def _load_plugins(names: list[str]) -> list[ExportPlugin]:
    plugins = []
    for name in names:
        dotted = _BUILTIN_PLUGINS.get(name, name)
        module_path, cls_name = dotted.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, cls_name)
        plugins.append(cls())
    return plugins
