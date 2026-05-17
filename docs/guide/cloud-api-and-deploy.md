# 云端抓取与部署

这一页覆盖两个有副作用的功能：

- `minerupress-fetch` 调用 MinerU 云端 API
- `cf_pages` 插件部署到 Cloudflare Pages

## MinerU 云端 API

如果你不想先在本地准备 MinerU 输出，而是希望直接上传 PDF 并拿回解析结果，可以在 `book.yml` 中配置 `api:`：

```yaml
api:
  token: ""
  enable_formula: true
  enable_table: true
  model_version: vlm
  sources:
    javaweb: resources/pdfs/javaweb.pdf
```

推荐把敏感信息放到 `.env`：

```bash
MINERU_API_TOKEN=...
```

然后执行：

```bash
minerupress-fetch book.yml
```

如果你要在工具链仓库里临时跑一本书，推荐先建一个被忽略的隔离工作区，再在里面执行 `minerupress-fetch`。完整示例见 [实战工作流](workflow-run-a-book.md)。

## `minerupress-fetch` 做了什么

它会：

1. 读取 `api.sources`
2. 对每个 PDF 调用 MinerU API
3. 如果页数超限，自动拆成多个 PDF 分片
4. 轮询直到解析完成
5. 下载 ZIP 结果并解压到 `mineru_root`
6. 把输出目录重命名为 `volume_uid_full` 或 `volume_uid_partN`
7. 清理同一 `volume_uid` 旧的 `full/part` 输出
8. 最后再走正常导出流程

## 推荐工作方式：先隔离，再抓取

如果 PDF 位于网盘目录、共享目录，或者你不希望把这本书的配置和生成物混进仓库根目录，推荐这样做：

1. 复制 `book_template/` 到独立目录，或仓库内的临时目录
2. 把源 PDF 复制到工作区内的 `resources/pdfs/`
3. 在工作区写 `.env` 和 `book.yml`
4. 运行 `minerupress-fetch book.yml`

这样做的好处：

- PDF 分片文件会写在当前工作区，不会尝试写回外部只读目录
- `resources/mineru/`、`docs/`、`site/`、`reports/` 都能和别的项目隔离
- 方便 AI agent 或脚本重复执行同一流程

## PDF 自动拆分

MinerU API 对单文件页数有限制。MineruPress 会在超限时自动拆分，并保证：

- 每个分片页数控制在安全阈值内
- `fetch()` 返回的目录顺序与 PDF 分片顺序一致
- 章节仍只需要使用原来的逻辑 `volume_uid`

这意味着你不需要在 `book.yml` 手工维护 `part1`、`part2` 之类的章节配置。

## `minerupress-export --fetch`

如果你已经有部分本地输出，但还想在导出前按 `api:` 补抓缺失或重抓内容，可以用：

```bash
minerupress-export --fetch book.yml
```

它的行为和 `minerupress-fetch` 类似，但命令入口仍然是导出命令。

## Cloudflare Pages 部署

启用 `cf_pages` 插件：

```yaml
plugins:
  - cf_pages

deploy:
  pages_project: my-book
  site_dir: site
  branch: main
  wrangler_cmd: npx wrangler
```

环境变量通常需要：

```bash
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
PAGES_PROJECT=my-book
```

说明：

- `pages_project` 可以写在 `deploy:` 中，也可以用 `PAGES_PROJECT`
- `CLOUDFLARE_API_TOKEN` 不存在时，插件会直接跳过部署
- 插件会先跑 `mkdocs build --strict`，构建失败就不会继续部署

## 部署时机

`cf_pages` 是 `on_export_done()` 阶段触发的，所以只要插件开启，执行一次 `minerupress-export` 就可能触发一次部署。

因此建议：

- 本地排查时先不要启用 `cf_pages`
- 或者至少不要在带生产凭据的环境里随手运行

## 什么时候不该用这些功能

以下场景建议先不要执行：

- 你还没确认 `book.yml` 章节边界是否稳定
- 你不确定 `.env` 里是否带着生产环境凭据
- 你只是想本地试验导出效果
- 你当前在 CI 或共享机器上，不希望消耗云端资源
