# mineru-book-pipeline

通用 MinerU → MkDocs Material 导出工具链，支持插件扩展。

## 安装

```bash
pip install -e ".[all]"   # 包含 QR 过滤和 CJK 间距插件
```

依赖项：

| 功能 | 额外依赖 |
|---|---|
| QR 过滤 | `opencv-python` |
| CJK 间距 | `pangu` |
| 两者都要 | `pip install -e ".[all]"` |

## 新书快速开始

```bash
# 1. 复制模板
cp -r book_template/ ~/dev/my-new-book/
cd ~/dev/my-new-book/

# 2. 填写 book.yml（章节、volume_uid、start_pattern）
# 3. 填写 mkdocs.yml（site_name、nav）

# 4. 导出
mineru-export book.yml

# 5. 预览
mkdocs serve
```

## book.yml 格式

```yaml
mineru_root: resources/mineru   # MinerU 输出根目录
docs_out: docs                  # MkDocs docs/ 目录
toc_max_page: 10                # 目录页最大页码（之前的标题匹配忽略）

plugins:
  - qr_filter                   # 内置：过滤课程二维码
  - cjk_spacing                 # 内置：中英文间距
  # - mypackage.MyPlugin        # 自定义：dotted import 路径

chapters:
  - slug: ch01-intro            # 输出文件名（不含 .md）
    title: 第1章 绪论           # 显示标题
    volume_uid: 73d5b3e7        # MinerU 输出目录名中的 UUID 前缀
    start_pattern: "^第\\s*1\\s*章"  # 匹配章节首行的正则
```

`volume_uid` 只需填 UUID 的前 8 位，pipeline 会自动在 `mineru_root` 下匹配。

## 自定义插件

继承 `ExportPlugin`，覆盖需要的钩子：

```python
from mineru_pipeline import ExportPlugin

class MyPlugin(ExportPlugin):
    def on_image(self, item: dict, img_path) -> bool:
        # 返回 False 丢弃图片
        return True

    def on_text(self, item: dict, text: str) -> str:
        # 返回处理后的文本
        return text.replace("旧词", "新词")

    def on_chapter_done(self, slug: str, lines: list[str]) -> list[str]:
        # 对整章做后处理
        return lines
```

在 `book.yml` 中引用：

```yaml
plugins:
  - mypackage.mymodule.MyPlugin
```

## 内置插件

### QRFilterPlugin

用 OpenCV `QRCodeDetector.detect()` 检测二维码 finder pattern（不依赖解码成功）。
`max_side` 参数控制最大边长阈值（默认 250px），超过此尺寸的图片不做检测。

### CJKSpacingPlugin

用 `pangu` 在中文和 ASCII 字符之间插入空格。
`$...$` 和 `$$...$$` 内的 LaTeX 内容受保护，不会被插入空格。

## 项目结构

```
mineru_pipeline/
├── core.py          # 导出引擎
├── loader.py        # book.yml 解析器
├── cli.py           # mineru-export 命令行入口
├── fingerprint.py   # SHA-256 内容指纹
└── plugins/
    ├── base.py          # ExportPlugin 基类
    ├── qr_filter.py     # QR 过滤插件
    └── cjk_spacing.py   # CJK 间距插件

book_template/
├── book.yml         # 配置模板
├── mkdocs.yml       # MkDocs Material 模板
└── Makefile         # 标准流水线 targets
```
