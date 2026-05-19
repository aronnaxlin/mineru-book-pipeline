# 快速开始

## 环境要求

- Python `>=3.11`
- 推荐安装 `mkdocs` 和 `mkdocs-material`
- 如果要用二维码过滤或中西文间距处理，安装对应可选依赖

推荐在发布版可用后这样安装：

```bash
pip install "minerupress[all]"
pip install mkdocs mkdocs-material
```

如果你更喜欢独立 CLI 环境，也可以用 `pipx`：

```bash
pipx install 'minerupress[all]'
pipx inject minerupress mkdocs mkdocs-material
```

如果你是在开发工具链本身，而不是普通使用，请改看 [安装与升级](install-and-upgrade.md) 里的开发安装一节。

## 创建一本新书工作区

MineruPress 仓库本身是工具链，不建议把真实图书内容直接塞进仓库根目录。更稳妥的做法是复制模板到单独目录：

```bash
cp -r book_template/ ~/dev/my-book/
cd ~/dev/my-book/
```

模板里包含：

- `book.yml`：导出配置
- `mkdocs.yml`：站点配置
- `.env.example`：环境变量示例
- `Makefile`：常用命令包装

## 准备输入数据

本地导出场景下，把 MinerU 的输出目录放到：

```text
resources/mineru/
```

每个分册目录下通常应包含：

- `*_content_list.json`
- `images/`

如果同一个逻辑分册被拆成多个物理目录，也没关系。只要它们目录名前缀都能匹配到同一个 `volume_uid`，导出器就会按自然顺序接起来处理。

## 第一次导出

1. 编辑 `book.yml`
2. 按章节填写 `slug` 和 `title`
3. 运行导出

```bash
minerupress export book.yml
```

导出结果默认会写到：

- `docs/chapters/`
- `docs/images/`

然后用 MkDocs 本地预览：

```bash
mkdocs serve
```

如果你是从一份原始 PDF 开始，而不是已经有本地 MinerU 输出，建议直接按 [实战工作流](workflow-run-a-book.md) 里的“隔离工作区 + `minerupress fetch`”路线操作。

## 常见命令

本地导出：

```bash
minerupress export book.yml
```

已有 API 配置时，先抓取再导出：

```bash
minerupress fetch book.yml
```

已有部分本地输出，希望先补抓再导出：

```bash
minerupress export --fetch book.yml
```

严格构建检查：

```bash
mkdocs build --strict
```

生成文档指纹：

```bash
minerupress fingerprint --docs-dir docs --out reports/fingerprints.json
```

## 目录建议

一个典型图书工作区通常长这样：

```text
my-book/
├── .env
├── book.yml
├── mkdocs.yml
├── docs/
├── resources/
│   ├── mineru/
│   └── pdfs/
├── reports/
└── site/
```

其中：

- `docs/`、`site/`、`reports/` 通常是生成物
- `.env` 放敏感配置，不要提交
- `resources/mineru/` 放 MinerU 输出
- `resources/pdfs/` 常用于云端 API 上传源 PDF

## 从任意目录执行

所有相对路径都以 `book.yml` 所在目录解析，因此下面这种调用是安全的：

```bash
minerupress export /absolute/path/to/my-book/book.yml
```

这意味着你不需要依赖当前 shell 所在目录来保证配置正确解析。
