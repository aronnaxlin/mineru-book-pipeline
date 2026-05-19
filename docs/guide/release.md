# 发布与分发

MineruPress 已具备标准 Python 包分发能力。对最终用户，推荐使用发布包安装；对维护者，保留 GitHub 开发安装。

用户安装：

```bash
pip install "minerupress[all]"
```

CLI 隔离安装：

```bash
pipx install 'minerupress[all]'
```

维护者开发安装：

```bash
git clone https://github.com/aronnaxlin/minerupress.git
cd minerupress
pip install -e ".[all]"
```

## 发布前检查

正式发布 Release 或 PyPI 包前，至少完成这些检查：

- `python -m compileall minerupress`
- `pytest`
- 用一个本地 MinerU fixture 跑 `minerupress export`
- 用 `minerupress headings` 验证章节边界草稿输出
- 确认 README、`docs/`、`skills/minerupress/` 已同步更新

## 构建包

推荐使用 `build`：

```bash
python -m pip install build twine
python -m build
twine check dist/*
```

构建结果会出现在：

- `dist/*.whl`
- `dist/*.tar.gz`

## GitHub Release

建议流程：

1. 更新 `pyproject.toml` 里的版本号
2. 更新 README 或 changelog 中的用户可见变化
3. 创建 tag，例如 `v0.1.0`
4. push tag，让 GitHub Actions 自动构建发行包并附到对应 GitHub Release
5. 发布 GitHub Release，让 PyPI 发布工作流继续执行

建议在 Release 说明中直接给用户放这两种安装方式：

```bash
pip install "minerupress[all]"
```

或：

```bash
pipx install 'minerupress[all]'
```

## PyPI 发布

仓库工作流建议使用 PyPI Trusted Publishing。准备好 PyPI 项目后：

- 在 PyPI 项目里配置 trusted publisher
- 在 GitHub 仓库中创建 `pypi` Environment
- 将 GitHub Release 发布动作作为 PyPI 发布触发器
- 由 GitHub Actions 自动执行发布，不再要求本地手工 `twine upload`

当前仓库约定：

- workflow 文件名：`release.yml`
- GitHub Environment：`pypi`
- 发布 job：`publish-pypi`

### 第一次配置教程

1. 在 GitHub 仓库进入 `Settings -> Environments`
2. 新建 environment，名称填 `pypi`
3. 如果你想手动确认每次正式发版，可以给这个 environment 加 `Required reviewers`
4. 在 PyPI 项目的 Trusted Publisher 里确认这些值一致：
   - Owner: `aronnaxlin`
   - Repository: `minerupress`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
5. 回到仓库，确认 [release.yml](/Users/aronnax/dev/mineru-book-pipeline/.github/workflows/release.yml:1) 中 `publish-pypi` job 使用了同名 environment

### 首次发版检查清单

- `pyproject.toml` 版本号已更新
- `README.md`、`docs/`、`skills/minerupress/` 已同步
- `python -m compileall minerupress` 通过
- `pytest` 通过
- GitHub `CI` workflow 是绿色
- PyPI Trusted Publisher 已绑定到 `release.yml`
- GitHub `pypi` Environment 已创建
- 你准备发布的 tag 形如 `v0.1.0`

### 实际发布步骤

1. 合并准备发布的改动
2. 更新版本号并提交
3. 创建并推送 tag：

```bash
git tag v0.1.0
git push origin v0.1.0
```

4. 到 GitHub `Releases` 页面创建或发布 `v0.1.0`
5. 等待 `Release` workflow：
   - `build` job 生成 `wheel` 和 `sdist`
   - `publish-pypi` job 通过 Trusted Publishing 上传到 PyPI
6. 发布完成后，用下面命令做烟雾验证：

```bash
pip install -U "minerupress[all]"
minerupress --help
```

如果临时需要手工发布，仍可执行：

```bash
twine upload dist/*
```

发布后用户升级方式：

```bash
pip install -U "minerupress[all]"
```

## 自动化建议

建议至少保留两条工作流：

- `ci.yml`：每次 push / PR 做 `compileall` 和 `pytest`
- `release.yml`：tag 或 Release 触发，自动构建 `wheel` / `sdist`，上传到 GitHub Release，并在发布 Release 时推送到 PyPI

这样用户就不需要通过 `git pull` 获取新版本，而是直接：

- `pip install -U minerupress`
- `pipx upgrade minerupress`
