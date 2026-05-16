# AGENTS.md

给后续在这个仓库里工作的 coding agent 使用。先读这份，再动代码。

## 项目定位

这是一个通用的 `MinerU -> MkDocs Material` 图书导出工具链。

核心流程：

1. 从 `book.yml` 读取图书配置、逻辑分册 UID、章节边界、插件列表和可选 API/部署配置。
2. 从 `resources/mineru/` 下的 MinerU 输出目录读取 `*_content_list.json` 和图片；同一个逻辑 UID 可以对应多个拆分 part。
3. 按章节边界导出 Markdown 到 `docs/chapters/`，图片复制到 `docs/images/`。
4. 可选插件处理图片、文本、整章后处理和导出完成后的部署。

这个仓库本身是工具链；根目录可能有本地调试用的 `book.yml`、`mkdocs.yml`、`docs/`、`site/`、`resources/`，这些是按书生成/配置的本地工作区内容，默认不应纳入版本控制，除非用户明确要求。

## 主要目录

- `mineru_pipeline/`: Python 包源码。
- `mineru_pipeline/core.py`: 导出引擎，负责章节边界查找、item -> Markdown、图片复制和插件 hook 调用。
- `mineru_pipeline/loader.py`: 解析 `book.yml`，组装 `BookConfig`、插件实例和可选 `APIConfig`。
- `mineru_pipeline/cli.py`: `mineru-export` 和 `mineru-fetch` 命令入口。
- `mineru_pipeline/api_client.py`: MinerU Precise API v4 客户端，包含上传、轮询、下载和 PDF 分片。
- `mineru_pipeline/fingerprint.py`: 对 `docs/` 下 Markdown 生成 SHA-256 指纹并输出差异。
- `mineru_pipeline/plugins/`: 内置插件和 `ExportPlugin` 基类。
- `book_template/`: 新书模板，包含 `book.yml`、`mkdocs.yml`、`.env.example`、`Makefile`。

## 环境与安装

需要 Python `>=3.11`。

推荐开发安装：

```bash
pip install -e ".[all]"
```

最小依赖在 `pyproject.toml` 中；可选依赖：

- `qr`: `opencv-python`，供 `qr_filter` 插件检测二维码。
- `cjk`: `pangu`，供 `cjk_spacing` 插件处理中英文间距。
- `all`: 同时安装上面两个。

敏感配置放 `.env`，不要提交。常见变量：

- `MINERU_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`
- `PAGES_PROJECT`

## 常用命令

本地 MinerU 输出导出：

```bash
mineru-export book.yml
```

云端 MinerU API 拉取并导出：

```bash
mineru-fetch book.yml
```

已有本地输出时补充拉取缺失分册：

```bash
mineru-export --fetch book.yml
```

模板书目录里可用的标准流水线：

```bash
make export
make lint
make fmt-check
make fingerprint
make build
make serve
```

根目录没有顶层 `Makefile`；如果在根目录验证工具链，直接调用 Python/CLI 命令。

## 验证建议

轻量代码检查：

```bash
python -m compileall mineru_pipeline
```

导出相关改动后，如果本地有有效 `book.yml` 和 `resources/mineru/`：

```bash
mineru-export book.yml
mkdocs build --strict
```

文档内容发生变化后可生成/比较指纹：

```bash
python -m mineru_pipeline.fingerprint --docs-dir docs --out reports/fingerprints.json
```

涉及 `mineru-fetch` 或 `api_client.py` 的改动通常需要网络和 `MINERU_API_TOKEN`，不要擅自调用会上传 PDF 或消耗云端资源的命令，除非用户明确要求。

涉及 `cf_pages` 的改动注意：插件会在 `CLOUDFLARE_API_TOKEN` 存在时执行 `mkdocs build` 和 `wrangler pages deploy`。本地验证时避免意外部署。

## book.yml 约定

关键字段：

