"""便签持久化与键盘流程回归测试，所有数据写入临时目录。"""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import Qt, QEvent, QPoint, QPointF, QCoreApplication
from PyQt5.QtGui import QInputMethodEvent, QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from quick_notes.store import NoteStore
from quick_notes.dialog import QuickNoteDialog


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_archive_and_log_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            first = store.create_note('中文便签\n第二行 <tag>')
            second = store.create_note('另一条')
            notes = NoteStore(directory).load_notes()
            self.assertEqual([n['id'] for n in notes], [second['id'], first['id']])
            self.assertEqual(notes[1]['content'], '中文便签\n第二行 <tag>')
            records = [json.loads(line) for line in (Path(directory) / 'notes_log.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual({r['id'] for r in records}, {first['id'], second['id']})
            self.assertTrue(all(r['created_at'] for r in records))

    def tearDown(self):
        # 主动销毁测试创建的Qt窗口，避免带应用事件过滤器的窗口留到解释器退出。
        for widget in self.app.topLevelWidgets():
            widget.hide()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_blank_rejected_and_write_failure_preserves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            with self.assertRaises(ValueError):
                store.create_note(' \n ')
            store.create_note('原记录')
            before = store.log_path.read_bytes()
            with patch('os.replace', side_effect=PermissionError('blocked')):
                with self.assertRaises(OSError):
                    store.create_note('不能提交')
            self.assertEqual(store.log_path.read_bytes(), before)
            self.assertEqual(len(NoteStore(directory).load_notes()), 1)

    def test_csv_failure_does_not_undo_commit_and_corruption_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            original = store._atomic_write
            def fail_csv(path, text, encoding='utf-8'):
                if path == store.csv_path:
                    raise PermissionError('CSV is open')
                return original(path, text, encoding)
            with patch.object(store, '_atomic_write', side_effect=fail_csv):
                note = store.create_note('已提交正文')
                self.assertTrue(store.log_error)
            self.assertEqual(store.load_notes()[0]['id'], note['id'])
            self.assertIsNone(store.log_error)
            store.log_path.write_text('{broken', encoding='utf-8')
            with self.assertRaises(ValueError):
                store.create_note('不能覆盖损坏文件')
            self.assertEqual(store.log_path.read_text(encoding='utf-8'), '{broken')

    def test_empty_legacy_database_and_log_migrate(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'notes_archive.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE notes(id TEXT, created_at TEXT, content TEXT)')
                connection.commit()
            (Path(directory) / 'notes_log.jsonl').write_text('', encoding='utf-8')
            store = NoteStore(directory)
            self.assertEqual(store.load_notes(), [])
            store.create_note('首次便签')
            self.assertEqual(len(store.load_notes()), 1)
            self.assertTrue((Path(directory) / 'notes_log.legacy.jsonl').exists())

    def test_enter_shift_enter_and_ime(self):
        saved = []
        dialog = QuickNoteDialog(saved.append)
        dialog.show()
        editor = dialog.editor
        editor.setPlainText('第一行')
        editor.moveCursor(editor.textCursor().End)
        QTest.keyClick(editor, Qt.Key_Return, Qt.ShiftModifier)
        self.assertEqual(editor.toPlainText(), '第一行\n')
        self.assertEqual(saved, [])
        QApplication.sendEvent(editor, QInputMethodEvent('拼音', []))
        QTest.keyClick(editor, Qt.Key_Return)
        self.assertEqual(saved, [])
        QApplication.sendEvent(editor, QInputMethodEvent('', []))
        editor.setPlainText('完整内容')
        QTest.keyClick(editor, Qt.Key_Return)
        self.assertEqual(saved, ['完整内容'])
        self.assertFalse(dialog.isVisible())

    def test_failed_save_and_cancel_preserve_draft(self):
        def fail(content):
            raise PermissionError('blocked')
        dialog = QuickNoteDialog(fail)
        dialog.show()
        QTest.keyClick(dialog.editor, Qt.Key_Return)
        self.assertTrue(dialog.isVisible())
        dialog.editor.setPlainText('未保存内容')
        QTest.keyClick(dialog.editor, Qt.Key_Return)
        self.assertEqual(dialog.editor.toPlainText(), '未保存内容')
        self.assertTrue(dialog.isVisible())
        self.assertTrue(dialog.status.text())
        dialog.reject()
        dialog.show()
        self.assertEqual(dialog.editor.toPlainText(), '未保存内容')
        dialog.close()

    def test_window_navigation_and_saved_note(self):
        import task_window
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(task_window, 'get_data_dir', return_value=directory), \
                patch.object(task_window, 'NoteHotkey') as hotkey, \
                patch.object(task_window.TransparentTaskWindow, 'load_window_settings'), \
                patch.object(task_window.TransparentTaskWindow, 'save_window_settings'), \
                patch.object(task_window.TransparentTaskWindow, 'delayed_task_load'), \
                patch.object(task_window.TransparentTaskWindow, 'check_autostart_launch'), \
                patch.object(task_window.TransparentTaskWindow, 'setup_windows_specific'), \
                patch.object(task_window, 'load_water_reminder', return_value=task_window.WaterReminder()):
            hotkey.return_value.registered = True
            window = task_window.TransparentTaskWindow()
            self.assertFalse(hasattr(window, 'page_title'))
            self.assertEqual(window.content_page_btn.text(), '📋')
            window.content_page_btn.click()
            self.assertEqual(window.current_page, 'notes')
            self.assertEqual(window.content_page_btn.text(), '📝')
            window.water_page_btn.click()
            window.water_page_btn.click()
            self.assertEqual(window.current_page, 'habits')
            self.assertFalse(window.water_page_btn.icon().isNull())
            window.content_page_btn.click()
            self.assertEqual(window.current_page, 'notes')
            window.content_page_btn.click()
            self.assertEqual(window.current_page, 'tasks')
            window.content_page_btn.click()
            self.assertEqual(window.current_page, 'notes')
            bar = window.drag_area.layout()
            self.assertEqual(bar.indexOf(window.content_page_btn), bar.indexOf(window.add_button) + 1)
            self.assertEqual(bar.indexOf(window.water_page_btn), bar.indexOf(window.content_page_btn) + 1)
            self.assertIn('暂无便签', window.notes_status.text())
            original_create = window.note_store.create_note
            original_load = window.note_store.load_notes
            def commit_then_block_reload(content):
                note = original_create(content)
                window.note_store.load_notes = lambda: (_ for _ in ()).throw(OSError('reload blocked'))
                return note
            with patch.object(window.note_store, 'create_note', side_effect=commit_then_block_reload):
                window.save_quick_note('界面保存测试')
            window.note_store.load_notes = original_load
            self.app.processEvents()
            self.assertEqual(window.current_page, 'notes')
            self.assertEqual(window.task_list_widget.count(), 1)
            card = window.task_list_widget.itemWidget(window.task_list_widget.item(0))
            self.assertIn('界面保存测试', card.content_label.text())
            self.assertEqual(window.notes_status.text(), '')
            note_id = card.note['id']
            window.on_item_double_clicked(card.item)
            self.assertTrue(card.is_editing)
            card.editor.setPlainText('编辑中的草稿')
            window.refresh_task_display()
            self.assertIs(window.note_cards[note_id], card)
            self.assertEqual(card.editor.toPlainText(), '编辑中的草稿')
            window.water_page_btn.click()
            window.content_page_btn.click()
            card = window.note_cards[note_id]
            self.assertTrue(card.is_editing)
            self.assertEqual(card.editor.toPlainText(), '编辑中的草稿')
            card.cancel_button.click()
            self.assertEqual(card.content_label.text(), '界面保存测试')
            card.begin_edit()
            card.editor.setPlainText('修改后的正文')
            with patch.object(window.note_store, 'update_note', side_effect=OSError('blocked')):
                card.save()
            self.assertTrue(card.is_editing)
            self.assertEqual(card.editor.toPlainText(), '修改后的正文')
            self.assertTrue(card.error.text())
            card.save()
            self.assertFalse(card.is_editing)
            self.assertEqual(card.content_label.text(), '修改后的正文')
            self.assertEqual(NoteStore(directory).load_notes()[0]['content'], '修改后的正文')
            self.assertNotIn('双击查看', window.notes_status.text())
            window.water_page_btn.click()
            self.assertEqual(window.current_page, 'habits')
            window.content_page_btn.click()
            window.content_page_btn.click()
            self.assertEqual(window.current_page, 'tasks')
            window.save_quick_note(('很长的便签正文\n' * 100).strip())
            window.resize(320, 420)
            window.show()
            self.app.processEvents()
            long_card = window.note_cards[window.notes[0]['id']]
            scrollbar = window.task_list_widget.verticalScrollBar()
            self.assertGreater(scrollbar.maximum(), 400)
            scrollbar.setValue(400)
            self.assertEqual(scrollbar.value(), 400)
            long_card.begin_edit()
            self.app.processEvents()
            self.assertTrue(window.task_list_widget.visualItemRect(long_card.item).intersects(window.task_list_widget.viewport().rect()))
            long_card.cancel()
            menu = window.note_actions.menu(long_card)
            self.assertEqual([action.text() for action in menu.actions() if not action.isSeparator()],
                             ['编辑', '置顶', '弹出浮窗', '归档', '更多', '删除'])
            self.assertEqual([a.text() for a in menu.actions()[4].menu().actions()], ['显示历史版本', '修改日期'])
            menu.deleteLater()
            note_id = long_card.note['id']
            original_count = len(window.notes)
            window.note_actions.open_popup(note_id)
            popup = window.note_actions.popups[note_id]
            popup.editor.setPlainText('浮窗修改正文')
            popup.submit()
            self.app.processEvents()
            self.assertEqual(len(window.notes), original_count)
            self.assertEqual(next(n for n in window.notes if n['id'] == note_id)['content'], '浮窗修改正文')
            self.assertNotIn(note_id, window.note_drafts)
            window.note_actions.mutate(note_id, 'pin', True)
            self.assertEqual(window.notes[0]['id'], note_id)
            window.note_actions.mutate(note_id, 'date', '2020-01-02T03:04:05+08:00')
            self.assertIn('2020-01-02 03:04', window.note_cards[note_id].time_label.text())
            window.note_actions.mutate(note_id, 'archive')
            self.assertNotIn(note_id, window.note_cards)
            window.show_page('water')
            window.resize(300, 280)
            self.app.processEvents()
            self.assertEqual(window.minimumHeight(), 280)
            self.assertFalse(window.task_list_widget.isVisible())
            water = window.water_widget
            water.water.today_logs = [{'time': '10:20', 'type': '喝一杯', 'amount': 250}]
            water._rebuild_log()
            for expanded in (True, False):
                water.log_container.setVisible(expanded)
                water.fit_available_height()
                self.app.processEvents()
                for widget in (water.title_label, water.progress_bar, water.reminder_time_label, water._btn_row_widget):
                    self.assertTrue(widget.isVisible())
                    bottom = widget.mapTo(water, widget.rect().bottomRight())
                    self.assertLess(bottom.y(), water.height())
            window.water_page_btn.click()
            self.assertEqual(window.current_page, 'habits')
            self.assertFalse(water.isVisible())
            self.assertTrue(window.task_list_widget.isVisible())
            self.assertEqual(window.water_page_btn.accessibleName(), '习惯列表')
            window.water_page_btn.click()
            self.assertEqual(window.current_page, 'water')
            window.close()
            hotkey.return_value.close.assert_called_once()

    def test_edit_preserves_creation_and_logs_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            first = store.create_note('原始内容')
            second = store.create_note('后创建的便签')
            updated = store.update_note(first['id'], '修改后\n多行')
            self.assertEqual(updated['created_at'], first['created_at'])
            self.assertEqual([n['id'] for n in store.load_notes()], [second['id'], first['id']])
            records = [json.loads(line) for line in store.log_path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(records[0]['content'], '原始内容')
            self.assertEqual(records[-1]['before_content'], '原始内容')
            self.assertEqual(records[-1]['content'], '修改后\n多行')
            self.assertEqual(records[-1]['action'], 'edit')
            with self.assertRaises(ValueError):
                store.update_note(first['id'], '  ')
            with self.assertRaises(ValueError):
                store.update_note('missing', '正文')
            with patch('os.replace', side_effect=PermissionError('blocked')):
                with self.assertRaises(OSError):
                    store.update_note(first['id'], '不能提交')
            self.assertEqual(store.load_notes()[1]['content'], '修改后\n多行')

    def test_pin_date_archive_delete_and_history(self):
        import csv
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            first = store.create_note('原内容')
            second = store.create_note('第二条')
            store.set_pinned(first['id'], True)
            self.assertEqual(store.load_notes()[0]['id'], first['id'])
            store.change_date(first['id'], '2020-01-02T03:04:05+08:00')
            self.assertEqual(store.load_notes()[0]['created_at'], first['created_at'])
            store.set_pinned(first['id'], False)
            self.assertEqual(store.load_notes()[0]['id'], second['id'])
            store.update_note(first['id'], '修改内容')
            self.assertEqual([v['content'] for v in store.history(first['id'])], ['原内容', '修改内容'])
            store.archive_note(first['id'])
            store.delete_note(second['id'])
            self.assertEqual(NoteStore(directory).load_notes(), [])
            events = [json.loads(line) for line in store.log_path.read_text(encoding='utf-8').splitlines()]
            archived = next(e for e in events if e['action'] == 'archive')
            self.assertTrue(archived['archived_at'])
            self.assertEqual(archived['content'], '修改内容')
            with (Path(directory) / 'notes_export.csv').open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertNotIn(first['id'], [r['id'] for r in rows])
            self.assertTrue(rows[0]['deleted_at'])
            self.assertFalse((Path(directory) / 'notes_archive.sqlite3').exists())

    def test_legacy_migration_read_only_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'notes_archive.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript("""
                    CREATE TABLE notes(id TEXT, created_at TEXT, content TEXT);
                    CREATE TABLE creation_log(id TEXT, created_at TEXT, content TEXT);
                    CREATE TABLE edit_log(id TEXT, edited_at TEXT, before_content TEXT, content TEXT);
                    INSERT INTO notes VALUES ('one','2026-09-09T10:00:00+08:00','新正文');
                    INSERT INTO creation_log VALUES ('one','2026-09-09T10:00:00+08:00','旧正文');
                    INSERT INTO edit_log VALUES ('one','2026-09-09T11:00:00+08:00','旧正文','新正文');
                """)
                connection.commit()
            original = database.read_bytes()
            store = NoteStore(directory)
            self.assertEqual(store.load_notes()[0]['content'], '新正文')
            self.assertEqual([v['content'] for v in store.history('one')], ['旧正文', '新正文'])
            store.archive_note('one')
            self.assertEqual(NoteStore(directory).load_notes(), [])
            self.assertEqual(database.read_bytes(), original)

    def test_outside_deactivation_preserves_draft_and_pin(self):
        dialog = QuickNoteDialog(lambda content: None)
        dialog.show()
        dialog.editor.setPlainText('点击外部仍保留的草稿')
        with patch.object(dialog, 'isActiveWindow', return_value=False):
            QApplication.sendEvent(dialog, QEvent(QEvent.WindowDeactivate))
            self.app.processEvents()
            self.assertFalse(dialog.isVisible())
            dialog.show()
            self.assertEqual(dialog.editor.toPlainText(), '点击外部仍保留的草稿')
            dialog.pin_button.setChecked(True)
            QApplication.sendEvent(dialog, QEvent(QEvent.WindowDeactivate))
            self.app.processEvents()
            self.assertTrue(dialog.isVisible())
            dialog.pin_button.setChecked(False)
            QApplication.sendEvent(dialog, QEvent(QEvent.WindowDeactivate))
            self.app.processEvents()
            self.assertFalse(dialog.isVisible())
        dialog.close()

    def test_toolbar_and_send_button(self):
        saved = []
        dialog = QuickNoteDialog(saved.append)
        dialog.show()
        self.assertFalse(dialog.save_button.isEnabled())
        dialog.tag_button.click()
        self.assertEqual(dialog.editor.toPlainText(), '#')
        self.assertTrue(dialog.save_button.isEnabled())
        dialog.editor.insertPlainText('想法')
        dialog.bullet_button.click()
        dialog.editor.insertPlainText('一件事')
        self.assertEqual(dialog.editor.toPlainText(), '#想法\n- 一件事')
        dialog.save_button.click()
        self.assertEqual(saved, ['#想法\n- 一件事'])
        self.assertFalse(dialog.isVisible())
        self.assertFalse(dialog.save_button.isEnabled())

    def test_pinned_toolbar_hover_and_click(self):
        saved = []
        dialog = QuickNoteDialog(saved.append)
        dialog.show()
        dialog.pin_button.setChecked(True)
        for button, effect in dialog.bottom_effects.items():
            QApplication.sendEvent(button, QEvent(QEvent.Leave))
            self.assertLess(effect.opacity(), 0.3)
            QApplication.sendEvent(button, QEvent(QEvent.Enter))
            self.assertEqual(effect.opacity(), 1.0)
        dialog.tag_button.click()
        self.assertEqual(dialog.editor.toPlainText(), '#')
        dialog.save_button.click()
        self.assertEqual(saved, ['#'])
        self.assertFalse(dialog.isVisible())

    def test_resize_corner_and_minimum_size(self):
        dialog = QuickNoteDialog(lambda content: None)
        dialog.show()
        dialog.move(100, 100)
        initial = dialog.geometry()
        corner = QPoint(dialog.width() - 3, dialog.height() - 3)
        origin = dialog.mapToGlobal(corner)
        QTest.mousePress(dialog, Qt.LeftButton, pos=corner)
        moved = origin + QPoint(120, 80)
        QApplication.sendEvent(dialog, QMouseEvent(QEvent.MouseMove,
            QPointF(dialog.mapFromGlobal(moved)), QPointF(moved),
            Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QTest.mouseRelease(dialog, Qt.LeftButton)
        self.assertEqual(dialog.size(), initial.size() + type(dialog.size())(120, 80))
        right, bottom = dialog.geometry().right(), dialog.geometry().bottom()
        origin = dialog.mapToGlobal(QPoint(3, 3))
        QTest.mousePress(dialog, Qt.LeftButton, pos=QPoint(3, 3))
        moved = origin + QPoint(1000, 1000)
        QApplication.sendEvent(dialog, QMouseEvent(QEvent.MouseMove,
            QPointF(dialog.mapFromGlobal(moved)), QPointF(moved),
            Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QTest.mouseRelease(dialog, Qt.LeftButton)
        self.assertEqual(dialog.size(), dialog.minimumSize())
        self.assertEqual(dialog.geometry().right(), right)
        self.assertEqual(dialog.geometry().bottom(), bottom)
        dialog.close()


if __name__ == '__main__':
    unittest.main()
