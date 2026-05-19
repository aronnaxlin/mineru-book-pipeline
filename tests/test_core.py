from pathlib import Path

import pytest

from minerupress.core import (
    BookConfig,
    ChapterConfig,
    _VolumeSegment,
    _compile_boundary_patterns,
    _find_boundary_after,
    export,
)


def _write_volume(root: Path, name: str, items: list[dict], image_name: str = "shared.png") -> None:
    volume = root / name
    images = volume / "images"
    images.mkdir(parents=True)
    (images / image_name).write_bytes(b"img")
    (volume / f"{name}_content_list.json").write_text(
        __import__("json").dumps(items, ensure_ascii=False),
        encoding="utf-8",
    )


def test_export_handles_boundaries_markdown_and_image_collisions(tmp_path: Path) -> None:
    mineru_root = tmp_path / "resources" / "mineru"
    docs_out = tmp_path / "docs"

    _write_volume(
        mineru_root,
        "book_part1",
        [
            {"type": "text", "text_level": 1, "page_idx": 0, "text": "第1章 引论 …… 3"},
            {"type": "text", "text_level": 1, "page_idx": 10, "text": "第 1 章"},
            {"type": "text", "text": "正文里讨论 <span> 标签"},
            {"type": "code", "code_body": "```python\nprint(1)"},
            {"type": "equation", "text": "$$x+1$$"},
            {"type": "table", "table_caption": ["表1"], "table_body": "<table><tr><td>A</td></tr></table>"},
            {"type": "image", "img_path": "images/shared.png", "img_caption": ["图1"]},
        ],
    )
    _write_volume(
        mineru_root,
        "book_part2",
        [
            {"type": "text", "text_level": 1, "page_idx": 0, "text": "第 2 章"},
            {"type": "text", "text": "第二章正文"},
            {"type": "image", "img_path": "images/shared.png"},
        ],
    )

    export(
        BookConfig(
            mineru_root=mineru_root,
            docs_out=docs_out,
            toc_max_page=5,
            chapters=[
                ChapterConfig(
                    slug="ch01",
                    title="引论",
                    volume_uid="book",
                    start_pattern=r"^第\s*1\s*章$",
                ),
                ChapterConfig(
                    slug="ch02",
                    title="第二章",
                    volume_uid="book",
                    start_pattern=r"^第\s*2\s*章$",
                ),
            ],
        )
    )

    ch01 = (docs_out / "chapters" / "ch01.md").read_text(encoding="utf-8")
    ch02 = (docs_out / "chapters" / "ch02.md").read_text(encoding="utf-8")

    assert "# 引论" in ch01
    assert "第1章 引论 …… 3" not in ch01
    assert "&lt;span&gt;" in ch01
    assert "```python\nprint(1)\n```" in ch01
    assert "$$\nx+1\n$$" in ch01
    assert "**表1**" in ch01
    assert "<table><tr><td>A</td></tr></table>" in ch01
    assert "![图1](../images/shared.png)" in ch01
    assert "![book_part2_shared.png](../images/book_part2_shared.png)" in ch02
    assert (docs_out / "images" / "shared.png").exists()
    assert (docs_out / "images" / "book_part2_shared.png").exists()


def test_missing_boundary_fails_in_strict_mode(tmp_path: Path) -> None:
    mineru_root = tmp_path / "resources" / "mineru"
    _write_volume(
        mineru_root,
        "book_full",
        [{"type": "text", "text_level": 1, "page_idx": 10, "text": "第 1 章"}],
    )

    config = BookConfig(
        mineru_root=mineru_root,
        docs_out=tmp_path / "docs",
        chapters=[
            ChapterConfig(
                slug="missing",
                title="不存在",
                volume_uid="book",
                start_pattern=r"^第\s*2\s*章$",
            )
        ],
    )

    with pytest.raises(RuntimeError, match="Chapter boundaries not found"):
        export(config)


def test_aside_text_can_be_a_chapter_boundary(tmp_path: Path) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "aside_text", "text": "第1章\n绪论", "page_idx": 16},
                {"type": "text", "text": "1.1 通信的基本概念", "page_idx": 16},
            ],
        )
    ]
    patterns = _compile_boundary_patterns(
        ChapterConfig(slug="ch01", title="第1章 绪论", volume_uid="book")
    )

    assert _find_boundary_after(segments, patterns, None, 0) == (0, 0)


def test_generated_chapter_title_patterns_do_not_match_bare_answer_labels(
    tmp_path: Path,
) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "text", "text": "第1章", "page_idx": 97},
            ],
        )
    ]
    patterns = _compile_boundary_patterns(
        ChapterConfig(slug="ch01", title="第1章 绪论", volume_uid="book")
    )

    assert _find_boundary_after(segments, patterns, None, 0) is None


def test_bare_chapter_title_still_matches_bare_chapter_label(tmp_path: Path) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "text", "text": "第 1 章", "page_idx": 10},
            ],
        )
    ]
    patterns = _compile_boundary_patterns(
        ChapterConfig(slug="ch01", title="第1章", volume_uid="book")
    )

    assert _find_boundary_after(segments, patterns, None, 0) == (0, 0)


def test_generated_patterns_cover_common_chinese_variants(tmp_path: Path) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "text", "text": "第一章：绪论", "page_idx": 10},
                {"type": "text", "text": "第 2 章  确知信号", "page_idx": 20},
                {"type": "text", "text": "项目二、尚硅谷书城", "page_idx": 30},
            ],
        )
    ]

    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("ch01", "第1章 绪论", "book")),
        None,
        0,
    ) == (0, 0)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("ch02", "第二章 确知信号", "book")),
        None,
        0,
    ) == (0, 1)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("project-02", "项目2 尚硅谷书城", "book")),
        None,
        0,
    ) == (0, 2)


def test_generated_patterns_cover_common_english_variants(tmp_path: Path) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "text", "text": "CHAPTER ONE: Introduction", "page_idx": 10},
                {"type": "text", "text": "Chap. 2 Signals and Systems", "page_idx": 20},
                {"type": "text", "text": "PART 2 - Digital Transmission", "page_idx": 30},
                {"type": "text", "text": "Lesson IV. Modulation", "page_idx": 40},
                {"type": "text", "text": "App. B: Tables", "page_idx": 50},
            ],
        )
    ]

    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("ch01", "Chapter 1 Introduction", "book")),
        None,
        0,
    ) == (0, 0)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("ch02", "Chapter Two Signals", "book")),
        None,
        0,
    ) == (0, 1)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("part-02", "Part II Digital Transmission", "book")),
        None,
        0,
    ) == (0, 2)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("lesson-04", "Lesson 4 Modulation", "book")),
        None,
        0,
    ) == (0, 3)
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("appendix-b", "Appendix B Tables", "book")),
        None,
        0,
    ) == (0, 4)


def test_generated_patterns_do_not_match_bare_labels_when_title_has_text(
    tmp_path: Path,
) -> None:
    segments = [
        _VolumeSegment(
            uid="book",
            path=tmp_path,
            items=[
                {"type": "text", "text": "附录A", "page_idx": 97},
                {"type": "text", "text": "Chapter 1", "page_idx": 98},
                {"type": "text", "text": "10.1", "page_idx": 99},
            ],
        )
    ]

    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("appendix-a", "附录A 习题答案", "book")),
        None,
        0,
    ) is None
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("ch01", "Chapter 1 Introduction", "book")),
        None,
        0,
    ) is None
    assert _find_boundary_after(
        segments,
        _compile_boundary_patterns(ChapterConfig("sec-10-1", "10.1 JavaScript 简介", "book")),
        None,
        0,
    ) is None
