# 主窗口代码索引

先按下表选择文件，再搜索关键方法。`../task_window.py`只负责兼容导出和直接运行入口；主程序仍使用`from task_window import TransparentTaskWindow`。

| 功能 | 文件 | 关键类／方法 |
| --- | --- | --- |
| 初始化、窗口配置、置顶 | `window.py` | `TransparentTaskWindow.__init__`、`setup_basic_window_properties`、`toggle_window_topmost`、`delayed_task_load`、`load_window_settings`、`save_window_settings` |
| 布局、样式、页面切换 | `layout.py` | `WindowLayoutMixin.initUI`、`_create_top_bar`、`update_window_style`、`show_page`、`show_add_dialog`、`create_water_cup_icon` |
| 文件夹快捷访问、折叠、菜单排序 | `folder_shortcuts.py` | `FolderShortcuts`、`FolderGrid`、`FolderDelegate` |
| 任务增改、排序、完成、存储调用 | `tasks.py` | `WindowTasksMixin.refresh_task_display`、`on_item_double_clicked`、`on_task_status_changed`、`_check_and_update_urgency`、`load_tasks`、`save_tasks` |
| 绘制、拖动、缩放、光标、Qt事件 | `interaction.py` | `WindowInteractionMixin.mousePressEvent`、`mouseMoveEvent`、`mouseReleaseEvent`、`resizeEvent`、`eventFilter`、`closeEvent` |
| 便签加载、列表、编辑、快捷记录 | `notes.py` | `WindowNotesMixin.load_notes`、`refresh_notes_display`、`update_inline_note`、`show_quick_note`、`save_quick_note` |
| 习惯添加、完成、编辑、日志 | `habits.py` | `WindowHabitsMixin.refresh_habit_display`、`on_habit_status_changed`、`on_habit_double_clicked`、`_sync_habit_log` |
| 截止时间及饮水通知 | `notifications.py` | `WindowNotificationsMixin.check_deadline_notifications`、`show_deadline_notification` |
| 贴边隐藏、恢复动画、悬停检测 | `edge_hide.py` | `WindowEdgeHideMixin._hide_at_edge`、`_restore_from_edge`、`_cursor_in_edge_trigger`、`_check_rehide`、`_check_pending_hide` |
| 任务／习惯行控件与信号 | `task_item.py` | `TaskListWidgetItem`、`_get_parent_window`、`update_text_style`、`on_checkbox_changed` |
| 饮水进度、喝水操作、今日记录 | `water_widgets.py` | `WaterProgressBar`、`WaterDisplayWidget`、`update_countdown`、`_on_drink`、`show_settings` |
| 饮水设置对话框 | `water_settings.py` | `_WaterSettingsDialog`、`_do_reset`、`get_active_range`、`get_quiet_range` |
| 窗口样式与自启动设置对话框 | `settings_dialog.py` | `SettingsDialog`、`on_autostart_changed`、`get_settings` |

## 依赖与修改边界

- `window.py`组合各个普通Mixin，最后继承`QWidget`。全部主窗口初始化保留在`TransparentTaskWindow.__init__`，Mixin没有构造函数。
- Mixin通过`self`调用其他功能的方法，共享同一个窗口实例。每个主窗口方法只在一个模块中定义，Qt事件中的`super()`沿继承顺序到达`QWidget`。
- 布局依赖饮水控件和设置对话框；任务与习惯模块依赖任务行控件；饮水控件依赖饮水设置对话框。
- `task_item.py`仅在`_get_parent_window`内部导入`window.py`的主窗口类，避免循环导入。不要从兼容入口反向导入实现依赖，也不要定义第二份主窗口类。
- `__init__.py`保持为空，导入包本身不会主动加载窗口实现。
- 数据读写仍由`../storage.py`和`../quick_notes/`处理。本目录不修改数据位置，源码数据仍在项目根目录，发布数据仍在exe同目录。
- `SettingsDialog`原有两个`update_autostart_status`定义按原顺序保留，后者生效。本次只拆分文件，未清理重复代码。

## 打包与验证入口

在项目根目录运行`python src/main.py`启动软件；`python src/task_window.py`保留原直接运行方式。打包入口为`python tools/build/build_simple.py`，其必需文件清单包含本包全部Python模块，spec通过`src`搜索路径收集静态导入。

自动验证位于`tools/tests/`。修改贴边逻辑时，除坐标检查外还须验证实际Windows Qt动画和定时器，覆盖持续悬停和移出再隐藏。
