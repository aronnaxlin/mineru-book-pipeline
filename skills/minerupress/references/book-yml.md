# book.yml Reference

Minimal local export:

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

Cloud API:

```yaml
api:
  token: ""  # prefer MINERU_API_TOKEN in .env
  enable_formula: true
  enable_table: true
  model_version: vlm
  sources:
    javaweb: resources/pdfs/javaweb.pdf
```

Boundary controls:

- `title`: canonical display title and default boundary source.
- `aliases`: alternate headings to auto-convert into boundary patterns.
- `start_pattern`: one regex for legacy configs.
- `start_patterns`: multiple regex alternatives.
- `toc_max_page`: skip early table-of-contents matches only for the first boundary in a logical volume.
- `allow_missing_boundaries`: keep `false` for CI/production.

Supported inferred heading styles include Chinese chapter/section labels, appendices, English `Chapter`/`Unit`/`Module`/`Part`/`Section`, project/module/task labels, and numeric headings such as `10.1`.
