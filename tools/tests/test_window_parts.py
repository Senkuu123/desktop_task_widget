"""窗口拆分后的类身份、任务信号和Qt事件回归；数据与系统设置均隔离。"""

import os
import json
import sys
import tempfile
from contextlib import contextmanager, ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from PyQt5.QtCore import QAbstractAnimation, QCoreApplication, QEvent, QPoint, QTimer, Qt
from PyQt5.QtGui import QCursor, QResizeEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget
from task import Task
import storage
from water_reminder import WaterReminder
from window_parts import notes, tasks, window


@contextmanager
def isolated_window():
    """使用真实Qt窗口，替换数据和开机设置边界，供自动测试及Windows专项验证共用。"""
    with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
        stack.enter_context(patch.object(storage, 'get_data_dir', return_value=directory))
        stack.enter_context(patch.multiple(storage, **{
            name: str(Path(directory) / filename) for name, filename in (
                ('TASKS_FILE', 'tasks.json'), ('SETTINGS_FILE', 'settings.json'),
                ('HABITS_FILE', 'habits.json'), ('WATER_FILE', 'water.json'),
                ('WATER_LOG_FILE', 'water_log.json'), ('HABIT_LOG_FILE', 'habit_log.json'))
        }))
        stack.enter_context(patch.object(notes, 'get_data_dir', return_value=directory))
        hotkey = stack.enter_context(patch.object(window, 'NoteHotkey'))
        hotkey.return_value.registered = True
        stack.enter_context(patch.object(window, 'AutoStartManager'))
        stack.enter_context(patch.object(window, 'load_water_reminder', return_value=WaterReminder()))
        for name in ('load_window_settings', 'save_window_settings', 'delayed_task_load',
                     'check_autostart_launch', 'setup_windows_specific'):
            stack.enter_context(patch.object(window.TransparentTaskWindow, name))
        widget = window.TransparentTaskWindow()
        try:
            yield widget
        finally:
            widget.close()
            for value in list(vars(widget).values()) + widget.findChildren(QTimer):
                if isinstance(value, (QTimer, QAbstractAnimation)):
                    value.stop()
            widget.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class WindowPartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_compatibility_entry_exports_same_classes(self):
        import task_window
        from window_parts import settings_dialog, task_item, water_settings, water_widgets
        self.assertIs(task_window.TransparentTaskWindow, window.TransparentTaskWindow)
        self.assertIs(task_window.TaskListWidgetItem, task_item.TaskListWidgetItem)
        self.assertIs(task_window.SettingsDialog, settings_dialog.SettingsDialog)
        self.assertIs(task_window.WaterProgressBar, water_widgets.WaterProgressBar)
        self.assertIs(task_window.WaterDisplayWidget, water_widgets.WaterDisplayWidget)
        self.assertIs(task_window._WaterSettingsDialog, water_settings._WaterSettingsDialog)
        self.assertEqual(window.TransparentTaskWindow.__mro__.count(QWidget), 1)

    def test_task_row_parent_lookup_and_completion_signal(self):
        with isolated_window() as widget, patch.object(tasks, 'save_tasks_to_json') as save:
            task = Task('拆分回归任务', '2099-01-01 12:00', task_id=1)
            widget.tasks = [task]
            widget.refresh_task_display()
            row = widget.task_list_widget.itemWidget(widget.task_list_widget.item(0))
            self.assertIs(row._get_parent_window(), widget)
            emitted = []
            row.task_status_changed.connect(lambda task_id, done: emitted.append((task_id, done)))
            row.checkbox.setChecked(True)
            self.assertTrue(task.is_done)
            self.assertIsNotNone(task.completed_at)
            self.assertEqual(emitted, [(1, True)])
            save.assert_called_once_with(widget.tasks)

    def test_daily_water_reset_writes_only_isolated_log(self):
        from window_parts.water_widgets import WaterDisplayWidget
        with isolated_window() as widget:
            water_widget = widget.findChild(WaterDisplayWidget)
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            water_widget.water.today_date = yesterday
            water_widget.water.today_intake = 250
            water_widget.update_countdown()
            log_path = Path(storage.WATER_LOG_FILE)
            self.assertEqual(log_path.parent, Path(storage.get_data_dir()))
            self.assertEqual(json.loads(log_path.read_text(encoding='utf-8'))[yesterday]['total_intake'], 250)

    def test_qt_events_resize_and_close_dispatch(self):
        failures = []
        with isolated_window() as widget, patch.object(
                sys, 'excepthook', side_effect=lambda *error: failures.append(error)):
            widget.show()
            widget.resize(410, 380)
            QTest.qWait(30)
            self.assertEqual((widget.width(), widget.height()), (410, 380))
            with patch.object(QCursor, 'pos', return_value=widget.mapToGlobal(QPoint(0, 0))):
                QApplication.sendEvent(widget, QEvent(QEvent.Enter))
                self.assertEqual(widget.cursor().shape(), Qt.SizeFDiagCursor)
                QApplication.sendEvent(widget, QEvent(QEvent.Leave))
                self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
            widget.show_page('notes')
            with patch.object(widget, 'resize_note_cards') as resize_cards:
                viewport = widget.task_list_widget.viewport()
                QApplication.sendEvent(viewport, QResizeEvent(viewport.size(), viewport.size()))
                self.app.processEvents()
                self.assertTrue(resize_cards.called)
            widget.close()
            widget.note_hotkey.close.assert_called_once()
            widget.save_window_settings.assert_called_once()
            self.assertEqual(failures, [])

    def test_deadline_notification_stays_deduplicated(self):
        with isolated_window() as widget, patch.object(widget, 'show_deadline_notification') as notify:
            deadline = (datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M')
            task = Task('即将到期', deadline, task_id=2)
            widget.tasks = [task]
            widget.water_reminder = None
            widget.check_deadline_notifications()
            widget.check_deadline_notifications()
            self.assertEqual(notify.call_count, 1)
            self.assertEqual(notify.call_args.args[0], task.content)
            task.mark_done()
            widget.check_deadline_notifications()
            self.assertNotIn(task.id, widget.notified_task_ids)


if __name__ == '__main__':
    unittest.main()