- `mineru_root`: MinerU 输出根目录，默认 `resources/mineru`。
- `docs_out`: MkDocs 文档目录，默认 `docs`。
- `volume_uid`: 可选的顶层默认逻辑分册 UID，章节不写 `volume_uid` 时使用它。
- `toc_max_page`: 查找每个逻辑 UID 的第一个章节边界时跳过的目录页阈值；`0` 表示不跳过。
- `allow_missing_boundaries`: 默认 `false`。严格模式下任一章节边界缺失会失败；临时排查时可设为 `true` 或用 CLI 参数放宽。
- `plugins`: 内置插件名或自定义插件 dotted import 路径。
- `chapters`: 章节列表，必须包含 `slug`、`title`；`volume_uid` 可从顶层继承，`start_pattern` 通常可省略。

`volume_uid` 是 MinerU 输出目录名的可匹配前缀，不一定是完整 UUID。单 PDF 自动拆分后会形成 `volume_uid_part1`、`volume_uid_part2` 等目录，章节仍使用同一个逻辑 `volume_uid`。章节边界可从 `title` 自动推导，支持 `第10章`、`附录A`、`Chapter 3`、`项目二`、`10.1` 等；只有 MinerU 标题异常或存在歧义时再写 `aliases`、`start_pattern` 或 `start_patterns`。

可选 `api:` 块用于 `mineru-fetch`；`sources` 的 key 要与章节的 `volume_uid` 对应。

可选 `deploy:` 块供 `cf_pages` 插件读取；目标 Pages 项目不存在时插件会创建项目后重试部署。

所有相对路径按 `book.yml` 所在目录解析，不依赖调用命令时的当前工作目录。

## 插件开发约定

插件继承 `mineru_pipeline.plugins.base.ExportPlugin`，按需覆盖：

- `on_image(item, img_path) -> bool`: 返回 `False` 丢弃图片。
- `on_text(item, text) -> str`: 处理文本、caption、alt 等。
- `on_chapter_done(slug, lines) -> list[str]`: 整章后处理。
- `on_export_done(docs_out) -> None`: 导出完成后的副作用，例如部署。

新增内置插件时：

1. 放在 `mineru_pipeline/plugins/`。
2. 在 `loader.py` 的 `_BUILTIN_PLUGINS` 注册短名。
3. 如需公开导入，再更新 `mineru_pipeline/plugins/__init__.py` 或 `mineru_pipeline/__init__.py`。
4. 更新 README 和模板里的 `book.yml` 注释。

插件应尽量容错：缺可选依赖时警告并退化为 no-op，避免让普通导出流程崩掉。

## 代码风格

- 使用标准库 `pathlib.Path` 处理路径。
- 保持现有 dataclass 配置风格，不为简单字段引入重型配置框架。
- 导出引擎应尽量保持书籍无关；书籍差异放在 `book.yml` 或插件中。
- 不要把特定教材的清洗规则写死进 `core.py`，优先做成插件。
- 对会触发网络、上传、部署或大量生成文件的命令保持克制，先确认用户意图。
- 不要提交 `.env`、`resources/`、`docs/`、`site/`、`reports/`、`.wrangler/` 等本地生成物或敏感内容。

## 当前仓库注意事项

- 当前仓库没有专门的测试目录；修改后至少运行 `python -m compileall mineru_pipeline`。
- `book_template/Makefile` 是给复制后的新书项目使用的，不代表根目录有 `make` 工作流。
- `api_client.fetch()` 返回 `list[Path]`，顺序必须与原始 PDF chunk 顺序一致；`_do_fetch()` 会把这些目录改名为 `volume_uid_full` 或 `volume_uid_partN`，并清理同 UID 的旧 full/part 输出。
- `core.export()` 会根据 UID 前缀在 `mineru_root` 下自动发现一个或多个分册目录，并按自然顺序顺推章节边界；改匹配逻辑时要避免破坏已有短前缀配置。
- `core.export()` 每次都会重建 `docs/chapters/` 和 `docs/images/`，不要在这些目录里放手工维护的内容。
- `skills/mineru-book-pipeline/` 是给外部 AI agent 发布/安装的 Skill，修改流水线行为后要同步更新其中的 `SKILL.md` 或 `references/`。
