"""
minerupress.headings
~~~~~~~~~~~~~~~~~~~~
Inspect MinerU content_list.json files and suggest chapter boundaries.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from typing import Iterable

_NATURAL_PARTS = re.compile(r"(\d+)")
_SPACE_RE = re.compile(r"\s+")
_TOC_LEADER_RE = re.compile(r"(?:\.{2,}|…+|··+|--+)\s*\d+\s*$")
_TRAILING_PAGE_RE = re.compile(r"\s+(?:\.{2,}|…+|··+)?\s*\d+\s*$")
_CHAPTER_ONLY_RE = re.compile(
    r"^\s*第\s*([0-9０-９一二三四五六七八九十百千万零〇两]+)\s*章\s*$"
)
_CHAPTER_FULL_RE = re.compile(
    r"^\s*第\s*([0-9０-９一二三四五六七八九十百千万零〇两]+)\s*章\s*(.+?)\s*$"
)
_APPENDIX_ONLY_RE = re.compile(r"^\s*附\s*录\s*([A-Za-zＡ-Ｚａ-ｚ0-9０-９]+)\s*$")
_APPENDIX_FULL_RE = re.compile(r"^\s*附\s*录\s*([A-Za-zＡ-Ｚａ-ｚ0-9０-９]+)\s*(.+?)\s*$")
_PART_RE = re.compile(
    r"^\s*第\s*([0-9０-９一二三四五六七八九十百千万零〇两]+)\s*篇\s*(.+?)?\s*$"
)
_SECTION_RE = re.compile(r"^\s*\d+(?:\.\d+)+\s+")
_HEADING_TYPES = {"text", "aside_text"}


@dataclass(frozen=True)
class HeadingCandidate:
    segment: str
    item_idx: int
    page_idx: int | None
    level: int | None
    text: str
    kind: str
    label: str
    title: str
    start_pattern: str
    is_toc_like: bool
    confidence: str


def load_content_items(mineru_root: Path, volume_uid: str | None = None) -> list[tuple[str, list[dict]]]:
    """Load MinerU content_list items grouped by physical segment directory."""
    root = Path(mineru_root)
    if not root.exists():
        raise FileNotFoundError(f"MinerU root not found: {root}")

    dirs = [
        path for path in sorted(root.iterdir(), key=_natural_key)
        if path.is_dir() and (volume_uid is None or path.name.startswith(volume_uid))
    ]
    if not dirs:
        target = f" matching volume_uid={volume_uid!r}" if volume_uid else ""
        raise FileNotFoundError(f"No MinerU segment directories found in {root}{target}")

    loaded: list[tuple[str, list[dict]]] = []
    for directory in dirs:
        candidates = sorted(directory.glob("*_content_list.json"))
        if not candidates:
            continue
        non_v2 = [path for path in candidates if "v2" not in path.name]
        content_path = non_v2[0] if non_v2 else candidates[0]
        with open(content_path, encoding="utf-8") as f:
            loaded.append((directory.name, json.load(f)))
    if not loaded:
        raise FileNotFoundError(f"No *_content_list.json files found in {root}")
    return loaded


def analyze_headings(
    segments: list[tuple[str, list[dict]]],
    *,
    toc_max_page: int | None = 20,
    include_toc: bool = True,
    include_generic: bool = False,
) -> list[HeadingCandidate]:
    """Return heading-like MinerU text items, with TOC and boundary hints."""
    results: list[HeadingCandidate] = []
    for segment_name, items in segments:
        for item_idx, item in enumerate(items):
            item_type = item.get("type")
            if item_type not in _HEADING_TYPES:
                continue
            if item_type == "text" and item.get("text_level") != 1:
                continue
            text = _normalize_text(item.get("text", ""))
            if not text:
                continue
            candidate = _classify_heading(
                segment_name=segment_name,
                item_idx=item_idx,
                item=item,
                text=text,
                items=items,
                toc_max_page=toc_max_page,
            )
            if candidate and not include_generic and candidate.kind == "heading":
                continue
            if candidate and (include_toc or not candidate.is_toc_like):
                results.append(candidate)
    return results


def print_report(candidates: Iterable[HeadingCandidate]) -> None:
    for candidate in candidates:
        marker = "toc?" if candidate.is_toc_like else "body"
        page = "?" if candidate.page_idx is None else str(candidate.page_idx)
        print(
            f"{candidate.segment}:{candidate.item_idx} "
            f"page={page} L{candidate.level} {marker} {candidate.confidence} "
            f"{candidate.kind} {candidate.label} | {candidate.text}"
        )
        if candidate.title:
            print(f"  title: {candidate.title}")
        if candidate.start_pattern:
            print(f"  start_pattern: {candidate.start_pattern}")


def print_yaml(candidates: Iterable[HeadingCandidate]) -> None:
    print("chapters:")
    for candidate in candidates:
        if candidate.is_toc_like or candidate.kind not in {"chapter", "appendix"}:
            continue
        title = candidate.title or candidate.text
        slug = _slug_for(candidate)
        print(f"  - slug: {slug}")
        print(f"    title: {title}")
        if candidate.start_pattern:
            print(f"    start_pattern: {candidate.start_pattern}")
        print()


def main(
    argv: Sequence[str] | None = None,
    *,
    prog: str = "minerupress-headings",
) -> int:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Inspect MinerU output and suggest chapter boundary YAML.",
    )
    parser.add_argument("mineru_root", nargs="?", default="resources/mineru")
    parser.add_argument("--volume-uid", help="Only inspect segment directories with this prefix.")
    parser.add_argument(
        "--toc-max-page",
        type=int,
        default=20,
        help="Pages below this index are treated as likely table-of-contents pages.",
    )
    parser.add_argument(
        "--format",
        choices=("report", "yaml"),
        default="report",
        help="Output a diagnostic report or book.yml chapter YAML.",
    )
    parser.add_argument(
        "--body-only",
        action="store_true",
        help="Hide heading candidates that look like table-of-contents entries.",
    )
    parser.add_argument(
        "--include-generic",
        action="store_true",
        help="Also show generic MinerU level-1 headings that are not chapters, parts, or appendices.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    segments = load_content_items(Path(args.mineru_root), args.volume_uid)
    candidates = analyze_headings(
        segments,
        toc_max_page=args.toc_max_page,
        include_toc=not args.body_only,
        include_generic=args.include_generic,
    )
    if args.format == "yaml":
        print_yaml(candidates)
    else:
        print_report(candidates)
    return 0


def _classify_heading(
    *,
    segment_name: str,
    item_idx: int,
    item: dict,
    text: str,
    items: list[dict],
    toc_max_page: int | None,
) -> HeadingCandidate | None:
    page_idx = _optional_int(item.get("page_idx"))
    level = _optional_int(item.get("text_level"))
    is_toc = _is_toc_like(text, page_idx, toc_max_page)

    match = _CHAPTER_ONLY_RE.match(text)
    if match:
        label = _ascii_digits(match.group(1))
        title = _next_title(items, item_idx)
        return _candidate(segment_name, item_idx, page_idx, level, text, "chapter", label, title, is_toc, "high")

    match = _CHAPTER_FULL_RE.match(text)
    if match:
        label = _ascii_digits(match.group(1))
        raw_title = _clean_title(_strip_toc_tail(match.group(2)))
        confidence = "low" if is_toc else "medium"
        return _candidate(segment_name, item_idx, page_idx, level, text, "chapter", label, raw_title, is_toc, confidence)

    match = _APPENDIX_ONLY_RE.match(text)
    if match:
        label = _ascii_digits(match.group(1)).upper()
        title = _next_title(items, item_idx)
        return _candidate(segment_name, item_idx, page_idx, level, text, "appendix", label, title, is_toc, "high")

    match = _APPENDIX_FULL_RE.match(text)
    if match:
        label = _ascii_digits(match.group(1)).upper()
        raw_title = _clean_title(_strip_toc_tail(match.group(2)))
        confidence = "low" if is_toc else "medium"
        return _candidate(segment_name, item_idx, page_idx, level, text, "appendix", label, raw_title, is_toc, confidence)

    match = _PART_RE.match(text)
    if match:
        label = _ascii_digits(match.group(1))
        title = _clean_title(_strip_toc_tail(match.group(2) or _next_title(items, item_idx)))
        return _candidate(segment_name, item_idx, page_idx, level, text, "part", label, title, is_toc, "medium")

    if level == 1 and not _SECTION_RE.match(text):
        return HeadingCandidate(
            segment=segment_name,
            item_idx=item_idx,
            page_idx=page_idx,
            level=level,
            text=text,
            kind="heading",
            label="",
            title=_clean_title(text),
            start_pattern="",
            is_toc_like=is_toc,
            confidence="low",
        )
    return None


def _candidate(
    segment: str,
    item_idx: int,
    page_idx: int | None,
    level: int | None,
    text: str,
    kind: str,
    label: str,
    title: str,
    is_toc_like: bool,
    confidence: str,
) -> HeadingCandidate:
    return HeadingCandidate(
        segment=segment,
        item_idx=item_idx,
        page_idx=page_idx,
        level=level,
        text=text,
        kind=kind,
        label=label,
        title=title,
        start_pattern=_start_pattern(kind, label),
        is_toc_like=is_toc_like,
        confidence=confidence,
    )


def _start_pattern(kind: str, label: str) -> str:
    escaped = re.escape(label)
    if kind == "chapter":
        return rf"^第\s*{escaped}\s*章$"
    if kind == "appendix":
        return rf"^附录\s*{escaped}$"
    return ""


def _next_title(items: list[dict], item_idx: int) -> str:
    for next_item in items[item_idx + 1:item_idx + 8]:
        if next_item.get("type") != "text":
            continue
        text = _normalize_text(next_item.get("text", ""))
        if not text or _SECTION_RE.match(text):
            continue
        if _CHAPTER_ONLY_RE.match(text) or _APPENDIX_ONLY_RE.match(text):
            continue
        return _clean_title(_strip_toc_tail(text))
    return ""


def _is_toc_like(text: str, page_idx: int | None, toc_max_page: int | None) -> bool:
    if _TOC_LEADER_RE.search(text):
        return True
    if toc_max_page is not None and page_idx is not None and page_idx < toc_max_page:
        if _TRAILING_PAGE_RE.search(text) and (
            _CHAPTER_FULL_RE.match(text)
            or _APPENDIX_FULL_RE.match(text)
            or _PART_RE.match(text)
        ):
            return True
    return False


def _strip_toc_tail(text: str) -> str:
    stripped = _TOC_LEADER_RE.sub("", text).strip()
    return _TRAILING_PAGE_RE.sub("", stripped).strip()


def _clean_title(text: str) -> str:
    text = _normalize_text(text)
    # MinerU sometimes splits Chinese title glyphs with spaces, e.g. "引 论".
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)


def _slug_for(candidate: HeadingCandidate) -> str:
    if candidate.kind == "chapter":
        value = _han_to_int(candidate.label)
        if value is None and candidate.label.isdigit():
            value = int(candidate.label)
        if value is not None:
            return f"ch{value:02d}"
        return f"ch-{_ascii_slug(candidate.label)}"
    if candidate.kind == "appendix":
        return f"appendix-{_ascii_slug(candidate.label).lower()}"
    return _ascii_slug(candidate.title or candidate.text)


def _ascii_slug(text: str) -> str:
    text = _ascii_digits(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "chapter"


def _normalize_text(text: object) -> str:
    return _SPACE_RE.sub(" ", str(text or "")).strip()


def _natural_key(path: Path) -> list[object]:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in _NATURAL_PARTS.split(path.name)
    ]


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ascii_digits(text: str) -> str:
    return text.translate(
        str.maketrans(
            "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )
    )


def _han_to_int(text: str) -> int | None:
    digits = {
        "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    }
    if not text or any(ch not in digits and ch not in "十百千万" for ch in text):
        return None
    total = section = number = 0
    for ch in text:
        if ch in digits:
            number = digits[ch]
        elif ch == "十":
            section += (number or 1) * 10
            number = 0
        elif ch == "百":
            section += (number or 1) * 100
            number = 0
        elif ch == "千":
            section += (number or 1) * 1000
            number = 0
        elif ch == "万":
            total += (section + number) * 10000
            section = number = 0
    return total + section + number


if __name__ == "__main__":
    main()
