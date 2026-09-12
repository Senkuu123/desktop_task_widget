# task_window.py模块拆分方案

状态：用户已确认，已按方案实施。2026-09-12。最终验证及发布结果见WORKLOG.md。

## 目标与现状

`src/task_window.py`有2724行，包含6个类、主窗口81个方法。目标是让后续AI按功能只读取相关小文件，保持现有软件行为。

当前代码基线为Git提交`3e3e66c`。已有14项自动测试全部通过。工作区只有原有IDE文件修改，本次规划尚未修改运行代码。

## 拆分目录

保留`src/task_window.py`作为兼容入口，导出原有窗口类并保留直接运行时的启动逻辑。实际实现放入`src/window_parts/`。

| 文件 | 职责 | 预计行数 |
|------|------|----------|
| `src/task_window.py` | 兼容导出、原直接运行入口 | 约40 |
| `src/window_parts/__init__.py` | 包标记 | 少量 |
| `src/window_parts/window.py` | TransparentTaskWindow构造、基本窗口属性、平台设置、配置加载保存、置顶 | 约280 |
| `src/window_parts/water_widgets.py` | WaterProgressBar、WaterDisplayWidget整类迁移 | 约365 |
| `src/window_parts/water_settings.py` | _WaterSettingsDialog整类迁移 | 约165 |
| `src/window_parts/task_item.py` | TaskListWidgetItem整类迁移 | 约330 |
| `src/window_parts/settings_dialog.py` | SettingsDialog整类迁移 | 约180 |
| `src/window_parts/layout.py` | 主窗口布局、样式、图标和页面导航 | 约370 |
| `src/window_parts/tasks.py` | 任务增改、刷新、完成和持久化调用 | 约170 |
| `src/window_parts/interaction.py` | 绘制、拖动、缩放、光标和窗口事件 | 约315 |
| `src/window_parts/notes.py` | 主窗口便签加载、展示、编辑入口 | 约115 |
| `src/window_parts/habits.py` | 主窗口习惯列表、状态和日志同步 | 约130 |
| `src/window_parts/notifications.py` | 截止时间检查和通知 | 约80 |
| `src/window_parts/edge_hide.py` | 贴边隐藏、恢复动画、全部相关定时器 | 约260 |

行数是规划值，最终以保留完整职责和方法为准，不为了凑行数拆散单个方法。

## 行为保持规则

1. 优先整类、整方法原样搬迁。保持方法名称、参数、默认值、装饰器、分支、常量、信号连接和定时器时序。
2. 主窗口按职责使用无构造函数的Mixin组合，QWidget仍为最终Qt基类。保留原构造函数语句及顺序，避免把初始化散到各模块。
3. 原有super调用继续沿主窗口MRO到Qt基类；同名事件方法只放一个位置，不引入方法覆盖。
4. TaskListWidgetItem寻找父窗口时仍使用原类做isinstance判断，仅在方法内局部导入window.py中的类以打破循环。兼容入口不定义第二份窗口类，因此直接运行与main导入拥有相同类身份。
5. SettingsDialog原有两个同名update_autostart_status定义按原顺序保留，本次不清理重复代码或修改行为。
6. 只调整必要导入与模块连接，不做UI、数据格式、功能、命名风格或历史bug的顺手改造。发现其他问题单独记录。
7. 主程序的`from task_window import TransparentTaskWindow`保持兼容。源码数据与发布目录约定保持现状。

## 测试与验证

- 以拆分前源码逐方法核对函数体和装饰器，采用忽略行号的AST比较及源码片段核对；除打破循环所需的局部导入外，业务方法体应一致。单独报告所有非搬迁差异。
- 同步现有测试的patch目标：主窗口构造依赖指向window模块，便签数据入口指向notes模块；继续使用临时数据，避免patch失效后接触实际文件。
- 拆分后运行完整14项现有回归，并补充窗口类身份、任务行父窗口查找、Mixin事件分派及关键状态流程的针对性检查。
- 对贴边隐藏使用实际Windows Qt窗口动画和定时器验证持续悬停、移出再隐藏；鼠标坐标注入与用户现场验证需明确区分，不以矩形计算通过代替动画验证。
- 做一次独立代码审查，检查循环导入、MRO、符号依赖和方法搬迁完整性。

## 打包与交付

- 更新`tools/build/build_simple.py`的必需模块清单及必要的spec配置，使用静态导入收集新包。
- 先输出隔离验证exe到`tools/build/cache/`，核对所有新模块入包；验证通过后更新`dist/quick-notes/DesktopTaskWidget.exe`。不移动或覆盖用户数据。
- 若发布exe被运行进程占用，先完成隔离构建和全部检查，再说明文件占用情况，不强制终止用户程序。
- 新增`src/window_parts/README.md`，列出功能到文件及关键方法的索引；更新根README、目录说明和项目规范中的AI定位提示，后续先读索引、再定点搜索。
- 在根目录WORKLOG追加实际拆分结果、验证范围及发布产物。此次不自动创建Git提交。

## 确认范围

用户已确认按上述保守拆分实施。规划时的基线保留在本文，实施结果以`src/window_parts/README.md`和根目录WORKLOG为准。
