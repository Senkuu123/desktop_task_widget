# 桌面任务小组件

Windows桌面任务、习惯、饮水提醒和快速便签工具。

## 目录导航

| 目录 | 放什么 | 常用入口 |
|------|--------|----------|
| [src/](src/) | 现版本18个Python源码文件及图标资源 | [main.py](src/main.py) |
| [tools/](tools/) | 打包、自动测试、Windows专项检查和维护工具 | [打包脚本](tools/build/build_simple.py) |
| [docs/](docs/) | 软件使用说明、数据说明、需求记录和目录说明 | [使用说明](docs/user-guide.md)、[完整目录说明](docs/directory-guide.md) |
| [dist/quick-notes/](dist/quick-notes/) | 日常运行的exe及它的数据 | [DesktopTaskWidget.exe](dist/quick-notes/DesktopTaskWidget.exe) |
| [archive/](archive/) | 废弃脚本、旧构建缓存、旧导出文件 | [归档说明](archive/README.md) |

`.venv/`是当前使用的Python环境，`venv/`是原有环境。两者包含第三方依赖，保持原位置。`.git/`保存版本历史，`.idea/`保存IDE设置。

## 常用操作

日常使用：双击`dist/quick-notes/DesktopTaskWidget.exe`。

在项目根目录的PowerShell中执行：

```powershell
# 从源码启动
.\.venv\Scripts\python.exe -X utf8 src/main.py

# 打包，更新dist/quick-notes/DesktopTaskWidget.exe
.\.venv\Scripts\python.exe -X utf8 tools/build/build_simple.py

# 自动回归测试，使用临时数据
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tools/tests -v
```

打包前退出目标exe。依赖清单见[requirements.txt](requirements.txt)，操作细节见[使用说明](docs/user-guide.md)。

## 数据与记录

源码运行时，数据保存在项目根目录；exe运行时，数据保存在exe同目录。便签主文件为`notes_log.jsonl`。

[WORKLOG.md](WORKLOG.md)按时间追加项目工作记录。[AGENTS.md](AGENTS.md)和[CLAUDE.md](CLAUDE.md)供开发助手读取。
