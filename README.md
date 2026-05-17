# MineruPress

Turn MinerU output into a publishable MkDocs Material book site.

Input: MinerU `content_list.json` + images  
Output: chapter-split MkDocs Material site  
Best for: scanned textbooks, course notes, internal manuals

[Live example](https://software-testing-methods.pages.dev): a textbook site generated from a PDF through MinerU and MineruPress.

```text
PDF / MinerU API
      |
      v
resources/mineru/*_content_list.json + images
      |
      v
docs/chapters/*.md + docs/images/
      |
      v
MkDocs Material site
```

MineruPress 是一条面向长文档发布的通用工具链，适合教材、讲义、内部手册、培训资料和知识库迁移这类 `PDF -> MinerU -> Markdown -> MkDocs` 场景。它把书籍差异收敛到 `book.yml` 和插件里，让导出、校验、增量修正、部署都能重复执行。

## 一分钟开始

复制模板就是一本新书的起点：

```bash
cp -r book_template/ my-book
cd my-book
minerupress-fetch book.yml
mkdocs serve
```

如果你已经有本地 MinerU 输出，把它放到 `resources/mineru/` 后运行：

```bash
minerupress-export book.yml
mkdocs serve
```

## 主要能力

- 把 MinerU 的 `*_content_list.json` 导出为按章节拆分的 Markdown。
- 把同一本书的多个物理分片当成一个逻辑 `volume_uid` 连续处理。
- 根据章节标题自动推导边界，支持 `第10章`、`第十章`、`附录A`、`Chapter 3`、`项目二`、`10.1` 等常见格式。
- 保留 MinerU `code_body` 代码块，普通正文中的 HTML/XML 标签会自动转义。
- 每次导出都会重建 `docs/chapters/` 和 `docs/images/`，避免旧文件残留。
- 提供 `minerupress-headings`，从 MinerU 输出中分析大标题并生成章节配置草稿。
- 支持图片过滤、中文与西文间距修正、Markdown 指纹比对，以及可选的 Cloudflare Pages 部署。
- 附带可复用的 AI Agent Skill，方便其他 agent 按同一流程处理图书项目。

## 安装

当前推荐从 GitHub 开发安装：

```bash
git clone https://github.com/aronnaxlin/minerupress.git
cd minerupress
pip install -e ".[all]"
```

可选依赖组：

| Extra | 增加依赖 | 用途 |
|---|---|---|
| `qr` | `opencv-python` | `qr_filter` 二维码图片过滤 |
| `cjk` | `pangu` | `cjk_spacing` 中西文间距处理 |
| `all` | 两者都装 | 常见完整环境 |

如果你的图书项目还没有安装 MkDocs：

```bash
pip install mkdocs mkdocs-material
```

要求 Python `>=3.11`。

## 快速开始

1. 复制模板创建一本新书工作区：

```bash
cp -r book_template/ ~/dev/my-book/
cd ~/dev/my-book/
```

2. 准备输入：

- 把 MinerU 输出目录放到 `resources/mineru/`
- 编辑 `book.yml`
- 编辑 `mkdocs.yml` 的站点信息与导航

3. 导出并本地预览：

```bash
minerupress-export book.yml
mkdocs serve
```

4. 严格构建校验：

```bash
mkdocs build --strict
```

兼容旧命令：

- `mineru-export`
- `mineru-fetch`

## 常用命令

本地 MinerU 输出导出：

```bash
minerupress-export book.yml
```

先上传 PDF 到 MinerU 云端，再导出：

```bash
minerupress-fetch book.yml
```

已有本地输出时，补抓缺失分册后再导出：

```bash
minerupress-export --fetch book.yml
```

分析 MinerU 大标题并生成章节配置草稿：

```bash
minerupress-headings resources/mineru --volume-uid javaweb --format yaml --body-only
```

允许边界缺失并继续导出，仅建议排查问题时使用：

```bash
minerupress-export --allow-missing-boundaries book.yml
```

生成或比对指纹：

```bash
python -m minerupress.fingerprint --docs-dir docs --out reports/fingerprints.json
```

## 测试与 CI

本地测试：

```bash
pip install -e ".[dev]"
pytest
```

仓库已配置 GitHub Actions，在 Python 3.11 和 3.12 上运行 `compileall` 与 `pytest`。

## 发布状态

MineruPress 目前处于 `0.1.0` alpha 阶段，推荐使用 GitHub 开发安装。正式 Release 和 PyPI 分发还在准备中；发布前需要补齐版本标记、构建产物校验和发布凭据。

## `book.yml` 最小示例

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

边界匹配建议：

- 优先只写 `title`
- MinerU 标题有别名时加 `aliases`
- 必须手工控正则时再写 `start_pattern` 或 `start_patterns`
- 生产环境保持 `allow_missing_boundaries: false`

所有相对路径都以 `book.yml` 所在目录为基准解析，所以可以从任意当前目录执行：

```bash
minerupress-export /path/to/my-book/book.yml
```

## 内置插件

- `qr_filter`：使用 OpenCV 检测并过滤小尺寸二维码图片。
- `cjk_spacing`：使用 `pangu` 为中西文混排补空格，并保护 LaTeX 公式片段。
- `cf_pages`：执行 `mkdocs build --strict` 后部署到 Cloudflare Pages；项目不存在时会自动创建后重试。

自定义插件继承 `ExportPlugin`：

```python
from pathlib import Path
from minerupress import ExportPlugin


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

然后在 `book.yml` 中引用 dotted path：

```yaml
plugins:
  - mypackage.mymodule.MyPlugin
```

## 文档索引

更详细的中文文档见 `docs/guide/`：

- [总览与术语](docs/index.md)
- [English README](docs/README_EN.md)
- [快速开始](docs/guide/getting-started.md)
- [实战工作流](docs/guide/workflow-run-a-book.md)
- [配置详解](docs/guide/configuration.md)
- [导出流程](docs/guide/export-pipeline.md)
- [插件系统](docs/guide/plugins.md)
- [云端抓取与部署](docs/guide/cloud-api-and-deploy.md)
- [校验、指纹与排障](docs/guide/validation-and-troubleshooting.md)
- [发布与分发](docs/guide/release.md)

## Agent Skill

这个仓库内置了一个给使用者安装的 Skill：

```text
skills/minerupress/
```

如果你想在自己的 agent 环境里获取它，可以从仓库安装：

```bash
npx skills add aronnaxlin/minerupress --skill minerupress
```

安装后，适合交给 AI agent 做配置、抓取、导出、验证、排障和部署。

如果你是在维护这个仓库本身，`skills/minerupress/` 目录就是要一起发布出去的 Skill 内容，不是给仓库作者自己“获取”的命令示例。

## 仓库边界

这个仓库是通用工具链，不应提交某本书的本地生成物或敏感信息。通常不应纳入版本控制的内容包括：

- `book.yml`
- `mkdocs.yml`
- `docs/`
- `site/`
- `resources/`
- `reports/`
- `.env`
- `.wrangler/`

当前仓库里历史上用于本地调试的一套书稿工作区已迁到 `local_book_workspace/`，并默认加入 `.gitignore`。真实图书项目建议复制 `book_template/` 到独立工作区中维护。

## 致谢

- [MinerU](https://github.com/opendatalab/MinerU)
- [MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Cloudflare Pages](https://pages.cloudflare.com/)
- [Vercel Agent Skills](https://vercel.com/docs/agent-resources/skills)

## License

Apache License 2.0，见 [LICENSE](LICENSE)。
