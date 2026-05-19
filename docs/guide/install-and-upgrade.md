# 安装与升级

这一页面向两类人：

- 使用 MineruPress 处理图书工作区的普通用户
- 需要修改 MineruPress 自身代码的开发者

## 环境要求

- Python `>=3.11`
- 如果要本地预览站点，额外安装 `mkdocs` 和 `mkdocs-material`
- 如果要用 `qr_filter` 或 `cjk_spacing`，安装 `minerupress[all]`

## 普通安装：`pip`

最直接的方式是安装 PyPI 发布包：

```bash
pip install "minerupress[all]"
pip install mkdocs mkdocs-material
```

适用场景：

- 你只是想使用 `minerupress export`、`minerupress fetch` 这类命令
- 你不需要修改 MineruPress 自身源码
- 你希望升级时直接 `pip install -U ...`

升级：

```bash
pip install -U "minerupress[all]"
```

卸载：

```bash
pip uninstall minerupress
```

## 推荐 CLI 安装：`pipx`

如果你希望 CLI 独立于当前 Python 项目环境，推荐使用 `pipx`：

```bash
pipx install 'minerupress[all]'
pipx inject minerupress mkdocs mkdocs-material
```

这样 `minerupress` 会安装到独立虚拟环境里，不容易和你的图书工作区依赖打架。

升级：

```bash
pipx upgrade minerupress
pipx inject minerupress mkdocs mkdocs-material --include-apps
```

卸载：

```bash
pipx uninstall minerupress
```

## 开发安装：GitHub 仓库

如果你要改工具链本身，而不仅仅是使用它，才需要 clone 仓库：

```bash
git clone https://github.com/aronnaxlin/minerupress.git
cd minerupress
pip install -e ".[all]"
```

如果你还要跑测试：

```bash
pip install -e ".[dev]"
```

这类安装适合：

- 修改 CLI、导出逻辑、插件系统
- 本地调试未发布改动
- 提交 PR 或维护 Release

## MkDocs 依赖说明

MineruPress 本身负责导出，不强依赖 MkDocs。只有当你要：

- 本地预览站点
- 执行 `mkdocs build --strict`
- 使用 `cf_pages` 插件部署

才需要额外安装：

```bash
pip install mkdocs mkdocs-material
```

## 关于本地 MinerU 工具链

`source: local_toolchain` 不会把 MinerU 内置进 MineruPress 包里。  
如果你要走本地 `mineru` CLI，请按 MinerU 官方文档单独安装：

```bash
uv pip install -U "mineru[all]"
```

MinerU 的按需扩展、轻量客户端、Docker、源码开发安装和 CLI 参数会随官方版本变化，更多安装模式见：

- [MinerU Quick Start](https://opendatalab.github.io/MinerU/quick_start/)
- [MinerU Extension Modules](https://opendatalab.github.io/MinerU/quick_start/extension_modules/)
- [MinerU CLI Tools](https://opendatalab.github.io/MinerU/usage/cli_tools/)

## 安装后快速检查

确认 CLI 可用：

```bash
minerupress --help
minerupress init --help
minerupress export --help
```

如果你已经准备好一个图书工作区，可以继续：

```bash
minerupress init my-book
cd my-book
mkdocs serve
```

模板默认 `source: uploaded_result`。已有 MinerU 输出时，把结果放到 `resources/mineru/` 后执行：

```bash
minerupress export book.yml
```

只有 PDF 时，先在 `book.yml` 里选择 `official_api` 或 `local_toolchain`，再执行：

```bash
minerupress fetch book.yml
```

如果你是维护者，准备首次正式发版时再看：

- [发布与分发](release.md)

## 常见选择建议

- 普通用户：优先 `pip install` 或 `pipx install`
- 长期命令行使用者：优先 `pipx`
- 贡献者或维护者：使用 GitHub 开发安装
