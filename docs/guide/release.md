# 发布与分发

MineruPress 目前处于 `0.1.0` alpha 阶段。当前推荐安装方式是从 GitHub 开发安装：

```bash
git clone https://github.com/aronnaxlin/minerupress.git
cd minerupress
pip install -e ".[all]"
```

## 发布前检查

正式发布 Release 或 PyPI 包前，至少完成这些检查：

- `python -m compileall minerupress`
- `pytest`
- 用一个本地 MinerU fixture 跑 `minerupress-export`
- 用 `minerupress-headings` 验证章节边界草稿输出
- 确认 README、`docs/`、`skills/minerupress/` 已同步更新

## 构建包

推荐使用 `build`：

```bash
python -m pip install build twine
python -m build
twine check dist/*
```

## GitHub Release

建议流程：

1. 更新 `pyproject.toml` 里的版本号
2. 更新 README 或 changelog 中的用户可见变化
3. 创建 tag，例如 `v0.1.0`
4. 在 GitHub 创建 Release，附上安装方式和主要变化

## PyPI 发布

准备好 PyPI token 后再执行：

```bash
twine upload dist/*
```

发布后，README 的安装方式可以从开发安装逐步调整为：

```bash
pip install minerupress
```

可选依赖仍然保留：

```bash
pip install "minerupress[all]"
```
