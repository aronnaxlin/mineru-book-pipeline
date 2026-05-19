from pathlib import Path

import pytest

from minerupress.loader import load_book_config


def _write_book(tmp_path: Path, body: str) -> Path:
    book_yml = tmp_path / "book.yml"
    book_yml.write_text(body, encoding="utf-8")
    return book_yml


def test_load_book_config_defaults_legacy_local_output_to_uploaded_result(tmp_path: Path) -> None:
    book_yml = _write_book(
        tmp_path,
        """
mineru_root: resources/mineru
chapters:
  - slug: ch01
    title: 第1章
    volume_uid: demo
""".strip(),
    )

    config, plugins, source_cfg = load_book_config(book_yml)

    assert config.mineru_root == (tmp_path / "resources" / "mineru").resolve()
    assert plugins == []
    assert source_cfg.kind == "uploaded_result"
    assert source_cfg.api is None
    assert source_cfg.local_toolchain is None


def test_load_book_config_supports_local_toolchain_source(tmp_path: Path) -> None:
    pdf_path = tmp_path / "resources" / "pdfs" / "book.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-1.7")

    book_yml = _write_book(
        tmp_path,
        """
source: local
local_toolchain:
  executable: mineru
  args:
    - -b
    - pipeline
  sources:
    demo: resources/pdfs/book.pdf
chapters:
  - slug: ch01
    title: 第1章
""".strip(),
    )

    config, _, source_cfg = load_book_config(book_yml)

    assert config.chapters[0].volume_uid == "demo"
    assert source_cfg.kind == "local_toolchain"
    assert source_cfg.local_toolchain is not None
    assert source_cfg.local_toolchain.executable == "mineru"
    assert source_cfg.local_toolchain.args == ["-b", "pipeline"]
    assert source_cfg.local_toolchain.sources == {
        "demo": str(pdf_path.resolve()),
    }


def test_load_book_config_rejects_unknown_source(tmp_path: Path) -> None:
    book_yml = _write_book(
        tmp_path,
        """
source: something-else
chapters:
  - slug: ch01
    title: 第1章
    volume_uid: demo
""".strip(),
    )

    with pytest.raises(ValueError, match="Unsupported source"):
        load_book_config(book_yml)
