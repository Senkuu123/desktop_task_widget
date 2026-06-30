# CLAUDE.md

本文件包含两部分内容：
1. **工作区规则** — 本沙箱的目录结构、项目规范及操作铁律。
2. **行为准则** — 面向 AI 编码的通用指导原则，减少常见错误。

---

## 第一部分：工作区规则（沙箱专用）

本文件给 Claude Code 在这个沙箱工作区里干活时阅读。

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

根目录不放源代码文件。脚本、笔记本、临时文件一律放进子项目或 `_shared/`。只有 `CLAUDE.md` 和三个约定目录（`_shared/`、`_archive/`、`_template/`）在根目录。

### 工作日志（项目级）

每个子项目根目录下用一个 `WORKLOG.md` 记录工作内容，给后续 Claude Code 会话当长上下文用。

**路径**：`<项目根>/WORKLOG.md`

**写入**
- 文件不存在则建，存在则追加到末尾，绝不覆盖
- 每条用 `## YYYY-MM-DD HH:MM` 二级标题做时间锚（时间用 PowerShell `Get-Date -Format 'yyyy-MM-dd HH:mm'`）
- 内容简短：做了什么、关键产出、踩坑
- 遵循 no_ai_style 规则，给人和后续 Claude 共同回看用

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