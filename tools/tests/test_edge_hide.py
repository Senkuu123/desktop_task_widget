"""贴边状态续接回归；真实动画与定时器运行，光标由测试注入。"""

import unittest
from unittest.mock import patch
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from test_window_parts import isolated_window
from window_parts import edge_hide


class EdgeHideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_click_resize_and_startup_continue_hiding(self):
        for operation in ('startup', 'click', 'resize'):
            with self.subTest(operation=operation), isolated_window() as widget:
                screen = self.app.primaryScreen().geometry()
                widget.move(screen.left(), screen.top() + 100)
                cursor = [widget.geometry().center()]
                with patch.object(edge_hide.QCursor, 'pos', side_effect=lambda: cursor[0]):
                    widget.show()
                    QTest.qWait(30)
                    self.assertTrue(widget._pending_hide)
                    if operation == 'click':
                        QTest.mouseClick(widget, Qt.LeftButton, pos=QPoint(20, 60))
                    elif operation == 'resize':
                        widget.resize(widget.width(), widget.height() + 50)
                        widget.resizing = True
                        QTest.mouseRelease(widget, Qt.LeftButton, pos=QPoint(20, 60))
                    self.assertTrue(widget._pending_hide)
                    cursor[0] = QPoint(screen.right() - 20, screen.bottom() - 20)
                    QTest.qWait(650)
                    self.assertTrue(widget.edge_hidden)
                    self.assertFalse(widget._pending_hide)

    def test_popup_delays_hide_and_move_away_cancels(self):
        with isolated_window() as widget:
            screen = self.app.primaryScreen().geometry()
            widget.move(screen.left(), screen.top() + 100)
            cursor = [widget.geometry().center()]
            with patch.object(edge_hide.QCursor, 'pos', side_effect=lambda: cursor[0]):
                widget.show()
                QTest.qWait(30)
                cursor[0] = QPoint(screen.right() - 20, screen.bottom() - 20)
                for method in ('activePopupWidget', 'activeModalWidget'):
                    with patch.object(QApplication, method, return_value=widget):
                        QTest.qWait(220)
                        self.assertFalse(widget.edge_hidden)
                        self.assertTrue(widget._pending_hide)
                # 不依赖拖动事件，定时器也应察觉实际位置已离开屏幕边缘。
                widget.move(screen.left() + 100, screen.top() + 100)
                QTest.qWait(220)
                self.assertFalse(widget.edge_hidden)
                self.assertFalse(widget._pending_hide)
                widget.move(screen.left(), screen.top() + 100)
                widget._schedule_edge_hide()
                QTest.qWait(650)
                self.assertTrue(widget.edge_hidden)


if __name__ == '__main__':
    unittest.main()
