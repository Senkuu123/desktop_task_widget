"""便签持久化与键盘流程回归测试，所有数据写入临时目录。"""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import Qt, QEvent, QPoint, QPointF
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

    def test_blank_rejected_and_log_failure_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NoteStore(directory)
            with self.assertRaises(ValueError):
                store.create_note(' \n ')
            with patch('os.replace', side_effect=PermissionError('blocked')):
                note = store.create_note('日志失败仍保存')
                self.assertTrue(store.log_error)
            recovered = NoteStore(directory)
            self.assertEqual([n['id'] for n in recovered.load_notes()], [note['id']])
            self.assertIsNone(recovered.log_error)
            self.assertTrue((Path(directory) / 'notes_log.jsonl').is_file())

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
            window.toggle_page()
            self.assertEqual(window.current_page, 'habits')
            window.toggle_notes_page()
            self.assertEqual(window.current_page, 'notes')
            self.assertIn('暂无便签', window.notes_status.text())
            window.toggle_notes_page()
            self.assertEqual(window.current_page, 'habits')
            window.save_quick_note('界面保存测试')
            self.app.processEvents()
            self.assertEqual(window.current_page, 'notes')
            self.assertEqual(window.task_list_widget.count(), 1)
            self.assertIn('界面保存测试', window.task_list_widget.item(0).text())
            self.assertNotIn('双击查看', window.notes_status.text())
            window.toggle_notes_page()
            self.assertEqual(window.current_page, 'habits')
            window.toggle_page()
            self.assertEqual(window.current_page, 'tasks')
            window.close()
            hotkey.return_value.close.assert_called_once()

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
