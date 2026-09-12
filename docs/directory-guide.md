# 项目目录说明

目录按日常职责划分，统一使用英文名称。项目自有Python文件共38个：运行源码31个、开发与测试工具6个、废弃脚本1个。

## 先找哪个目录

| 需求 | 位置 |
|------|------|
| 运行现成软件 | `dist/quick-notes/DesktopTaskWidget.exe` |
| 修改软件功能 | `src/` |
| 打包exe | `tools/build/build_simple.py` |
| 运行自动测试 | `tools/tests/test_quick_notes.py` |
| 检查Windows焦点与快捷键 | `tools/tests/manual/` |
| 看软件使用方法 | `docs/user-guide.md` |
| 查数据格式 | `docs/notes-data.md` |
| 查需求和历史决策 | `docs/`及根目录`WORKLOG.md` |
| 找废弃脚本和旧产物 | `archive/` |

## 目录树

```text
desktop_task_widget_code/
├─ src/                         现版本源码
│  ├─ main.py                   启动入口
│  ├─ task_window.py            主窗口兼容入口
│  ├─ window_parts/             按功能拆分的主窗口实现及代码索引
│  ├─ ...                       模型、存储、对话框等运行模块
│  ├─ quick_notes/              快速便签模块
│  └─ resources/                app_icon.ico、images.qrc
├─ tools/                       开发和维护工具
│  ├─ build/
│  │  ├─ build_simple.py        打包命令入口
│  │  ├─ DesktopTaskWidget.spec PyInstaller配置
│  │  ├─ version_info.txt       exe版本元数据
│  │  ├─ dpi.manifest           Windows DPI清单
│  │  └─ cache/                 自动生成的构建缓存，不提交Git
│  ├─ tests/
│  │  ├─ test_quick_notes.py    便签与主窗口回归
│  │  ├─ test_window_parts.py   拆分后的类身份、信号及事件回归
│  │  └─ manual/               Windows专项验证
│  └─ maintenance/              clear_icon_cache.bat
├─ docs/                        使用说明、数据说明、需求及目录说明
├─ dist/quick-notes/             日常使用的exe及对应用户数据
├─ archive/                     历史归档
│  ├─ retired-scripts/          废弃Python脚本及分类依据
│  ├─ build/                    原build目录中的旧构建产物
│  ├─ exports/                  旧任务文本导出
│  └─ python-cache/             原根目录字节码缓存
├─ .venv/                       当前使用的Python环境
├─ venv/                        原有Python环境
├─ .git/                        Git版本历史
├─ .idea/                       IDE配置
├─ .gitignore                   Git忽略规则
├─ requirements.txt            运行依赖清单
├─ README.md                    项目入口与常用命令
├─ WORKLOG.md                   追加式工作记录
├─ AGENTS.md                    Codex项目规范
└─ CLAUDE.md                    Claude项目规范
```

源码运行后，任务、习惯、饮水、便签及设置文件还会出现在项目根目录，这是现有数据位置约定。exe使用`dist/quick-notes/`中的数据。

## 38个Python文件清单

