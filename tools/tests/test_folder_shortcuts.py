"""快捷文件夹路径、排序保存及待办页空间分配回归，使用临时数据。"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_window_parts import isolated_window, window, storage, Task
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QMenu
from window_parts.folder_shortcuts import FolderShortcuts, FolderGrid

SAVE_SETTINGS = window.TransparentTaskWindow.save_window_settings
LOAD_SETTINGS = window.TransparentTaskWindow.load_window_settings


class FolderShortcutsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_add_edit_remove_validation_and_cancel(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / '中文 文件夹'
            second = Path(directory) / 'second'
            first.mkdir()
            second.mkdir()
            panel = FolderShortcuts()
            changes = []
            panel.changed.connect(lambda: changes.append(True))
            with patch('window_parts.folder_shortcuts.QMessageBox.information'), patch(
                    'window_parts.folder_shortcuts.QMessageBox.warning') as warning:
                self.assertTrue(panel.set_path(str(first)))
                self.assertFalse(panel.set_path(str(first / '..' / first.name)))
                self.assertFalse(panel.set_path(str(first / 'missing')))
                warning.assert_called_once()
                item = panel.grid.item(0)
                self.assertTrue(panel.set_path(str(second), item))
                self.assertEqual(item.text(), 'second')
                with patch('window_parts.folder_shortcuts.QFileDialog.getExistingDirectory', return_value='') as choose:
                    panel.choose_folder(item)
                    panel.choose_folder()
                    for call in choose.call_args_list:
                        self.assertFalse(call.args[3] & QFileDialog.DontUseNativeDialog)
                        self.assertTrue(call.args[3] & QFileDialog.ShowDirsOnly)
                self.assertEqual(panel.paths(), [str(second)])
                panel.remove_folder(item)
                self.assertEqual(panel.paths(), [])
                self.assertTrue(second.is_dir())
                self.assertEqual(len(changes), 3)
            panel.deleteLater()

    def test_sort_and_settings_restore(self):
        with isolated_window() as widget:
            grid = widget.folder_shortcuts.grid
            paths = [str(Path(storage.get_data_dir()) / name) for name in ('one', 'two', 'three')]
            for path in paths:
                Path(path).mkdir()
                widget.folder_shortcuts.set_path(path)
            widget.resize(450, 600)
            widget.show()
            self.app.processEvents()
            panel = widget.folder_shortcuts
            panel.select_sort('name')
            self.assertEqual(panel.paths(), [paths[0], paths[2], paths[1]])
            panel.select_sort('name')
            self.assertEqual(panel.paths(), [paths[1], paths[2], paths[0]])
            widget.folder_shortcuts.toggle_collapsed()
            SAVE_SETTINGS(widget)
            LOAD_SETTINGS(widget)
            restored = FolderShortcuts(widget.folder_paths, widget.folders_collapsed,
                                       sort_key=widget.folder_sort_key, sort_desc=widget.folder_sort_desc)
            self.assertEqual(restored.paths(), [paths[1], paths[2], paths[0]])
            self.assertEqual(restored.sort_key, 'name')
            self.assertTrue(restored.sort_desc)
            self.assertTrue(restored.collapsed)
            self.assertTrue(restored.grid.isHidden())
            restored.deleteLater()

    def test_layout_collapse_scroll_and_page_switch(self):
        with isolated_window() as widget:
            widget.tasks = [Task(f'待办任务{i}', '2099-01-01 12:00', task_id=i) for i in range(25)]
            widget.refresh_task_display()
            widget.resize(400, 600)
            widget.show()
            self.app.processEvents()
            panel = widget.folder_shortcuts
            expanded_height = widget.task_list_widget.height()
            self.assertGreater(panel.height(), 200)
            self.assertGreater(widget.task_list_widget.verticalScrollBar().maximum(), 0)
            panel.header.click()
            self.app.processEvents()
            self.assertEqual(panel.height(), panel.header.height())
            self.assertGreater(widget.task_list_widget.height(), expanded_height + 150)
            panel.header.click()
            self.app.processEvents()
            self.assertEqual(widget.task_list_widget.height(), expanded_height)
            for page in ('notes', 'habits', 'water'):
                widget.show_page(page)
                self.app.processEvents()
                self.assertTrue(panel.isHidden())
            widget.show_page('tasks')
            self.app.processEvents()
            self.assertFalse(panel.isHidden())
            widget.resize(300, 280)
            widget.current_font_size = 20
            widget.update_window_style()
            self.app.processEvents()
            self.assertGreater(widget.task_list_widget.height(), 0)
            self.assertLessEqual(panel.geometry().bottom(), widget.list_container.height())
            self.assertLessEqual(panel.grid.gridSize().width(), panel.grid.viewport().width())

    def test_date_sort_missing_path_and_menu_toggle(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [str(Path(directory) / name) for name in ('a', 'b', 'c')]
            for index, path in enumerate(paths):
                Path(path).mkdir()
                os.utime(path, (1000 + index * 100, 1000 + index * 100))
            missing = str(Path(directory) / 'missing')
            panel = FolderShortcuts([paths[1], missing, paths[2], paths[0]])
            menu = QMenu()
            panel.add_blank_actions(menu)
            menu.actions()[-1].trigger()
            self.assertEqual(panel.paths(), paths + [missing])
            menu.actions()[-1].trigger()
            self.assertEqual(panel.paths(), paths[::-1] + [missing])
            with patch('window_parts.folder_shortcuts.QMessageBox.information'):
                panel.set_path(paths[0], panel.grid.item(0))
            self.assertEqual(panel.paths(), paths[::-1] + [missing])
            panel.deleteLater()

    def test_three_square_tiles_at_minimum_width(self):
        with isolated_window() as widget:
            panel = widget.folder_shortcuts
            for i in range(9):
                panel.add_item(f'C:/folder{i}')
            widget.resize(300, 280)
            widget.show()
            for font_size in (8, 11, 20):
                widget.current_font_size = font_size
                widget.update_window_style()
                QTest.qWait(30)
                rects = [panel.grid.visualItemRect(panel.grid.item(i)) for i in range(4)]
                self.assertTrue(all(rect.width() == rect.height() for rect in rects))
                self.assertEqual(rects[0].top(), rects[2].top())
                self.assertGreater(rects[3].top(), rects[0].top())
                self.assertLess(rects[2].right(), panel.grid.viewport().width())
                self.assertLess(panel.grid.iconSize().width(), rects[0].width() // 2)

    def test_grid_settles_at_scrollbar_threshold(self):
        panel = FolderShortcuts([f'C:/folder{i}' for i in range(6)])
        panel.apply_style(11, 100)
        panel.show()
        try:
            for height in (221, 225, 235, 245, 255):
                panel.resize(300, height)
                QTest.qWait(40)
                with patch.object(panel.grid, 'fit_grid', wraps=panel.grid.fit_grid) as fit:
                    before = panel.grid.gridSize()
                    QTest.qWait(80)
                    self.assertLessEqual(fit.call_count, 2, f'布局在高度{height}持续振荡')
                    self.assertEqual(panel.grid.gridSize(), before)
        finally:
            panel.close()
            panel.deleteLater()

    def test_fixed_tiles_and_splitter_height_persistence(self):
        with isolated_window() as widget:
            panel = widget.folder_shortcuts
            for i in range(12):
                panel.add_item(f'C:/folder{i}')
            widget.resize(300, 600)
            widget.show()
            QTest.qWait(40)
            grid_size, icon_size = panel.grid.gridSize(), panel.grid.iconSize()
            for width in (410, 520, 800, 300):
                widget.resize(width, 600)
                QTest.qWait(20)
                self.assertEqual(panel.grid.gridSize(), grid_size)
                self.assertEqual(panel.grid.iconSize(), icon_size)
                first = panel.grid.visualItemRect(panel.grid.item(0)).translated(panel.grid.viewport().pos())
                self.assertEqual(first.left(), 0)
            splitter = widget.task_folder_splitter
            splitter.moveSplitter(140, 1)
            QTest.qWait(20)
            top = widget.task_list_widget.height()
            bottom = panel.height()
            widget.resize(300, 780)
            QTest.qWait(30)
            self.assertEqual(widget.task_list_widget.height(), top)
            self.assertEqual(panel.height(), bottom + 180)
            SAVE_SETTINGS(widget)
            LOAD_SETTINGS(widget)
            self.assertEqual(widget.task_area_height, top)
            panel.header.click()
            QTest.qWait(20)
            self.assertGreater(widget.task_list_widget.height(), top)
            self.assertEqual(splitter.handle(1).height(), 0)
            panel.header.click()
            QTest.qWait(20)
            self.assertEqual(widget.task_list_widget.height(), top)
            widget.show_page('notes')
            QTest.qWait(20)
            self.assertEqual(splitter.handle(1).height(), 0)
            widget.show_page('tasks')
            QTest.qWait(20)
            self.assertEqual(widget.task_list_widget.height(), top)

    def test_hidden_scrollbar_wheel_and_left_aligned_row(self):
        with isolated_window() as widget:
            panel = widget.folder_shortcuts
            for i in range(12):
                panel.add_item(f'C:/folder{i}')
            widget.resize(300, 400)
            widget.show()
            QTest.qWait(40)
            grid = panel.grid
            bar = grid.verticalScrollBar()
            self.assertFalse(bar.isVisible())
            self.assertGreater(bar.maximum(), 0)
            first = grid.visualItemRect(grid.item(0)).translated(grid.viewport().pos())
            third = grid.visualItemRect(grid.item(2)).translated(grid.viewport().pos())
            self.assertEqual(first.left(), 0)
            self.assertEqual(first.top(), third.top())
            position = grid.viewport().rect().center()
            for delta in (-120, 120):
                previous = bar.value()
                event = QWheelEvent(QPointF(position), QPointF(grid.viewport().mapToGlobal(position)),
                                    QPoint(), QPoint(0, delta), Qt.NoButton, Qt.NoModifier,
                                    Qt.NoScrollPhase, False)
                self.app.sendEvent(grid.viewport(), event)
                self.app.processEvents()
                self.assertGreater(bar.value(), previous) if delta < 0 else self.assertLess(bar.value(), previous)
                self.assertFalse(bar.isVisible())

    def test_open_uses_local_url_and_handles_missing_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            panel = FolderShortcuts([directory])
            with patch('window_parts.folder_shortcuts.QDesktopServices.openUrl', return_value=True) as opened:
                panel.open_folder(panel.grid.item(0))
                self.assertEqual(os.path.normpath(opened.call_args.args[0].toLocalFile()), directory)
            panel.update_item(panel.grid.item(0), str(Path(directory) / 'missing'))
            with patch('window_parts.folder_shortcuts.QDesktopServices.openUrl') as opened, patch(
                    'window_parts.folder_shortcuts.QMessageBox.warning') as warning:
                panel.open_folder(panel.grid.item(0))
                opened.assert_not_called()
                warning.assert_called_once()
            panel.deleteLater()

    def test_old_or_invalid_optional_settings(self):
        panel = FolderShortcuts()
        self.assertFalse(panel.collapsed)
        self.assertEqual(panel.paths(), [])
        panel.deleteLater()
        panel = FolderShortcuts([None, '', 'C:/example', 'C:/example'])
        self.assertEqual(len(panel.paths()), 1)
        panel.deleteLater()


if __name__ == '__main__':
    unittest.main()
