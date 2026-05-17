from pathlib import Path

import pytest

from minerupress.core import BookConfig, ChapterConfig, export


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
