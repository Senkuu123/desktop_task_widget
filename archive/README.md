# 历史归档

此目录保留旧文件，现版本不依赖这里的源码或构建结果。

| 子目录 | 内容 |
|--------|------|
| `retired-scripts/` | 被现用打包脚本替代的独立版本信息生成器及归档依据 |
| `build/` | 原项目根目录build中的旧构建缓存、实验spec和第一轮目录验证产物 |
| `exports/` | 原根目录的历史任务文本导出 |
| `python-cache/` | 原根目录的Python字节码缓存 |

历史构建文件中的旧源码路径仅用于追溯当时的构建，不是现用打包入口。当前使用`tools/build/build_simple.py`；新的构建缓存写入`tools/build/cache/`。

`retired-scripts/create_version_info.py`保留可执行性，输出路径已同步；手动运行会覆盖`tools/build/version_info.txt`，其中仍是旧版英文元数据。现用打包脚本已内置中文版本信息生成器。
