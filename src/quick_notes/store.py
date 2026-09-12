import csv
import io
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PyQt5.QtCore import QLockFile


FIELDS = ("id", "created_at", "display_at", "updated_at", "content", "pinned", "archived_at", "deleted_at")
ACTIONS = {"create", "edit", "pin", "unpin", "change_date", "archive", "delete"}


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("便签时间必须包含时区")
    return parsed


class NoteStore:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_path = self.data_dir / "notes_archive.sqlite3"
        self.log_path = self.data_dir / "notes_log.jsonl"
        self.csv_path = self.data_dir / "notes_export.csv"
        self.log_error: str | None = None
        with self._locked():
            self._read_events()

    @contextmanager
    def _locked(self):
        lock = QLockFile(str(self.data_dir / "notes_log.lock"))
        if not lock.tryLock(5000):
            raise OSError("便签文件正在被其他程序使用，请稍后重试")
        try:
            yield
        finally:
            lock.unlock()

    def _atomic_write(self, path: Path, text: str, encoding: str = "utf-8") -> None:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding=encoding, newline="", dir=self.data_dir,
                prefix=path.stem + "-", suffix=".tmp", delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _write_events(self, events: list[dict]) -> None:
        self._atomic_write(self.log_path, "".join(
            json.dumps(event, ensure_ascii=False) + "\n" for event in events
        ))

    def _read_events(self) -> list[dict]:
        rows = []
        if self.log_path.exists():
            for number, line in enumerate(self.log_path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if not line.strip():
                    raise ValueError(f"便签日志第{number}行为空，未覆盖原文件")
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"便签日志第{number}行损坏，未覆盖原文件") from error
                if not isinstance(row, dict):
                    raise ValueError(f"便签日志第{number}行不是对象")
                rows.append(row)
            if not rows:
                from quick_notes.legacy import migrate_events
                if not self.archive_path.exists() or migrate_events(self.archive_path, []):
                    raise ValueError("便签日志为空，无法确认数据完整性，未覆盖原文件")
        if rows and any("schema_version" in row for row in rows):
            self._state(rows)
            return rows
        if rows or self.archive_path.exists():
            from quick_notes.legacy import migrate_events
            events = migrate_events(self.archive_path, rows)
            self._state(events)
            if self.log_path.exists():
                backup = self.data_dir / "notes_log.legacy.jsonl"
                if not backup.exists():
                    self._atomic_write(backup, self.log_path.read_text(encoding="utf-8-sig"))
            # Empty legacy databases have nothing to import; no new database is created.
            if events:
                self._write_events(events)
            return events
        return []

    @staticmethod
    def _state(events: list[dict]) -> dict[str, dict]:
        notes = {}
        event_ids = set()
        for event in events:
            if event.get("schema_version") != 1 or event.get("action") not in ACTIONS:
                raise ValueError("便签日志包含不支持的格式或操作")
            if not all(key in event for key in (*FIELDS, "event_id", "occurred_at")):
                raise ValueError("便签日志缺少必要字段")
            if not isinstance(event["event_id"], str) or not event["event_id"] or event["event_id"] in event_ids:
                raise ValueError("便签日志事件ID无效或重复")
            event_ids.add(event["event_id"])
            if not isinstance(event["id"], str) or not event["id"] or not isinstance(event["content"], str):
                raise ValueError("便签日志ID或正文无效")
            if type(event["pinned"]) is not bool:
                raise ValueError("便签置顶状态无效")
            for field in ("created_at", "display_at", "updated_at", "occurred_at"):
                _timestamp(event[field])
            for field in ("archived_at", "deleted_at"):
                if event[field] is not None:
                    _timestamp(event[field])
            previous = notes.get(event["id"])
            if event["action"] == "create":
                if previous is not None:
                    raise ValueError("便签日志包含重复创建")
            elif previous is None or previous["created_at"] != event["created_at"]:
                raise ValueError("便签日志创建记录缺失或创建时间被修改")
            if event["action"] == "edit" and ("before_content" not in event or event["before_content"] != previous["content"]):
                raise ValueError("便签修改历史不连续")
            notes[event["id"]] = {field: event[field] for field in FIELDS}
        return notes

    def _export_csv(self, notes: dict[str, dict]) -> None:
        try:
            output = io.StringIO(newline="")
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(note for note in notes.values() if not note["archived_at"])
            self._atomic_write(self.csv_path, output.getvalue(), "utf-8-sig")
            self.log_error = None
        except (OSError, UnicodeError, csv.Error) as error:
            self.log_error = f"便签已保存，CSV导出失败：{error}"

    def load_notes(self) -> list[dict]:
        with self._locked():
            notes = self._state(self._read_events())
            self._export_csv(notes)
            visible = [note for note in notes.values() if not note["archived_at"] and not note["deleted_at"]]
            return sorted(visible, key=lambda note: (note["pinned"], _timestamp(note["display_at"]), note["id"]), reverse=True)

    def _save(self, action: str, note_id: str | None = None, **changes) -> dict:
        with self._locked():
            events = self._read_events()
            notes = self._state(events)
            now = datetime.now().astimezone().isoformat()
            if action == "create":
                note = dict(id=uuid4().hex, created_at=now, display_at=now, updated_at=now,
                            content=changes["content"], pinned=False, archived_at=None, deleted_at=None)
            else:
                if note_id not in notes:
                    raise ValueError("便签不存在")
                note = notes[note_id].copy()
                if note["archived_at"] or note["deleted_at"]:
                    raise ValueError("便签已归档或删除")
            before_content = note["content"]
            note.update(changes)
            note["updated_at"] = now
            if action == "archive":
                note["archived_at"] = now
            elif action == "delete":
                note["deleted_at"] = now
            event = dict(note, schema_version=1, event_id=uuid4().hex, action=action, occurred_at=now)
            if action == "edit":
                event["before_content"] = before_content
            events.append(event)
            notes = self._state(events)
            self._write_events(events)
            self._export_csv(notes)
            return note.copy()

    def create_note(self, content: str) -> dict:
        content = content.strip()
        if not content:
            raise ValueError("便签内容不能为空")
        return self._save("create", content=content)

    def update_note(self, note_id: str, content: str) -> dict:
        content = content.strip()
        if not content:
            raise ValueError("便签内容不能为空")
        return self._save("edit", note_id, content=content)

    def set_pinned(self, note_id: str, pinned: bool) -> dict:
        if type(pinned) is not bool:
            raise ValueError("置顶状态必须为布尔值")
        return self._save("pin" if pinned else "unpin", note_id, pinned=pinned)

    def change_date(self, note_id: str, display_at: str) -> dict:
        _timestamp(display_at)
        return self._save("change_date", note_id, display_at=display_at)

    def archive_note(self, note_id: str) -> dict:
        return self._save("archive", note_id)

    def delete_note(self, note_id: str) -> dict:
        return self._save("delete", note_id)

    def history(self, note_id: str) -> list[dict]:
        with self._locked():
            return [event.copy() for event in self._read_events()
                    if event["id"] == note_id and event["action"] in {"create", "edit"}]
