import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class NoteStore:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_path = self.data_dir / "notes_archive.sqlite3"
        self.log_path = self.data_dir / "notes_log.jsonl"
        self.log_error: str | None = None
        with closing(sqlite3.connect(self.archive_path)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS notes ("
                    "id TEXT PRIMARY KEY, created_at TEXT NOT NULL, "
                    "content TEXT NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS creation_log ("
                    "id TEXT PRIMARY KEY, created_at TEXT NOT NULL, "
                    "content TEXT NOT NULL)"
                )

    def load_notes(self) -> list[dict[str, str]]:
        with closing(sqlite3.connect(self.archive_path)) as connection:
            connection.row_factory = sqlite3.Row
            notes = [dict(row) for row in connection.execute(
                "SELECT id, created_at, content FROM notes ORDER BY rowid DESC"
            )]
        self._export_log()
        return notes

    def create_note(self, content: str) -> dict[str, str]:
        content = content.strip()
        if not content:
            raise ValueError("便签内容不能为空")
        note = {
            "id": uuid4().hex,
            "created_at": datetime.now().astimezone().isoformat(),
            "content": content,
        }
        with closing(sqlite3.connect(self.archive_path)) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO notes (id, created_at, content) "
                    "VALUES (:id, :created_at, :content)", note
                )
                connection.execute(
                    "INSERT INTO creation_log (id, created_at, content) "
                    "VALUES (:id, :created_at, :content)", note
                )
        self._export_log()
        return note

    def _export_log(self) -> None:
        temporary_path = None
        try:
            with closing(sqlite3.connect(self.archive_path)) as connection:
                connection.row_factory = sqlite3.Row
                with connection:
                    # Serialize exporters and writers so an older snapshot cannot win.
                    connection.execute("BEGIN IMMEDIATE")
                    rows = connection.execute(
                        "SELECT id, created_at, content "
                        "FROM creation_log ORDER BY rowid"
                    )
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", newline="\n",
                        dir=self.data_dir, prefix="notes_log-", suffix=".tmp",
                        delete=False,
                    ) as stream:
                        temporary_path = Path(stream.name)
                        for row in rows:
                            stream.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary_path, self.log_path)
            self.log_error = None
        except (OSError, sqlite3.Error, UnicodeError) as error:
            self.log_error = f"便签已存档，创建日志导出失败：{error}"
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
