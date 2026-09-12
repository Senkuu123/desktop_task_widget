# 历史废弃Python文件

此目录保存已被现有实现替代的脚本，不参与现版本运行或打包。

| 文件 | 原位置 | 废弃依据 |
|------|--------|----------|
| `create_version_info.py` | 项目根目录 | 当前`tools/build/build_simple.py`已内置版本信息生成；现有`version_info.txt`采用内置生成器的中文元数据。独立脚本没有调用方，保留的是旧版英文元数据。 |

归档日期：2026-09-12。脚本的输出路径已适配新位置，手动运行会覆盖`tools/build/version_info.txt`，平时使用现版本打包工具即可。

`src/quick_notes/legacy.py`仍用于只读迁移旧SQLite和旧JSONL数据，属于现版本依赖，不归档。
