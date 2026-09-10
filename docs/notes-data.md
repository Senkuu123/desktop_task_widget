# 便签数据文件与看板口径

不再使用数据库保存新操作。所有文件位于程序数据目录：源码运行时为项目目录，打包后为exe同目录。

## 文件

| 文件 | 用途 |
| --- | --- |
| notes_log.jsonl | 唯一主文件，UTF-8，每行一个JSON事件，含正文和完整状态。请备份此文件。 |
| notes_export.csv | 自动导出的最新状态，UTF-8 BOM，适用于Excel、Power BI及Python。可从主文件重建，请勿当作主文件编辑。 |
| notes_archive.sqlite3 | 旧版数据，只读迁移后保留原文件，新操作不再写入。 |
| notes_log.legacy.jsonl | 旧格式JSONL迁移前备份。 |
| notes_log.lock | 操作期间使用的临时进程锁。 |

每次操作在JSONL中新增一个事件，使用临时文件和原子替换提交完整文件；进程锁避免两个实例覆盖彼此的记录。文件损坏会报错，不作为空列表覆盖。

## 字段

| 字段 | 含义 |
| --- | --- |
| schema_version | 格式版本，当前为1 |
| event_id | 唯一事件ID，用于统计和去重 |
| id | 便签ID，正文修改不会改变 |
| action | create、edit、pin、unpin、change_date、archive、delete |
| occurred_at | 本次操作真实发生时间 |
| created_at | 原始创建时间，修改展示日期不影响它 |
| display_at | 列表展示日期和时间，可修改；列表按此字段排序 |
| updated_at | 最近一次操作时间，包含日期/状态调整，不仅是正文编辑 |
| content | 操作后的完整正文，保留换行 |
| before_content | edit事件的修改前正文 |
| pinned | 列表是否置顶，与浮窗固定无关 |
| archived_at | 归档时间，未归档为null |
| deleted_at | 软删除时间，未删除为null |

所有时间均为含时区的ISO 8601字符串。CSV包含从id到deleted_at的状态字段，不包含event_id、action、occurred_at和before_content；空时间输出为空字段。

归档事件保留归档时的全文与时间，之后不在默认列表或CSV中出现，不提供归档列表和取消归档。删除便签仍有日志，CSV保留deleted_at，默认列表隐藏。

## 看板统计建议

- 每日新增：JSONL筛选action=create，按created_at统计；不要把编辑、改日期事件算成新增。
- 编辑频次：筛选action=edit，按occurred_at统计。
- 归档数量和归档内容：JSONL筛选action=archive，读取archived_at、content。
- 当前有效便签：CSV筛选deleted_at为空；归档已在导出时排除。
- 按用户整理日期分析：用display_at；按真实活动日期分析：用created_at或occurred_at。
- JSONL同一便签会出现多行，统计便签数应按id去重；求最新状态按文件中最后一次事件取值，不按display_at排序取值。

CSV正文含逗号、引号和换行时使用标准CSV转义；请用CSV读取器解析，不按单行文本计数。日志包含完整笔记，分享看板源数据前按需去掉正文列。
