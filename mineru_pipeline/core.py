"""
mineru_pipeline.core
~~~~~~~~~~~~~~~~~~~~
Generic MinerU content_list.json → Markdown exporter engine.

Book-specific configuration (chapters, volume UIDs, site metadata) lives
entirely in a book.yml file and is passed in as a BookConfig dataclass.
All content transformation is handled by the plugin system.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .plugins.base import ExportPlugin

# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ChapterConfig:
    slug: str                  # output filename stem, e.g. "ch01-overview"
    title: str                 # display title, e.g. "第1章 概述"
    volume_uid: str            # prefix of the MinerU output directory UID
    start_pattern: str         # regex matched against text items to find boundary


@dataclass
class BookConfig:
    chapters: list[ChapterConfig]
    mineru_root: Path = Path("resources/mineru")
    docs_out: Path = Path("docs")
    # Pages past this index are considered table-of-contents and skipped
    # when searching for chapter boundaries.
    toc_max_page: int = 10


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SKIP_TYPES = {"page_number", "header", "footer", "page_footnote"}
_LEVEL_MAP  = {1: "#", 2: "##", 3: "###", 4: "####"}


def _caption_text(raw) -> str:
    if isinstance(raw, list):
        return " ".join(str(x) for x in raw).strip()
    return str(raw).strip() if raw else ""


def _load_volume(vol_dir: Path) -> list[dict]:
    candidates = sorted(vol_dir.glob("*_content_list.json"))
    non_v2 = [p for p in candidates if "v2" not in p.name]
    path = non_v2[0] if non_v2 else candidates[0]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find_boundary(
    items: list[dict],
    pattern: re.Pattern,
    toc_max_page: int,
) -> int | None:
    for idx, item in enumerate(items):
        if item.get("type") != "text":
            continue
        if item.get("page_idx", 0) <= toc_max_page:
            continue
        if pattern.match(item.get("text", "")):
            return idx
    return None


def _item_to_md(
    item: dict,
    img_base: Path | None,
    plugins: Sequence[ExportPlugin],
) -> str | None:
    """Convert a single content_list item to Markdown, applying plugins."""

    t = item.get("type", "")
    if t in _SKIP_TYPES:
        return None

    # ---- image ----
    if t == "image":
        raw_path = item.get("img_path", "")
        if not raw_path:
            return None
        fname = Path(raw_path).name
        full_path = (img_base / fname) if img_base else None

        for plugin in plugins:
            if not plugin.on_image(item, full_path):
                return None  # plugin says drop it

        raw_caption = item.get("img_caption", "")
        caption = _caption_text(raw_caption)
        alt = caption if caption else fname
        for plugin in plugins:
            alt = plugin.on_text(item, alt)
        lines = [f"![{alt}](../images/{fname})"]
        if caption:
            cap_display = caption
            for plugin in plugins:
                cap_display = plugin.on_text(item, cap_display)
            lines.append(f"*{cap_display}*")
        return "\n".join(lines)

    # ---- equation ----
    if t == "equation":
        latex = item.get("text", "").strip()
        if not latex:
            return None
        # MinerU sometimes wraps in $$...$$; strip to avoid doubling
        inner = latex
        if inner.startswith("$$") and inner.endswith("$$"):
            inner = inner[2:-2].strip()
        return f"$$\n{inner}\n$$"

    # ---- table ----
    if t == "table":
        raw_caption = item.get("table_caption", "")
        caption = _caption_text(raw_caption)
        body = item.get("table_body", "")
        parts = []
        if caption:
            cap_display = caption
            for plugin in plugins:
                cap_display = plugin.on_text(item, cap_display)
            parts.append(f"**{cap_display}**")
        if body:
            parts.append(body)
        return "\n\n".join(parts) if parts else None

    # ---- code ----
    if t == "code":
        code = item.get("text", "").strip()
        return f"```\n{code}\n```" if code else None

    # ---- all text-like types ----
    text = item.get("text", "").strip()
    if not text:
        return None

    if t == "text":
        level = item.get("text_level")
        for plugin in plugins:
            text = plugin.on_text(item, text)
        if level and level in _LEVEL_MAP:
            return f"{_LEVEL_MAP[level]} {text}"
        return text

    # list, aside_text, chart, …
    for plugin in plugins:
        text = plugin.on_text(item, text)
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export(config: BookConfig, plugins: Sequence[ExportPlugin] = ()) -> None:
    """
    Run the full export pipeline for one book.

    Parameters
    ----------
    config:
        Book-specific configuration (chapters, paths, etc.)
    plugins:
        Zero or more ExportPlugin instances applied during conversion.
    """
    mineru_root = config.mineru_root
    docs_out    = config.docs_out

    # Discover volume directories by UID prefix
    uid_prefixes = sorted({ch.volume_uid for ch in config.chapters})
    vol_dirs: dict[str, Path] = {}
    for d in mineru_root.iterdir():
        if not d.is_dir():
            continue
        for prefix in uid_prefixes:
            if prefix in d.name and prefix not in vol_dirs:
                vol_dirs[prefix] = d

    missing = [p for p in uid_prefixes if p not in vol_dirs]
    if missing:
        raise FileNotFoundError(
            f"Volume directories not found for UIDs: {missing}\n"
            f"Searched in: {mineru_root}"
        )

    volumes: dict[str, list[dict]] = {
        uid: _load_volume(d) for uid, d in vol_dirs.items()
    }

    # Copy images (plugins may filter individual files)
    images_out = docs_out / "images"
    images_out.mkdir(parents=True, exist_ok=True)
    total_copied = total_skipped = 0
    for uid, vol_dir in vol_dirs.items():
        img_src = vol_dir / "images"
        if not img_src.exists():
            continue
        for img in img_src.iterdir():
            if not img.is_file():
                continue
            # Synthesise a minimal item dict for the plugin hook
            fake_item = {"type": "image", "img_path": f"images/{img.name}"}
            keep = all(p.on_image(fake_item, img) for p in plugins)
            if keep:
                shutil.copy2(img, images_out / img.name)
                total_copied += 1
            else:
                total_skipped += 1
    print(f"  Images: {total_copied} copied, {total_skipped} filtered → {images_out}")

    # Group chapters by volume
    vol_chapters: dict[str, list[ChapterConfig]] = {uid: [] for uid in uid_prefixes}
    for ch in config.chapters:
        vol_chapters[ch.volume_uid].append(ch)

    chapters_out = docs_out / "chapters"
    chapters_out.mkdir(parents=True, exist_ok=True)

    for uid, chapter_list in vol_chapters.items():
        items   = volumes[uid]
        img_base = vol_dirs[uid] / "images"

        # Find all boundaries in this volume
        boundaries: list[tuple[int, ChapterConfig]] = []
        for ch in chapter_list:
            pat = re.compile(ch.start_pattern)
            idx = _find_boundary(items, pat, config.toc_max_page)
            if idx is None:
                print(f"  [WARN] boundary not found: {ch.title}")
            else:
                boundaries.append((idx, ch))
        boundaries.sort(key=lambda x: x[0])

        for i, (start, ch) in enumerate(boundaries):
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else None
            chapter_items = items[start:end]

            lines: list[str] = [f"# {ch.title}", ""]
            for item in chapter_items:
                md = _item_to_md(item, img_base=img_base, plugins=plugins)
                if md is not None:
                    lines.append(md)
                    lines.append("")

            for plugin in plugins:
                lines = plugin.on_chapter_done(ch.slug, lines)

            out_path = chapters_out / f"{ch.slug}.md"
            out_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"  Wrote {out_path.name}  ({len(chapter_items)} items)")

    print(f"\nDone. Output in {docs_out}")
