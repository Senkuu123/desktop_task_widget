from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QCursor


class WindowEdgeHideMixin:
    def _check_near_edge(self):
        geo = self.geometry()
        screen = QApplication.screenAt(self.pos())
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()
        threshold = 5

        dists = {}
        if abs(geo.left() - sg.left()) <= threshold:
            dists['left'] = abs(geo.left() - sg.left())
        if abs(sg.right() - geo.right()) <= threshold:
            dists['right'] = abs(sg.right() - geo.right())
        if abs(geo.top() - sg.top()) <= threshold:
            dists['top'] = abs(geo.top() - sg.top())

        if not dists:
            return None
        best_dist = min(dists.values())
        candidates = [e for e, d in dists.items() if d == best_dist]
        if len(candidates) == 1:
            return candidates[0]
        # 等距离时优先 top > right > left
        for preferred in ('top', 'right', 'left'):
            if preferred in candidates:
                return preferred
        return candidates[0]

    def _hide_at_edge(self, edge):
        """窗口完全滑出屏幕边缘，靠2px条触发恢复"""
        if self.edge_hidden:
            return
        self.edge_hidden = True
        self._current_edge = edge
        self._should_rehide = True
        self._original_pos = self.pos()
        self._temp_shown = False
        self._restoring = False
        self._edge_show_pos = None
        self._stop_restore_timer()
        self._stop_rehide_timer()

        geo = self.geometry()
        # 用窗口位置取屏幕，比center()更可靠（边缘处center可能跨屏）
        screen = QApplication.screenAt(self.pos())
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()

        self._edge_screen_geometry = sg
        targets = {
            'left':   (sg.left() - geo.width(), geo.y()),
            'right':  (sg.right() + 1, geo.y()),
            'top':    (geo.x(), sg.top() - geo.height()),
        }
        show_targets = {
            'left':   (sg.left() - geo.width() + 2, geo.y()),
            'right':  (sg.right() - 1, geo.y()),
            'top':    (geo.x(), sg.top() - geo.height() + 2),
        }
        tx, ty = targets.get(edge, (geo.x(), geo.y()))

        # 方向校验：target必须在正确的一侧，否则回退到主屏幕
        bad = False
        if edge == 'left' and tx >= sg.left():
            bad = True
        elif edge == 'right' and tx <= sg.right():
            bad = True
        elif edge == 'top' and ty >= sg.top():
            bad = True
        if bad:
            screen = QApplication.primaryScreen()
            sg = screen.geometry()
            targets = {
                'left':   (sg.left() - geo.width(), geo.y()),
                'right':  (sg.right() + 1, geo.y()),
                'top':    (geo.x(), sg.top() - geo.height()),
            }
            show_targets = {
                'left':   (sg.left() - geo.width() + 2, geo.y()),
                'right':  (sg.right() - 1, geo.y()),
                'top':    (geo.x(), sg.top() - geo.height() + 2),
            }
            tx, ty = targets.get(edge, (geo.x(), geo.y()))

        self._edge_hide_pos = (tx, ty)
        self._edge_show_pos = show_targets.get(edge, (geo.x(), geo.y()))

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setEndValue(QPoint(tx, ty))
        anim.finished.connect(self._on_hide_anim_done)
        self._hide_anim = anim
        anim.start()

    def _on_hide_anim_done(self):
        if self.edge_hidden:
            # 隐藏完成后始终保持TopMost，确保2px条可被鼠标触发
            try:
                import ctypes
                hwnd = int(self.winId())
                SWP_NOACTIVATE = 0x0010
                HWND_TOPMOST = -1
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    0x0002 | 0x0001 | SWP_NOACTIVATE)  # SWP_NOMOVE | SWP_NOSIZE
            except Exception:
                pass
            self._start_restore_timer()

    def _restore_from_edge(self):
        """窗口滑回原始位置"""
        if not self.edge_hidden:
            return
        self.edge_hidden = False
        self._temp_shown = False
        self._restoring = True
        self._stop_restore_timer()

        if self._hide_anim and self._hide_anim.state() == QPropertyAnimation.Running:
            self._hide_anim.stop()
        if self._show_anim and self._show_anim.state() == QPropertyAnimation.Running:
            self._show_anim.stop()

        orig = self._original_pos if self._original_pos is not None else self.pos()
        screen = QApplication.screenAt(orig)
        if screen:
            sg = screen.geometry()
        else:
            sg = QApplication.primaryScreen().geometry()
        # QRect的right/bottom包含末端像素，恢复位置须与吸附位置一致。
        ox = max(sg.left(), min(orig.x(), sg.right() + 1 - self.width()))
        oy = max(sg.top(), min(orig.y(), sg.bottom() + 1 - self.height()))

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setEndValue(QPoint(ox, oy))
        anim.finished.connect(self._on_restore_anim_done)
        self._show_anim = anim
        anim.start()

    def _on_restore_anim_done(self):
        # 恢复动画结束，取消TopMost
        if self._restoring:
            self._restoring = False
            try:
                import ctypes
                hwnd = int(self.winId())
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                HWND_NOTOPMOST = -2
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            except Exception:
                pass
        if self._should_rehide and self._current_edge:
            self._start_rehide_timer()

    def _start_restore_timer(self):
        if self.edge_restore_timer:
            return
        self.edge_restore_timer = QTimer(self)
        self.edge_restore_timer.timeout.connect(self._check_cursor_near_hidden_edge)
        self.edge_restore_timer.start(100)

    def _stop_restore_timer(self):
        if self.edge_restore_timer:
            self.edge_restore_timer.stop()
            self.edge_restore_timer = None

    def _cursor_in_edge_trigger(self, pos):
        # 唤出和保持展开使用同一屏幕、同一条触发区域，避免坐标舍入形成缝隙。
        edge = self._current_edge
        origin = self._original_pos if self._original_pos is not None else self.pos()
        sg = getattr(self, '_edge_screen_geometry', None)
        if sg is None:
            screen = QApplication.screenAt(origin) or QApplication.primaryScreen()
            sg = screen.geometry()
        # 高DPI原生像素转逻辑坐标可能舍入到right+1/bottom+1。
        if not sg.adjusted(-1, -1, 1, 1).contains(pos):
            return False
        if edge == 'left':
            return pos.x() <= sg.left() + 1 and origin.y() <= pos.y() < origin.y() + self.height()
        if edge == 'right':
            return pos.x() >= sg.right() - 1 and origin.y() <= pos.y() < origin.y() + self.height()
        if edge == 'top':
            return pos.y() <= sg.top() + 1 and origin.x() <= pos.x() < origin.x() + self.width()
        return False

    def _check_cursor_near_hidden_edge(self):
        """检测光标是否进入被隐藏边缘的2px条，触发恢复。"""
        if not self.edge_hidden or not self._current_edge or self._restoring:
            return
        if self._hide_anim and self._hide_anim.state() == QPropertyAnimation.Running:
            return
        if self._cursor_in_edge_trigger(QCursor.pos()):
            self._restore_from_edge()

    def _start_rehide_timer(self):
        if self._rehide_timer:
            return
        self._rehide_timer = QTimer(self)
        self._rehide_timer.timeout.connect(self._check_rehide)
        self._rehide_timer.start(200)

    def _stop_rehide_timer(self):
        if self._rehide_timer:
            self._rehide_timer.stop()
            self._rehide_timer = None

    def _check_rehide(self):
        if not self._should_rehide or not self._current_edge:
            self._stop_rehide_timer()
            return
        if self._pending_hide or self._restoring or self.edge_hidden:
            return
        cursor = QCursor.pos()
        geo = self.geometry()
        if not geo.contains(cursor) and not self._cursor_in_edge_trigger(cursor):
            self._stop_rehide_timer()
            edge = self._current_edge
            self._hide_at_edge(edge)

    def _start_pending_hide_timer(self):
        if self._pending_hide_timer:
            return
        self._should_rehide = False
        self._stop_rehide_timer()
        self._pending_hide_timer = QTimer(self)
        self._pending_hide_timer.timeout.connect(self._check_pending_hide)
        self._pending_hide_timer.start(150)

    def _stop_pending_hide_timer(self):
        if self._pending_hide_timer:
            self._pending_hide_timer.stop()
            self._pending_hide_timer = None

    def _check_pending_hide(self):
        if not self._pending_hide:
            self._stop_pending_hide_timer()
            return
        geo = self._pending_hide_geometry or self.geometry()
        if not geo.contains(QCursor.pos()):
            self._stop_pending_hide_timer()
            edge = self._pending_hide_edge
            self._pending_hide = False
            if edge:
                self._hide_at_edge(edge)