| 分类 | 文件 | 说明 |
|------|------|------|
| 现用源码 | `src/main.py` | 程序启动、DPI、图标初始化 |
| 现用源码 | `src/task_window.py` | 兼容导出和直接运行入口 |
| 现用源码 | `src/task.py` | 任务模型 |
| 现用源码 | `src/habit.py` | 习惯模型 |
| 现用源码 | `src/water_reminder.py` | 饮水模型 |
| 现用源码 | `src/storage.py` | 任务、习惯、饮水、设置存储 |
| 现用源码 | `src/add_task_dialog.py` | 添加任务窗口 |
| 现用源码 | `src/edit_task_dialog.py` | 编辑任务窗口 |
| 现用源码 | `src/add_habit_dialog.py` | 添加习惯窗口 |
| 现用源码 | `src/autostart_manager.py` | 开机启动管理 |
| 现用源码 | `src/images_rc.py` | Qt编译资源，main显式导入 |
| 现用源码 | `src/quick_notes/__init__.py` | 便签包入口 |
| 现用源码 | `src/quick_notes/actions.py` | 便签菜单及历史窗口 |
| 现用源码 | `src/quick_notes/card.py` | 卡片与原位编辑 |
| 现用源码 | `src/quick_notes/dialog.py` | 新建便签与编辑浮窗 |
| 现用源码 | `src/quick_notes/hotkey.py` | 全局快捷键 |
| 现用源码 | `src/quick_notes/store.py` | JSONL存储及CSV导出 |
| 现用源码 | `src/quick_notes/legacy.py` | 旧SQLite与JSONL迁移，store条件导入，仍需打包 |
| 现用源码 | `src/window_parts/__init__.py` | 包标记 |
| 现用源码 | `src/window_parts/window.py` | 主窗口初始化、配置和置顶 |
| 现用源码 | `src/window_parts/layout.py` | 布局、样式和页面导航 |
| 现用源码 | `src/window_parts/tasks.py` | 任务操作与列表 |
| 现用源码 | `src/window_parts/interaction.py` | 绘制、鼠标、缩放及Qt事件 |
| 现用源码 | `src/window_parts/notes.py` | 主窗口便签入口 |
| 现用源码 | `src/window_parts/habits.py` | 习惯列表和日志同步 |
| 现用源码 | `src/window_parts/notifications.py` | 截止时间与饮水通知 |
| 现用源码 | `src/window_parts/edge_hide.py` | 贴边动画和定时器 |
| 现用源码 | `src/window_parts/task_item.py` | 任务和习惯行控件 |
| 现用源码 | `src/window_parts/water_widgets.py` | 饮水进度和操作控件 |
| 现用源码 | `src/window_parts/water_settings.py` | 饮水设置窗口 |
| 现用源码 | `src/window_parts/settings_dialog.py` | 样式与自启动设置窗口 |
| 打包工具 | `tools/build/build_simple.py` | 检查源码、生成缺失资源并调用PyInstaller |
| 自动测试 | `tools/tests/test_quick_notes.py` | 14项自动回归测试，使用临时数据 |
| 自动测试 | `tools/tests/test_window_parts.py` | 5项类身份、任务信号、事件分派、通知去重与跨日数据隔离测试 |
| 专项验证 | `tools/tests/manual/verify_window_edges.py` | Windows真实动画及定时器，鼠标逻辑坐标注入 |
| 专项验证 | `tools/tests/manual/verify_note_popup.py` | Windows焦点、固定及草稿检查 |
| 专项验证 | `tools/tests/manual/verify_note_hotkey.py` | 快捷键注册、事件投递和释放检查 |
| 历史废弃 | `archive/retired-scripts/create_version_info.py` | 已被当前打包脚本的内置生成器替代 |

两个虚拟环境里的Python文件属于第三方依赖，不计入38个自有文件。它们的目录结构和启动器可能依赖原路径，因此保留整个环境的位置。

## 移动后的路径约定

- 入口为`src/main.py`。主窗口实现已拆入`src/window_parts/`，先读该目录README按功能定位；`src/task_window.py`保持导入兼容。便签包内部结构保持完整。
- 图标与Qt资源定义移入`src/resources/`；重新生成的`images_rc.py`仍位于`src/`。
- spec、版本元数据和DPI清单集中在`tools/build/`。打包脚本根据自身位置定位项目，spec根据SPECPATH定位项目；输入路径为绝对路径。
- 新构建缓存位于`tools/build/cache/release/`。`archive/build/`仅保留旧构建记录，其中的历史spec不是现用入口。
- 源码数据、默认备份和默认导出定位项目根目录；冻结程序数据定位exe目录，资源定位PyInstaller目录。不会因启动时工作目录不同而改变这些位置。
- 自动测试和专项脚本均根据自身位置加入`src/`搜索路径。
- 归档版本生成器若被手动执行，输出到`tools/build/version_info.txt`，保留的是旧英文元数据；现用生成器在打包脚本内部。
- Git精确忽略`tools/build/cache/`、`archive/build/`和`archive/python-cache/`，打包源码与spec正常纳入版本控制。已有被跟踪的旧虚拟环境文件，本次不改其Git状态。
- 根目录README作为导航，完整使用说明放在`docs/user-guide.md`。历史WORKLOG中的旧路径保留当时语境。

## 验证说明

目录整理验证包含19项自动测试、38个文件语法解析、跨工作目录的导入和资源定位、数据目录断言、实际PyInstaller构建及入包模块核对。具体最终结果与验证产物位置记录在根目录WORKLOG中。
