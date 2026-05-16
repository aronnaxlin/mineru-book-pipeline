---
name: mineru-book-pipeline
description: Use when an AI agent needs to turn MinerU local output or MinerU cloud API results into a MkDocs Material book site with chapter splitting, image filtering, CJK spacing, strict validation, and optional Cloudflare Pages deployment. Trigger for tasks involving mineru-book-pipeline, MinerU content_list.json, book.yml, mineru-export, mineru-fetch, generated docs/chapters, or PDF-to-MkDocs book automation.
---

# MinerU Book Pipeline

Use this skill to configure, run, verify, and troubleshoot the MinerU -> MkDocs Material pipeline.

## Install The Toolchain

If the current machine does not already have the project, install it first:

```bash
git clone https://github.com/aronnaxlin/mineru-book-pipeline.git
cd mineru-book-pipeline
pip install -e ".[all]"
```

For a new book workspace, copy `book_template/` outside the toolchain repo or
use it as the starting point for `book.yml`, `mkdocs.yml`, `.env.example`, and
`Makefile`. Keep real PDFs, MinerU output, `.env`, generated `docs/`, and
generated `site/` out of the toolchain repository unless the user explicitly
asks to commit a book project.

## Workflow

1. Inspect the book workspace:
   - Read `book.yml`, `mkdocs.yml`, and `AGENTS.md` if present.
   - Check `resources/mineru/` for one or more MinerU output directories containing `*_content_list.json`.
   - Treat `docs/chapters/`, `docs/images/`, `site/`, `reports/`, and `.env` as generated or local-only unless the user explicitly asks otherwise.

2. Configure `book.yml`:
   - Use a top-level `volume_uid` for a logical book/PDF. Split outputs such as `javaweb_p1` and `javaweb_p2` can share `volume_uid: javaweb`.
   - Prefer chapter `title` plus `slug`; omit `start_pattern` unless the generated boundary matcher is ambiguous.
   - Add `aliases` or `start_patterns` only when MinerU headings differ from the canonical title.
   - Keep `allow_missing_boundaries: false` for production runs.

3. Run export:

```bash
mineru-export book.yml
```

For cloud API upload and export:

```bash
mineru-fetch book.yml
```

4. Verify:

```bash
mkdocs build --strict
```

If Markdown fingerprints are part of the project workflow:

```bash
python -m mineru_pipeline.fingerprint --docs-dir docs --out reports/fingerprints.json
```

## Chapter Boundary Guidance

The exporter can infer boundary patterns from chapter titles. Use titles like:

- `第10章 JavaScript`
- `附录A 部分习题的解答`
- `Chapter 3 Arrays`
- `项目二 尚硅谷书城`
- `10.1 JavaScript 简介`

Use `aliases` for alternate visible headings:

```yaml
chapters:
  - slug: appendix-a
    title: 附录A 部分习题的解答
    aliases:
      - Appendix A
```

Use `start_patterns` for precise regex alternatives:

```yaml
chapters:
  - slug: unit-01
    title: 第一单元 Web 基础
    start_patterns:
      - "^Unit\\s*1\\b"
      - "^第\\s*一\\s*单元"
```

Only use `--allow-missing-boundaries` while diagnosing bad MinerU output. A successful production run should find every configured chapter boundary.

## Generated Outputs

Each export rebuilds:

- `docs/chapters/`
- `docs/images/`

Do not hand-edit generated chapter Markdown as a long-term fix. Instead, update `book.yml`, source MinerU output, or add a plugin.

## Code And HTML Prose

MinerU code items may store their body in `code_body` rather than `text`.
The exporter preserves already-fenced code blocks from MinerU and falls back
to wrapping unfenced code. If a chapter appears to drop examples after phrases
like "示例代码如下", inspect the source `*_content_list.json` for `type: code`
items before editing generated Markdown.

Literal HTML/XML tags in normal prose and captions are escaped during export
so textbooks can discuss tags such as `<span>` without MkDocs rendering them
as real HTML. Raw `table_body` HTML is preserved as table markup.

## References

Read `references/book-yml.md` when you need a compact configuration reference or examples.
