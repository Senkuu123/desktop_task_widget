"""真实Windows Qt窗口动画和定时器回归；鼠标坐标注入，不移动用户鼠标或写用户数据。"""

import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'windows'
PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import setup_dpi_scaling
from PyQt5.QtCore import QPoint, QPropertyAnimation
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from test_window_parts import isolated_window
from window_parts import edge_hide


def main():
    setup_dpi_scaling()
    app = QApplication([])
    assert app.platformName() == 'windows', '必须使用真实Windows Qt平台'
    screen = app.primaryScreen().geometry()
    errors = []
    results = []
    with patch.object(sys, 'excepthook', side_effect=lambda *error: errors.append(error)):
        for edge in ('left', 'right', 'top'):
            with isolated_window() as widget:
                x = screen.left() if edge == 'left' else (
                    screen.right() + 1 - widget.width() if edge == 'right' else screen.left() + 100)
                y = screen.top() if edge == 'top' else screen.top() + 100
                widget.move(x, y)
                widget.show()
                QTest.qWait(100)
                outside = QPoint(screen.right() - 10, screen.bottom() - 10)
                cursor = [outside]
                trigger = QPoint(screen.left(), y + 20) if edge == 'left' else (
                    QPoint(screen.right(), y + 20) if edge == 'right' else QPoint(x + 20, screen.top()))
                with patch.object(edge_hide.QCursor, 'pos', side_effect=lambda: cursor[0]), \
                        patch.object(widget, '_check_rehide', wraps=widget._check_rehide) as rehide_check:
                    widget._hide_at_edge(edge)
                    assert widget._hide_anim.state() == QPropertyAnimation.Running
                    QTest.qWait(450)
                    assert widget.edge_hidden and widget.edge_restore_timer.isActive()
                    cursor[0] = trigger
                    # 等待100ms探测定时器和300ms恢复动画真实执行。
                    QTest.qWait(600)
                    assert not widget.edge_hidden and not widget._restoring
                    assert widget._show_anim.state() == QPropertyAnimation.Stopped
                    # 模拟窗口被系统向内偏移2逻辑像素，鼠标仍停在原唤出条。
                    offset = QPoint(2, 0) if edge == 'left' else (
                        QPoint(-2, 0) if edge == 'right' else QPoint(0, 2))
                    widget.move(widget.pos() + offset)
                    before = rehide_check.call_count
                    for _ in range(10):
                        QTest.qWait(220)
                        assert not widget.edge_hidden, f'{edge}持续悬停时意外隐藏'
                    checks = rehide_check.call_count - before
                    assert checks >= 8, f'{edge}再隐藏定时器未持续运行'
                    cursor[0] = outside
                    QTest.qWait(650)
                    assert widget.edge_hidden, f'{edge}移出后未隐藏'
                    assert widget._hide_anim.state() == QPropertyAnimation.Stopped
                    results.append({'edge': edge, 'hover_timer_checks': checks, 'result': 'passed'})
    assert not errors, errors
    print(json.dumps({'platform': app.platformName(), 'mouse': 'injected logical coordinates',
                      'real_window_animation': True, 'results': results}, ensure_ascii=False))


if __name__ == '__main__':
    main()
