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

## 2026-09-10 10:55

修复饮水区域缩小时裁切，并拆分习惯列表。
- 修改前快照919407f，保留便签菜单/JSONL/267高度版本。新最小高度280，宽度300。
- 根因：饮水主要控件、固定96高记录区和习惯列表争用高度。现在饮水主操作区固定完整高度，记录使用剩余空间可收缩滚动；空间极小时隐藏次要饮水统计，保留标题、进度条、倒计时和三个按钮。
- 新增water独立页，habits仅显示习惯任务。水杯/蓝底白色循环图标切换两页，跨组返回最近访问页。饮水页＋打开饮水设置。
- 14项隔离测试通过，含280高度、记录展开收起、核心区域边界及页面切换；Windows高DPI实际渲染确认主要按钮完整。单组件布局改动由本体自检。
- README及验收说明更新，dist/quick-notes/DesktopTaskWidget.exe打包成功。按用户要求保存修改后快照，个人数据与IDE配置不提交。

## 2026-09-10 11:10

习惯按钮替换为用户指定的🔄，与旁边emoji使用同一字体基线；删除原手绘循环图标。水杯图案向下补偿约1个逻辑像素。验证各按钮几何中心同高，Windows高DPI截图核对视觉位置。14项测试通过，本体自检，打包exe已更新。未创建新Git提交。

## 2026-09-10 11:12

按用户要求保存习惯图标替换和水杯位置微调的本地Git快照；个人数据与IDE配置不提交。

## 2026-09-10 11:38

修复右侧贴边鼠标静止时反复隐藏恢复。根因是恢复位置使用right-width而非right+1-width，留下1像素空隙，最右鼠标被再隐藏定时器判在窗口外。统一包含末端像素的计算，同步修正bottom边界，以及QPoint(0,0)不应当作空恢复位置。
- 回归先复现连续5次错误隐藏；修复后14项测试通过，覆盖右/左/上边缘静止与离开、负坐标屏幕。修正一处原测试对相同时间便签排序的不稳定假设。
- 小范围修复本体自检，git diff --check通过；build_simple.py已生成最新dist/quick-notes/DesktopTaskWidget.exe。未创建Git提交。

## 2026-09-10 11:49

用户反馈上一轮1像素修正未解决闪动，确认运行dist/quick-notes目录。当前环境使用实际Windows/200%缩放运行旧修复版动画未复现，不能认定用户现场根因已查清。
- 本轮统一唤出与保持展开的2像素屏幕边缘区域，记录隐藏时的屏幕，避免根据鼠标所在屏幕切换触发基准。鼠标仍在原唤出条时保持展开；恢复中及隐藏时不执行再隐藏。
- 14项测试通过，新增窗口向内偏移后悬停不再隐藏、跨屏边界不触发；真实Windows动画保持边缘2秒（10轮定时检查，实际向内移动2像素）保持展开，鼠标离开后隐藏。鼠标坐标由测试注入，真实用户现场结果仍需实际使用验证。

- 补充高DPI坐标舍入容差：触发屏幕边界允许1个逻辑像素偏差，覆盖right+1位置，避免末端鼠标无法触发或再次隐藏；追加回归通过。
- 最终build_simple.py打包成功，更新dist/quick-notes/DesktopTaskWidget.exe；未创建Git提交。

## 2026-09-12 14:16

整理Python文件及整个项目目录，按用户补充统一英文名称。
- 23个自有py：src现用18个，tools/build打包1个，tools/tests自动测试1个及manual专项检查2个，archive/retired-scripts废弃版本生成脚本1个。15个文件内容与整理前哈希一致，8个文件适配路径或归档说明。quick_notes/legacy.py仍参与旧数据迁移，保留现用。
- 图标与qrc集中src/resources；spec、版本元数据及DPI清单集中tools/build；新缓存tools/build/cache；原build、根字节码缓存和旧文本导出归入archive。完整使用说明移docs/user-guide.md，根README改为入口导航，完整目录清单见docs/directory-guide.md。
- 数据路径继续按源码项目根／exe同目录定位，默认备份与导出、自启动配置、资源加载、打包输入及测试导入已同步。dist/quick-notes发布程序和数据、两个虚拟环境保留原位置。
- 用户确认手动清理了根目录6个JSON数据文件，按要求保持删除状态；原有IDE修改保留。
- 整理前、首轮及最终布局均通过现有14项测试；最终23文件语法、跨工作目录导入、数据／图标／冻结路径、临时目录生成资源及文档链接检查通过。PyInstaller实际构建和TOC核对确认18个现用模块及移动后资源完整入包，工具和归档脚本未入包。
- 最终验证exe：tools/build/cache/layout-verification/dist/DesktopTaskWidget.exe。沙箱内创建新缓存曾遇WinError 5，同一构建命令获自动批准在沙箱外完成。未启动验证exe或重复Windows专项交互测试，原发布exe未覆盖。
- 代码审查发现build/忽略模式会漏收tools/build源码，已改为精确缓存路径；第二轮复核通过。git diff --check通过。未创建Git提交。

## 2026-09-12 17:10

完成task_window.py拆分前分析，方案见docs/task-window-split-plan.md，待用户确认实施。
- 当前2724行、6类，主窗口81个方法；基线3e3e66c，14项现有测试通过，运行代码未修改。
- 拟保留task_window兼容入口，按职责拆入window_parts，多数文件约80至370行；逐方法核对迁移，保持初始化和定时器顺序。
- 已识别父窗口类型判断的循环导入风险、测试patch目标迁移，以及SettingsDialog重复同名方法需保留现有覆盖顺序。

## 2026-09-12 22:32

