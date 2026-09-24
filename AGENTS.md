# AGENTS.md

本文件包含两部分内容：
1. **工作区规则** — 本沙箱的目录结构、项目规范及操作铁律。
2. **行为准则** — 面向 AI 编码的通用指导原则，减少常见错误。

---

## 第一部分：工作区规则（沙箱专用）

本文件给 Codex 在这个沙箱工作区里干活时阅读。

### 工作区定位

这个目录是个人沙箱，用来存放github拉取的项目、随手开发小项目、做试验、写一次性脚本。每个小东西放在独立子目录里，不在根目录散放文件。

### 军事化管理（铁律）

给用户的所有文件，必须要告诉他路径在哪，不要让用户再来反复问你

### 子项目规范

#### 命名

`YYYYMMDD-语义名`，小写英文，单词用连字符分隔。例：`20260506-csv-parser`。

#### 创建

1. 在根目录创建 `YYYYMMDD-语义名/`
2. 从 `_template/README.md` 复制一份到项目目录
3. 把 README 填好（做什么、怎么跑、依赖、备注），再开始写代码

README 是给下一个 AI（或自己）看的，要写到让它读完后就知道这个项目干什么、怎么跑起来。

#### 完成或废弃

把整个项目目录移到 `_archive/` 下面，不要删掉。移之前确认 README 还算准确。

只写了一半、没有 README 的项目，补上 README 再移。

### 共享目录

- `_shared/` — 放不归属任何具体项目的临时代码、试验片段、工具脚本。放进去的文件也要有个简短的注释头说明用途。不要在这个目录下建无说明的 `test.py`、`a.js` 之类文件。
- `_archive/` — 已完成或废弃的项目。保持项目目录结构不变，只移动位置。
- `_template/` — 新项目的 README 模板。不要往这个目录放别的东西。

### 根目录约束

根目录不放源代码文件。脚本、笔记本、临时文件一律放进子项目或 `_shared/`。只有 `AGENTS.md` 和三个约定目录（`_shared/`、`_archive/`、`_template/`）在根目录。

### 工作日志（项目级）

每个子项目根目录下用一个 `WORKLOG.md` 记录工作内容，给后续 Codex 会话当长上下文用。

**路径**：`<项目根>/WORKLOG.md`

**写入**
- 文件不存在则建，存在则追加到末尾，绝不覆盖
- 每条用 `## YYYY-MM-DD HH:MM` 二级标题做时间锚（时间用 PowerShell `Get-Date -Format 'yyyy-MM-dd HH:mm'`）
- 内容简短：做了什么、关键产出、踩坑
- 遵循 no_ai_style 规则，给人和后续 Codex 共同回看用

**追加触发**：完成有产出的任务后（写代码、改文件、做分析、解决问题、配置调整）追加，写完一句话告知路径。闲聊、纯查询、用户明说「不用记」不写。

**读取触发**：需要回忆历史决策、确认之前怎么处理、了解项目上下文时主动 Read `<项目根>/WORKLOG.md`。按需读，因为很长，不需要每次都读。

---

## 第二部分：行为准则（通用编码规范）

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
### 贴边隐藏回归约定

- 隐藏恢复问题不能仅验证目标矩形。需使用实际Windows窗口动画和定时器验证持续悬停、移出隐藏；唤出区域与保持展开区域应一致。曾发生1像素修正测试通过但用户仍复现，报告必须区分模拟坐标测试与用户现场。

### 本项目目录约定

- 用户偏好英文目录名。整理目录时同时考虑源码、资源、工具、文档及历史产物，避免只移动py后留下零散文件。
- `src/`为现用源码，图标资源位于`src/resources/`；`tools/build/`为打包脚本、spec与Windows元数据；`tools/tests/`为自动测试及`manual/`专项验证；`docs/`为文档；`archive/`为历史文件。
- 日常入口和完整目录说明以根目录README及`docs/directory-guide.md`为准。发布目录固定`dist/quick-notes/`，源码数据仍位于项目根目录，现有虚拟环境不搬迁。
- Git只忽略具体缓存目录，不能用`build/`这种匹配所有层级的规则，否则会漏收`tools/build/`中的打包源码。

### 主窗口代码定位

- `src/task_window.py`仅为兼容入口。涉及主窗口时先读`src/window_parts/README.md`，按功能与关键方法定位，再读取相关模块；不要默认整包通读。
- 初始化与配置在`window.py`，布局在`layout.py`，拖动缩放在`interaction.py`，贴边动画在`edge_hide.py`，任务／习惯／便签分别在`tasks.py`、`habits.py`、`notes.py`；各控件和设置窗口有独立模块。
- 原方法名、信号和定时器时序保持兼容。Mixin无构造函数，初始化集中在主窗口；任务行只在父窗口查找时局部导入主窗口类，避免循环导入。
- 测试patch须指向函数实际所属模块，数据使用临时目录。Windows贴边动画专项入口为`tools/tests/manual/verify_window_edges.py`。

### 文件夹选择对话框

- 新增和修改文件夹路径使用Windows系统原生选择框，不设置`QFileDialog.DontUseNativeDialog`。曾因强制Qt对话框继承透明窗口样式，出现黑底与文字不可读；不要为输入路径而禁用系统选择框。

### 文件夹布局与排序回归
- 文件夹单元格保持正方形，窗口最小宽度300下须实测同一行3个，包含滚动条出现与不同字号。
- 用户现场确认拖动排序不可用，现采用名称/修改日期右键排序；模拟拖放调用通过不能据此宣称实际拖动可用。

- 文件夹滚动条固定隐藏且不占位，保留滚轮滚动；网格按控件宽度计算并平分左右余量。不能重新引入滚动条显隐与viewport宽度相互影响的尺寸反馈振荡。需测试临界高度下事件循环稳定，而不只检查单帧截图。

- 文件夹图标与实际一至两行名称作为整体在正方形单元格中居中；单击不保留选中背景高亮。

- 文件夹右键菜单使用快捷便签同款显式QMenu样式（深灰背景、浅灰文字及悬停色），覆盖透明父窗口样式；覆盖图标、空白处及标题栏入口。

- 文件夹格子固定96×96、图标固定41×41逻辑像素，缩放主窗口只改列数和居中留白。待办高度由可拖动分隔线保存，新增窗口高度给文件夹，折叠和切页不得覆盖保存的分配。
- 贴边pending不能被普通点击永久清除；点击、缩放松手和启动显示后都续接贴边判断，待隐藏使用当前矩形，菜单/模态窗口/鼠标按住期间暂停。
- 可见滚动条共用src/ui_styles.py的4像素样式；文件夹继续隐藏并不占位。
- 统一滚动条样式须保留滑块默认透明、悬停和拖动显示；便签右侧留白保持紧凑。文件夹分隔线默认透明，去掉标题区域顶边框，保留悬停反馈与拖动功能。

- 便签卡片左右至主窗口边缘留白均为10逻辑像素；右侧由4像素间隔、4像素滚动条、2像素外边距组成，无需滚动时也保留同等空间。
