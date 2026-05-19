from importlib import resources
from pathlib import Path

import yaml


def _files_under(root: Path) -> set[str]:
    return {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
    }


def test_bundled_template_matches_repo_template() -> None:
    repo_template = Path(__file__).resolve().parents[1] / "book_template"

    with resources.as_file(resources.files("minerupress").joinpath("book_template")) as bundled:
        assert _files_under(bundled) == _files_under(repo_template)
        for rel_path in _files_under(repo_template):
            assert (bundled / rel_path).read_bytes() == (repo_template / rel_path).read_bytes()


def test_template_mkdocs_nav_points_to_existing_files() -> None:
    template = Path(__file__).resolve().parents[1] / "book_template"
    mkdocs = yaml.safe_load((template / "mkdocs.yml").read_text(encoding="utf-8"))
    docs_dir = template / mkdocs["docs_dir"]

    assert (docs_dir / "index.md").exists()
    assert (docs_dir / "chapters" / "ch01-overview.md").exists()


def test_template_defaults_to_existing_uploaded_result_mode() -> None:
    template = Path(__file__).resolve().parents[1] / "book_template"
    book = yaml.safe_load((template / "book.yml").read_text(encoding="utf-8"))

    assert book["source"] == "uploaded_result"
    assert book["volume_uid"] == "my-book"
    assert book["chapters"] == [
        {
            "slug": "ch01-overview",
            "title": "第1章 概述",
        }
    ]
