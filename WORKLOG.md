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

## 2026-09-09 09:54

新增快速便签。
- 主窗口增加便签列表切换按钮和便签页添加入口；Ctrl＋Alt＋N全局唤起，Enter保存，Shift＋Enter换行，Esc收起并保留本次运行草稿。
- quick_notes目录包含输入窗口、Windows原生快捷键和持久化模块。SQLite事务同时保存便签与创建日志，notes_log.jsonl提供可读日志；导出失败可重建，不诱导重复保存。
- 列表展示创建时间和内容摘要，双击查看及复制全文。保存成功有短提示，读写失败给出数据目录。
- 验证：5项隔离自动化测试通过；Windows注册、冲突、原生事件投递、退出释放验证通过；按主程序DPI配置渲染并检查输入窗口和列表；git diff --check通过。中文输入法组合态由测试事件模拟，未完成真实输入法选词与其他应用间切换的手工验收。
- 代码审查无阻断项；体验审查指出错误提示缺路径，已修复，并补充隐藏主窗口时的保存反馈。
- 构建产物：dist/quick-notes/DesktopTaskWidget.exe。使用原spec打包成功，原spec的winotify.notification隐藏导入仍有未找到提示，本次未改旧通知逻辑。新版exe尚未人工启动验收。
- 使用说明：README.md。验收约定：docs/quick-notes-ac.md。测试：tests/test_quick_notes.py、tests/verify_note_hotkey.py。
- 本机venv目录解释器引用已失效，实际使用.venv/Scripts/python.exe；测试进程加-X utf8以兼容已有启动日志中的emoji。

## 2026-09-09 10:26

按flomo截图调整快捷便签弹窗。
- quick_notes/dialog.py改为白底无边框460×480，中文标题和占位文案，固定/关闭图标、纯文本标签及列表工具、灰色空态和绿色可发送按钮。标题区域可拖动。
- 删除弹窗快捷键说明及task_window.py便签列表的双击查看和复制全文说明。
- 默认失焦或点击应用内外部区域时收起，保留草稿；固定后保持展开。右键菜单关闭后重新检查焦点，避免菜单边界漏收起。
- 7项隔离回归测试通过，Windows Qt激活切换、固定、草稿恢复、菜单后外部点击验证通过；外部点击测试使用Qt事件，未做真实鼠标跨进程手工验收。截图按主程序DPI配置检查，体验静态审查通过。
- 构建目标：dist/quick-notes/DesktopTaskWidget-flomo.exe，与旧版同目录共用数据，先退出旧版再运行。操作说明已更新README.md。
- 新增tests/verify_note_popup.py验证焦点交互。临时spec放在build目录，使用绝对输入路径以避免PyInstaller按spec位置查找main.py失败。

## 2026-09-09 10:53

调整便签弹窗边框、缩放和置顶状态。
- quick_notes/dialog.py使用透明窗口背景自绘白底细边框，按用户补充将圆角收小到6px。
- 支持拖动四边与四角缩放，最小320×300；左/上边缩小时保持对侧位置，退出缩放后释放鼠标并恢复光标。
- 置顶图钉改绿色实心并移除选中底色。底部按钮置顶时透明度为18%，悬停恢复，仍可点击。
- 9项回归测试通过，包含拖动放大、缩小下限、淡化后悬停和保存；Windows焦点切换测试通过，已检查正常尺寸和最小尺寸截图。
- 本轮局部弹窗调整由本体实现和自检，未另派reviewer。说明与验收文档已更新。
- 新版产物：dist/quick-notes/DesktopTaskWidget-flomo-v2.exe；先退出旧版再运行，同目录数据继续使用。

## 2026-09-09 10:56

将quick_notes/dialog.py弹窗边框由深灰改为浅灰#d9d9d9，保留1px线宽和6px圆角。纯颜色调整，静态自检，不重复运行交互测试。新版输出dist/quick-notes/DesktopTaskWidget-flomo-v3.exe，README入口同步更新。

## 2026-09-09 11:00

更新打包脚本并创建源码Git快照。
- build_simple.py检查便签模块和spec，使用当前Python解释器调用PyInstaller，固定项目路径，输出dist/quick-notes/DesktopTaskWidget.exe；移除删除build和dist的旧逻辑，避免误删exe旁的数据，失败返回非零状态。
- DesktopTaskWidget.spec移除不存在的winotify.notification隐藏导入，并实际嵌入dpi.manifest。README已更新打包命令与固定产物路径。
- 已通过新脚本完成实际构建，生成54.38MB的exe；git diff --check通过。
- 快照范围为当前源码、项目规范、验收文档、测试和工作日志，个人任务/饮水/窗口数据及IDE配置不提交；构建产物留在dist目录。

## 2026-09-09 11:09

便签弹窗增加轻微外阴影。
- quick_notes/dialog.py预留12px透明边距，叠加柔和灰黑阴影并略向下偏移；保留浅灰边框与6px圆角，可见输入区域尺寸不变。
- 缩放热区随阴影边距调整；9项回归测试通过，已渲染检查阴影效果。
- 使用build_simple.py更新dist/quick-notes/DesktopTaskWidget.exe，README同步说明；本次改动未另建Git提交。

