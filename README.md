# mineru-book-pipeline

An AI-friendly pipeline for turning [MinerU](https://github.com/opendatalab/MinerU) output into a clean [MkDocs](https://www.mkdocs.org/) Material book site.

It is designed for repeatable book conversion work:

- Export MinerU `*_content_list.json` into one Markdown file per chapter.
- Treat split PDFs as one logical volume, so `javaweb_p1` and `javaweb_p2` can share `volume_uid: javaweb`.
- Infer chapter boundaries from human titles such as `第10章`, `第十章`, `附录A`, `Chapter 3`, `项目二`, or `10.1`.
- Rebuild generated `docs/chapters/` and `docs/images/` on each export to avoid stale files.
- Filter images, add CJK spacing, fingerprint output, and optionally deploy to Cloudflare Pages.
- Ship a reusable agent Skill for other AI agents.

## Install

```bash
pip install -e ".[all]"
```

Optional dependency groups:

| Extra | Adds | Used by |
|---|---|---|
| `qr` | `opencv-python` | QR image filtering |
| `cjk` | `pangu` | Chinese/ASCII spacing |
| `all` | both | common book export setup |

MkDocs itself is used by generated book projects. Install it in your book environment if it is not already available:

```bash
pip install mkdocs mkdocs-material
```

## Quick Start

Create a new book workspace:

```bash
cp -r book_template/ ~/dev/my-book/
cd ~/dev/my-book/
```

Prepare:

1. Put MinerU output directories under `resources/mineru/`.
2. Edit `book.yml`.
3. Edit `mkdocs.yml` site metadata and navigation.

Export and preview:

```bash
mineru-export book.yml
mkdocs serve
```

Build strictly:

```bash
mkdocs build --strict
```

## Cloud MinerU API

For API-based parsing, copy `book_template/.env.example` to `.env` and fill secrets locally:

```bash
MINERU_API_TOKEN=...
```

Then configure `api.sources` in `book.yml` and run:

```bash
mineru-fetch book.yml
```

Large PDFs are split automatically before upload. The fetched output is renamed to `volume_uid_full` or `volume_uid_partN`, and stale outputs for that same `volume_uid` are cleaned before export.

## Configuration

Minimal `book.yml`:

```yaml
mineru_root: resources/mineru
docs_out: docs
volume_uid: javaweb
toc_max_page: 10
allow_missing_boundaries: false

plugins:
  - qr_filter
  - cjk_spacing

chapters:
  - slug: ch01-overview
    title: 第1章 Web开发概述
  - slug: appendix-a
    title: 附录A 部分习题的解答
```

Boundary matching:

- Prefer `title`; the exporter derives common boundary patterns automatically.
- Use `aliases` when MinerU headings use alternate titles.
- Use `start_pattern` or `start_patterns` only when you need exact regex control.
- Keep `allow_missing_boundaries: false` in production. Use `--allow-missing-boundaries` only while diagnosing noisy OCR output.

Example:

```yaml
chapters:
  - slug: unit-01
    title: 第一单元 Web 基础
    aliases:
      - Unit 1
    start_patterns:
      - "^第\\s*一\\s*单元"
```

All relative paths are resolved from the directory containing `book.yml`, so this works from any current working directory:

```bash
mineru-export /path/to/my-book/book.yml
```

## Plugins

Built-in plugins:

- `qr_filter`: drops small QR-code images with OpenCV.
- `cjk_spacing`: inserts spacing between CJK and ASCII text with `pangu`, while protecting LaTeX spans.
- `cf_pages`: builds with `mkdocs build --strict` and deploys to Cloudflare Pages. If the Pages project does not exist, it creates it and retries.

Custom plugins subclass `ExportPlugin`:

```python
from pathlib import Path
from mineru_pipeline import ExportPlugin

class MyPlugin(ExportPlugin):
    def on_image(self, item: dict, img_path: Path | None) -> bool:
        return True

    def on_text(self, item: dict, text: str) -> str:
        return text

    def on_chapter_done(self, slug: str, lines: list[str]) -> list[str]:
        return lines

    def on_export_done(self, docs_out: Path) -> None:
        pass
```

Then reference it from `book.yml`:

```yaml
plugins:
  - mypackage.mymodule.MyPlugin
```

## Agent Skill

This repository includes an installable Skill for AI agents:

```text
skills/mineru-book-pipeline/
```

Install from a GitHub repository:

```bash
npx skills add <owner/repo> --skill mineru-book-pipeline
```

Use it when an agent needs to configure, export, validate, troubleshoot, or deploy a MinerU-to-MkDocs book pipeline.

## Repository Scope

This repository is the reusable toolchain and template. It should not commit a specific book's local artifacts.

Ignored root-level book artifacts include:

- `book.yml`
- `mkdocs.yml`
- `docs/`
- `site/`
- `.temp/`
- `resources/`
- `.env`
- `.wrangler/`

Keep real book projects in their own workspace copied from `book_template/`.

## Acknowledgements

This project stands on the shoulders of:

- [MinerU](https://github.com/opendatalab/MinerU), for document parsing and `content_list.json` output.
- [MkDocs](https://www.mkdocs.org/), for the static documentation framework.
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), for the book-ready theme.
- [Cloudflare Pages](https://pages.cloudflare.com/), for simple static site hosting.
- [Vercel Agent Skills](https://vercel.com/docs/agent-resources/skills), for the Skill packaging model used by `skills/mineru-book-pipeline/`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
