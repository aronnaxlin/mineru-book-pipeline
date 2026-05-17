---
name: minerupress
description: Use when an AI agent needs to turn MinerU local output or MinerU cloud API results into a publishable MkDocs Material book site with chapter splitting, image filtering, CJK spacing, strict validation, and optional Cloudflare Pages deployment. Trigger for tasks involving MineruPress, minerupress, MinerU content_list.json, book.yml, minerupress-export, minerupress-fetch, mineru-export, mineru-fetch, generated docs/chapters, or PDF-to-MkDocs book publishing automation.
---

# MineruPress

Use this skill to configure, run, verify, and troubleshoot the MineruPress publishing pipeline for MinerU -> MkDocs Material book sites.

## Install The Toolchain

If the current machine does not already have the project, install it first:

```bash
git clone https://github.com/aronnaxlin/minerupress.git
cd minerupress
pip install -e ".[all]"
```

For a new book workspace, copy `book_template/` outside the toolchain repo or
use it as the starting point for `book.yml`, `mkdocs.yml`, `.env.example`, and
`Makefile`. Keep real PDFs, MinerU output, `.env`, generated `docs/`, and
generated `site/` out of the toolchain repository unless the user explicitly
asks to commit a book project.

## Preferred Workflow

Default to a two-stage, isolated workflow when the user starts from a raw PDF:

1. Create an isolated book workspace rather than reusing the toolchain root.
2. Copy the source PDF into that workspace under `resources/pdfs/`.
3. Run a first pass with `minerupress-fetch` to obtain MinerU output.
4. Inspect `*_content_list.json` to confirm the real chapter boundary shape.
5. Refine `book.yml` chapter boundaries and rerun `minerupress-export`.
6. Verify with `mkdocs build --strict` and optionally fingerprints.

This is the safest default because:

- automatic PDF splitting writes chunk files next to the source PDF
- cloud-drive or protected paths may fail with `PermissionError`
- table-of-contents pages often need one refinement pass before chapter boundaries are stable
- generated `docs/`, `site/`, `reports/`, and `resources/mineru/` stay isolated per book

## Workflow

1. Inspect the book workspace:
   - Read `book.yml`, `mkdocs.yml`, and `AGENTS.md` if present.
   - Check `resources/mineru/` for one or more MinerU output directories containing `*_content_list.json`.
   - Treat `docs/chapters/`, `docs/images/`, `site/`, `reports/`, and `.env` as generated or local-only unless the user explicitly asks otherwise.

2. If the user starts from a raw PDF instead of existing MinerU output:
   - Create or use an isolated workspace for that specific book.
   - Copy the PDF into `resources/pdfs/` inside the workspace instead of referencing a cloud-drive or protected external path directly.
   - Write a minimal `api:` block and a temporary placeholder chapter.
   - Run `minerupress-fetch book.yml` first to fetch MinerU output and get an initial export.
   - Run `minerupress-headings resources/mineru --volume-uid <uid> --format yaml --body-only` to generate a chapter YAML draft.

3. Configure `book.yml`:
   - Use a top-level `volume_uid` for a logical book/PDF. Split outputs such as `javaweb_p1` and `javaweb_p2` can share `volume_uid: javaweb`.
   - Prefer chapter `title` plus `slug`; omit `start_pattern` unless the generated boundary matcher is ambiguous.
   - Add `aliases` or `start_patterns` only when MinerU headings differ from the canonical title.
   - Keep `allow_missing_boundaries: false` for production runs.
   - After the first fetch, inspect `*_content_list.json` and replace placeholder chapters with the real chapter list.
   - If the table of contents page causes false matches, prefer a display-only `title` plus an exact `start_pattern` such as `^第\\s*1\\s*章$`.

4. Run export:

```bash
minerupress-export book.yml
```

For cloud API upload and export:

```bash
minerupress-fetch book.yml
```

Legacy commands `mineru-export` and `mineru-fetch` are also available for existing projects.

5. Verify:

```bash
mkdocs build --strict
```

If Markdown fingerprints are part of the project workflow:

```bash
python -m minerupress.fingerprint --docs-dir docs --out reports/fingerprints.json
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

If TOC lines such as `第1章 引论 …… 3` are matched before the real body heading,
switch to exact body-heading regexes:

```yaml
chapters:
  - slug: ch01-introduction
    title: 引论
    start_pattern: "^第\\s*1\\s*章$"
```

This avoids the generated title matcher from locking onto the table of contents.

Use the headings helper before hand-writing many boundaries:

```bash
minerupress-headings resources/mineru --volume-uid javaweb --format report
minerupress-headings resources/mineru --volume-uid javaweb --format yaml --body-only
```

The report marks TOC-looking candidates as `toc?` and body-looking candidates as `body`.

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
For the end-to-end isolated-book workflow, also read the project docs page
`docs/guide/workflow-run-a-book.md` in this repository.
