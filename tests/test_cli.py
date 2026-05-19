from pathlib import Path

from minerupress import cli


def test_discover_generated_output_dirs_finds_nested_content_lists(tmp_path: Path) -> None:
    first = tmp_path / "book-one" / "auto"
    second = tmp_path / "book-two" / "auto"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "book-one_content_list.json").write_text("[]", encoding="utf-8")
    (second / "book-two_content_list.json").write_text("[]", encoding="utf-8")

    found = cli._discover_generated_output_dirs(tmp_path)

    assert found == [first, second]


def test_root_cli_routes_export_subcommand(monkeypatch) -> None:
    captured = {}

    def fake_run_export(args):
        captured["command"] = args.command
        captured["book_yml"] = args.book_yml
        captured["fetch"] = args.fetch
        return 0

    monkeypatch.setattr(cli, "_run_export", fake_run_export)

    rc = cli.root_main(["export", "demo.yml", "--fetch"])

    assert rc == 0
    assert captured == {
        "command": "export",
        "book_yml": "demo.yml",
        "fetch": True,
    }


def test_root_cli_routes_init_subcommand(tmp_path: Path) -> None:
    target = tmp_path / "my-book"

    rc = cli.root_main(["init", str(target)])

    assert rc == 0
    assert (target / "book.yml").exists()
    assert (target / "mkdocs.yml").exists()
    assert (target / "docs" / "index.md").exists()
    assert (target / "docs" / "chapters" / "ch01-overview.md").exists()
    assert (target / "resources" / "mineru").is_dir()
    assert (target / "resources" / "pdfs").is_dir()


def test_init_refuses_non_empty_directory_without_force(tmp_path: Path) -> None:
    target = tmp_path / "my-book"
    target.mkdir()
    (target / "existing.txt").write_text("keep me", encoding="utf-8")

    rc = cli.root_main(["init", str(target)])

    assert rc == 1
    assert not (target / "book.yml").exists()


def test_legacy_export_wrapper_inserts_subcommand(monkeypatch) -> None:
    captured = {}

    def fake_run_export(args):
        captured["command"] = args.command
        captured["book_yml"] = args.book_yml
        captured["allow_missing_boundaries"] = args.allow_missing_boundaries
        return 0

    monkeypatch.setattr(cli, "_run_export", fake_run_export)

    rc = cli.export_main(["book.yml", "--allow-missing-boundaries"])

    assert rc == 0
    assert captured == {
        "command": "export",
        "book_yml": "book.yml",
        "allow_missing_boundaries": True,
    }


def test_legacy_headings_wrapper_inserts_subcommand(monkeypatch) -> None:
    captured = {}

    def fake_run_headings(args):
        captured["command"] = args.command
        captured["mineru_root"] = args.mineru_root
        captured["format"] = args.format
        return 0

    monkeypatch.setattr(cli, "_run_headings", fake_run_headings)

    rc = cli.headings_main(["resources/mineru", "--format", "yaml"])

    assert rc == 0
    assert captured == {
        "command": "headings",
        "mineru_root": "resources/mineru",
        "format": "yaml",
    }
