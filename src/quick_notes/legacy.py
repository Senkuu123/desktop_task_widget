import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


def migrate_events(archive_path: Path, legacy_rows: list[dict]) -> list[dict]:
    for row in legacy_rows:
        required = ("id", "content", "edited_at", "before_content") if row.get("action") == "edit" else ("id", "content", "created_at")
        if row.get("action") not in (None, "create", "edit") or not all(key in row for key in required):
            raise ValueError("旧便签日志格式不完整，未执行迁移")
    rows = []
    current = []
    if archive_path.exists():
        with closing(sqlite3.connect(archive_path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "notes" not in tables:
                raise ValueError("旧便签数据库缺少notes表，未执行迁移")
            current = [dict(row) for row in connection.execute("SELECT id, created_at, content FROM notes ORDER BY rowid")]
            if "creation_log" in tables:
                rows.extend(dict(row) for row in connection.execute("SELECT id, created_at, content FROM creation_log ORDER BY rowid"))
            if "edit_log" in tables:
                rows.extend(dict(row) for row in connection.execute("SELECT 'edit' AS action, id, edited_at, before_content, content FROM edit_log ORDER BY rowid"))
    seen = {(row.get("action", "create"), row["id"], row.get("created_at", row.get("edited_at")), row["content"]) for row in rows}
    for row in legacy_rows:
        key = (row.get("action", "create"), row["id"], row.get("created_at", row.get("edited_at")), row["content"])
        if key not in seen:
            rows.append(row)
            seen.add(key)
    creates = {}
    for row in rows:
        if row.get("action") != "edit":
            existing = creates.get(row["id"])
            if existing and (existing["created_at"] != row["created_at"] or existing["content"] != row["content"]):
                raise ValueError("旧便签创建记录冲突，未执行迁移")
            creates[row["id"]] = row
    for note in current:
        if note["id"] not in creates:
            first_edit = next((row for row in rows if row["id"] == note["id"] and row.get("action") == "edit"), None)
            creates[note["id"]] = dict(note, content=first_edit["before_content"] if first_edit else note["content"])
    events = []
    states = {}
    for row in creates.values():
        note = dict(id=row["id"], created_at=row["created_at"], display_at=row["created_at"],
                    updated_at=row["created_at"], content=row["content"], pinned=False,
                    archived_at=None, deleted_at=None)
        states[note["id"]] = note
        events.append(dict(note, schema_version=1, event_id=uuid4().hex, action="create", occurred_at=note["created_at"]))
    for row in rows:
        if row.get("action") != "edit":
            continue
        if row["id"] not in states:
            raise ValueError("旧便签修改历史缺少创建记录，未执行迁移")
        note = states[row["id"]]
        if note["content"] != row["before_content"]:
            raise ValueError("旧便签修改历史不连续，未执行迁移")
        note.update(content=row["content"], updated_at=row["edited_at"])
        events.append(dict(note, schema_version=1, event_id=uuid4().hex, action="edit",
                           occurred_at=row["edited_at"], before_content=row["before_content"]))
    for original in current:
        if states[original["id"]]["content"] != original["content"]:
            raise ValueError("旧便签正文与修改历史不一致，未执行迁移")
    return events