## 2026-09-09 16:45

按用户要求将便签阴影代码、README和工作日志保存为本地Git快照；个人数据和IDE配置继续留在工作区。

## 2026-09-09 17:19

主窗口标题、便签卡片和原位编辑。
- 左上角新增白色当前列表名：待办事项、快捷便签、饮水小助手。移除便签数量行，保留空态和错误提示。
- 新增quick_notes/card.py，深色卡片间隔分明，灰色小号创建时间在上。双击原位编辑显示绿边、计数、取消和保存；Enter保存、Shift＋Enter换行、Esc取消。
- 卡片增量刷新保留编辑焦点，草稿独立保存在主窗口，页面切换后恢复。保存失败保留正文，取消恢复原文。
- quick_notes/store.py新增事务编辑接口及edit_log，保留原创建记录和排序，日志导出包含修改前后内容。打包脚本补充card.py检查。
- 10项隔离测试通过，覆盖修改日志、回滚、跨页草稿、失败重试、取消及100行便签阅读/编辑；Windows Qt截图检查普通、编辑和300px窄窗口。
- 代码审查通过；体验审查发现长卡片按条目滚动会跳过正文，已改连续像素滚动，并在进入编辑后滚动到可见位置，定点复核通过。
- README和docs/quick-notes-ac.md更新。产物dist/quick-notes/DesktopTaskWidget.exe通过build_simple.py生成；本轮未创建Git提交。

## 2026-09-09 17:24

按用户要求将列表标题、便签卡片和原位编辑功能保存为本地Git快照；个人数据和IDE配置留在工作区。

## 2026-09-09 22:30

移除主窗口左上角列表名称，拆分待办事项、饮水小助手（水滴）、快捷便签三个固定入口，重复点击保持当前列表。同步README和验收说明。
- 10项测试断言通过，覆盖按钮点击、选中状态和草稿保留；第二次测试结束后进程未退出，已中止该进程，独立打包成功。
- 小范围导航组件调整采用本体自检，未另派审查。git diff --check通过。
- 更新产物：dist/quick-notes/DesktopTaskWidget.exe。本轮未创建Git提交。

## 2026-09-09 22:38

待办事项与快捷便签合并为切换按钮，显示当前列表原图标，置于新增与饮水按钮之间；饮水页点击返回最近使用的内容页。饮水按钮改为绘制的蓝色水面水杯。
- 同步README、验收说明及导航测试；10项断言通过，测试进程退出阶段仍未结束，已中止，退出异常尚未定位。
- 小范围组件改动由本体自检，git diff --check通过；独立打包成功，产物dist/quick-notes/DesktopTaskWidget.exe。未创建Git提交。

## 2026-09-09 22:48

按用户要求保存导航按钮调整的本地Git快照，包含移除列表标题、待办与便签合并切换、水杯图标及相关测试和文档；个人数据与IDE配置保留在工作区。

## 2026-09-10 09:08

检查便签存储与卡片实现，记录操作菜单、归档、历史版本、改日期及看板数据方案至docs/notes-actions-plan.md，待确认实施。明确SQLite为主数据，JSONL为重新生成的日志导出。尚未修改程序或真实数据库。

## 2026-09-10 09:41

完成便签操作菜单与纯文件存储。
- 卡片右侧三个点：编辑、列表置顶/取消置顶、弹出浮窗、归档、更多（历史版本、修改日期）、红色删除。浮窗编辑原记录并隔离新建草稿。
- JSONL为事件主文件，锁保护及原子替换；归档记录时间正文并隐藏，不提供恢复或归档列表。软删除留日志。展示日期时间可改，真实创建时间不变。CSV导出当前状态排除归档。
- 旧SQLite只读迁移并保留，旧JSONL迁移前备份；兼容旧空库空日志。说明见docs/notes-data.md，验收见docs/pm-notes-actions-ac.md。未访问或迁移真实用户数据。
- 14项隔离测试通过，包含迁移、原子写失败、CSV失败、日期/置顶/归档/删除、浮窗修改及菜单。主动清理测试Qt窗口后测试进程正常退出，未据此认定此前截图来源。
- 代码审查发现提交后再读取失败可能误报保存失败并造成重试重复，已改用提交返回状态更新内存，定点复核通过。Windows实际Qt渲染检查菜单和卡片。
- build_simple.py增加actions.py和legacy.py检查，成功生成dist/quick-notes/DesktopTaskWidget.exe（54.40MB）。本轮未创建Git快照。
- 用户询问token消耗：本会话长历史、规则/源码重复读取和多代理往返增加上下文；无逐项账单可精确量化，后续使用定点读取和工作日志减少重复。

## 2026-09-10 10:25

主窗口最小高度由400改为267（约原来的2/3），宽度仍为300。隔离验证待办、便签、饮水三页均可缩至300×267；小范围调整本体自检，打包程序已更新。

## 2026-09-10 10:46

按用户要求，在饮水布局修复前保存当前便签菜单、纯文件存储和267最小高度版本为本地Git快照。个人数据与IDE配置不提交。
