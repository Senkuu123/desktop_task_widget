# WORKLOG

## 2026-06-30

### 贴边隐藏 + 饮水小助手（本次会话）

改动文件：
- `task_window.py` — 添加QPoint/QTime导入；新增QSpinBox/QTimeEdit到QWidgets导入；__init__改为从storage加载water_reminder；initUI用self.water_reminder初始化WaterDisplayWidget；新增_should_rehide/_rehide_timer/_current_edge/_original_pos状态变量；mouseReleaseEvent末尾调用_check_near_edge/_hide_at_edge；toggle_window_topmost置顶时清_should_rehide并停rehide timer；check_deadline_notifications新增饮水提醒触发；show_deadline_notification新增msg_override参数；update_window_style新增饮水按钮样式同步；_WaterSettingsDialog新增is_enabled复选框和get_is_enabled()方法；新增7个贴边隐藏方法（_check_near_edge/_hide_at_edge/_on_hide_anim_done/_restore_from_edge/_on_restore_anim_done/_start_restore_timer/_stop_restore_timer/_check_cursor_near_hidden_edge）+ 3个再隐藏方法（_start_rehide_timer/_stop_rehide_timer/_check_rehide）
- `water_reminder.py` — 新增is_enabled字段（默认False），update_reminder和get_next_reminder_display在未启用时直接返回None/提示，to_dict/from_dict序列化is_enabled
- `add_habit_dialog.py` — 新建
- `habit.py` — 新建
- `storage.py` — 新增HABITS_FILE/WATER_FILE路径；新增save_habits_to_json/load_habits_from_json/save_water_reminder/load_water_reminder函数
- `build_simple.py` — required_files新增water_reminder.py

### Bug修复 + 饮水日志 + UI对齐

问题与修复：
1. 拖动离开边缘后仍自动隐藏 — mouseReleaseEvent在拖动结束且未靠近边缘时，清除_should_rehide并停止_rehide_timer
2. 饮水按钮文案 — "一杯"→"喝一杯"，"½杯"→"喝半杯"，"¼杯"→"抿一口"
3. 饮水设置对话框UI — 从暗色主题改为与AddTaskDialog一致的浅灰背景+绿色强调色+红色取消按钮；删除重复的旧代码（goal_spin/enable_cb/btn_row被追加了两遍）
4. 提醒时机 — update_reminder()改为在next_reminder_time到达时立即触发，不额外延迟
5. 饮水日志 — water_reminder.py新增today_logs列表，记录每笔{time/amount/type}；WaterDisplayWidget新增折叠日志面板（›按钮展开后显示﹀，QScrollArea滚动，最高160px）；每日重置时清空日志
6. 日志区域 — 最大高度160px（约4行），滚动条样式与主窗口一致（默认透明，悬停显示）
7. 重置按钮 — 设置对话框新增橙色"重置今日"按钮，点击即清零今日数据，即使取消也会保存重置结果
8. 完成提醒 — "恭喜"改为"真棒"
9. 日志面板定位 — 从VBoxLayout子元素改为绝对定位子widget（QWidget(self)），展开时从按钮下方下延160px覆盖下方内容，不移动按钮位置；resizeEvent中动态更新宽度和位置；背景改为rgba(40,40,40,0.95)半透明深色
10. 展开箭头 — "↓"改为"∨"（收起），展开后显示"∧"，font-weight加粗

待办：
- 用户需运行`python build_simple.py`打包测试

## 2026-06-30

### 任务/习惯页面切换 + 截止时间提醒

改动文件：
- `task_window.py` — 新增page_toggle_btn（📋/🔄）在➕和⚙️之间；新增current_page状态；toggle_page方法；refresh_task_display按页面路由；新增TaskListWidgetItem的mode='habit'分支；新增check_deadline_notifications/show_deadline_notification（winotify+MessageBoxW回退）
- `add_habit_dialog.py` — 新建
- `habit.py` — 新建
- `storage.py` — 新增习惯相关存储函数
- `build_simple.py` — 新增habit.py、add_habit_dialog.py、winotify隐藏导入
