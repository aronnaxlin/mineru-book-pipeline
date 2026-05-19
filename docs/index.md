# MineruPress 文档

MineruPress 是一条把 MinerU 解析结果整理成 MkDocs Material 在线图书的发布流水线。它解决的不是单次 PDF 转 Markdown，而是一本书从原始解析结果到长期可维护站点之间的整条链路：

- 读取 `book.yml`
- 发现一个或多个逻辑分册
- 按章节边界切分内容
- 复制图片并生成 `docs/chapters/*.md`
- 调用插件做文本、图片、整章和导出完成后的处理

## 适用场景

- 教材或讲义转在线阅读站点
- 内部培训资料和手册发布
- 多 PDF、分片 PDF 的统一编排
- 需要 AI agent 稳定重复执行的文档生产流程

## 核心术语

- `volume_uid`：逻辑分册标识。章节配置写的是逻辑 UID，不必关心 API 自动拆出的 `part1`、`part2` 目录名。
- `mineru_root`：MinerU 输出根目录，默认是 `resources/mineru/`。
- `docs_out`：生成给 MkDocs 使用的文档目录，默认是 `docs/`。
- `toc_max_page`：查找每个逻辑分册第一个章节边界时，跳过前几页目录页的阈值。
- `allow_missing_boundaries`：是否允许找不到章节边界时继续导出。

## 功能地图

- [English README](README_EN.md)：面向英文读者的仓库总览。
- [快速开始](guide/getting-started.md)：安装、初始化工作区、第一次导出。
- [安装与升级](guide/install-and-upgrade.md)：`pip` / `pipx` 安装、升级、开发安装与卸载。
- [实战工作流](guide/workflow-run-a-book.md)：基于一本文档从 PDF 抓取、切章、建站到校验的完整流程。
- [配置详解](guide/configuration.md)：`book.yml` 字段说明、章节边界控制、路径解析规则。
- [导出流程](guide/export-pipeline.md)：导出器如何发现分册、处理图片、转换 item、生成输出。
- [插件系统](guide/plugins.md)：内置插件、自定义插件、hook 生命周期。
- [云端抓取与部署](guide/cloud-api-and-deploy.md)：`minerupress fetch`、自动拆 PDF、Cloudflare Pages。
- [校验、指纹与排障](guide/validation-and-troubleshooting.md)：严格构建、指纹、常见问题排查。
- [发布与分发](guide/release.md)：GitHub Release 与 PyPI 发布前检查。

## 使用原则

- 把书籍差异留在 `book.yml` 或插件中，不要硬编码到导出引擎。
- 生成后的 `docs/chapters/` 和 `docs/images/` 会被重建，不适合手工长期维护。
- 涉及上传、部署、云端消耗的动作要谨慎，确认配置无误再执行。
- 仓库根目录里的具体书稿工作区应放到 `local_book_workspace/` 这类被忽略的目录，避免和项目文档混在一起。