完成主窗口模块拆分与正式打包。
- src/task_window.py由2724行缩至35行，保留六类兼容导出及直接运行入口；实现分入src/window_parts的12个功能模块，另含包标记，最长369行。功能与关键方法索引见src/window_parts/README.md。
- 对照3e3e66c逐项核对133个方法AST、类信号和入口；仅任务行父窗口查找增加局部导入以避免循环依赖，其余方法逻辑保持。185个公共依赖绑定核对通过。
- 打包脚本加入13个包文件检查；隔离构建及正式构建成功，31个运行源码全部入包，工具及归档未入包。正式程序已更新：dist/quick-notes/DesktopTaskWidget.exe；旧exe备份：tools/build/cache/window-split/DesktopTaskWidget.before-split.exe。发布目录8个数据文件修改时间仍早于本次构建，未启动正式exe。
- 19项自动测试通过；Windows真实窗口、动画与定时器验证左／右／上三边隐藏恢复、持续悬停和移出隐藏，每边11次悬停检测通过。鼠标采用注入逻辑坐标，不等同于用户现场鼠标验证。
- 审查发现测试跨午夜可能写真实饮水日志，已将两处fixture的数据目录及六个路径常量重定向临时目录，并增加真实跨日写入测试；第二轮复审通过。38个py语法检查通过。
- README、AGENTS及目录说明同步，后续AI按索引读取相关模块。未创建Git提交，保留原IDE修改。

## 2026-09-23 11:13
- 查看待办布局、页面切换与配置保存逻辑，形成文件夹快速访问方案。
- 方案：docs/folder-shortcuts-plan.md。等待用户确认，尚未修改源码。

## 2026-09-23 11:32
- 实现待办页底部文件夹网格，支持折叠恢复、目录增改删、双击打开、拖动排序及配置持久化。按用户反馈取消固定显示开关。
- 新增src/window_parts/folder_shortcuts.py和tools/tests/test_folder_shortcuts.py；更新布局、页面切换、配置、打包清单和使用说明。
- 25项自动测试通过；Windows Qt窗口预览检查长名称、缩放和折叠，修正高缩放下文字越界。拖动验证使用注入鼠标事件、模拟落点，未做人工原生鼠标拖放验收。
- 预览：docs/folder-shortcuts-preview.png。独立代码审查未发现阻断问题；单页组件未另派体验审查。
- 发布位置为dist/quick-notes/DesktopTaskWidget.exe。当前桌面运行的是另一目录的旧程序，未替换该外部副本。

## 2026-09-23 11:36
- 修复新增及修改文件夹弹出黑底Qt选择框的问题：移除DontUseNativeDialog，恢复Windows原生目录选择框。
- 在AGENTS.md记录使用系统选择框的约定，补充新增/修改入口的选项回归断言，6项文件夹测试通过。
- 用户退出程序后更新dist/quick-notes/DesktopTaskWidget.exe，并核对发布副本哈希一致。原生对话框未做人工现场验收。

## 2026-09-23 11:52
- 文件夹单元格改为正方形，缩小图标与名称，最小窗口宽度下放3列；Windows实际Qt窗口加DPI设置验证通过，预览为docs/folder-shortcuts-preview.png。
- 移除用户现场不可用的拖放排序，改为空白处及标题栏右键名称/修改日期排序，同项再次点击反向，保存排序字段与顺序；无法访问目录在日期排序中放末尾。
- 7项文件夹测试通过，包含菜单切换、排序重载和不同字号下三列正方形布局。其余19项回归测试通过。
- 本次为小范围修复，由本体自检。更新发布文件dist/quick-notes/DesktopTaskWidget.exe。

## 2026-09-23 12:04
- 复现文件夹闪动：滚动条显隐影响viewport宽度，网格94/98像素反复切换，60毫秒约300次重排。
- 改按控件宽度固定预留滚动条空间，尺寸未变时不重复设置图标和格子大小。保留最小窗口3列。
- 新增临界高度稳定性回归，修复前80毫秒触发315次fit_grid导致失败，修复后通过。全套27项通过，Windows平台8项文件夹测试通过。
- 更新dist/quick-notes/DesktopTaskWidget.exe。小范围修复由本体自检，未另派审查。

## 2026-09-23 14:31
- 文件夹图标与名称按实际行数计算总高度，整体水平、垂直居中；取消选中状态及其背景绘制，保留鼠标悬停反馈。
- 8项文件夹回归通过；Windows Qt注入单击确认无选中项，检查单行和双行名称预览。预览：docs/folder-shortcuts-preview.png。
- 小范围样式调整由本体自检，更新dist/quick-notes/DesktopTaskWidget.exe。

## 2026-09-23 14:53
- 文件夹滚动条固定隐藏并移除右侧占位，格子按控件宽度计算，左右余量平分，让整排居中。滚轮滚动保留。
- Windows平台9项文件夹测试通过，新增隐藏滚动条下滚轮上下滚动与左右余量校验；原闪动、最小宽度3列测试仍通过。
- 更新预览docs/folder-shortcuts-preview.png与发布程序dist/quick-notes/DesktopTaskWidget.exe。小范围修改由本体自检。

## 2026-09-23 15:02
- 修复文件夹菜单全黑：统一create_menu入口，使用快捷便签同款背景、文字、边框、间距和悬停样式，覆盖图标、空白处及标题栏菜单。
- Windows实际Qt菜单预览检查通过，9项文件夹回归通过。预览：docs/folder-menu-preview.png。
- 小范围样式修复由本体自检，更新dist/quick-notes/DesktopTaskWidget.exe。

## 2026-09-24 10:13
- 按用户要求保存当前文件夹快速访问功能及修复的本地Git快照，不推送远程。
