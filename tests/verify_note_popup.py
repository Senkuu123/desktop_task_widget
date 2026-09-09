"""Windows真实Qt窗口激活切换验证；不创建或修改便签数据。"""
import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
os.environ['QT_QPA_PLATFORM'] = 'windows'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import setup_dpi_scaling
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtTest import QTest
from quick_notes.dialog import QuickNoteDialog

ctypes.windll.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
ctypes.windll.user32.SetForegroundWindow.restype = wintypes.BOOL


def activate(widget):
    widget.show()
    widget.raise_()
    widget.activateWindow()
    ctypes.windll.user32.SetForegroundWindow(int(widget.winId()))
    QTest.qWait(150)


def main():
    setup_dpi_scaling()
    app = QApplication([])
    outside = QWidget()
    outside.setWindowTitle('便签焦点验证')
    outside.resize(100, 100)
    dialog = QuickNoteDialog(lambda content: None)
    try:
        activate(outside)
        activate(dialog)
        dialog.editor.setPlainText('验证用草稿，不写入文件')
        assert dialog.isActiveWindow(), '测试窗口未取得焦点'
        activate(outside)
        assert not dialog.isVisible(), '点击其他窗口未收起'
        activate(dialog)
        assert dialog.editor.toPlainText() == '验证用草稿，不写入文件'
        dialog.pin_button.setChecked(True)
        activate(outside)
        assert dialog.isVisible(), '固定窗口不应失焦收起'
        activate(dialog)
        dialog.pin_button.setChecked(False)
        menu = dialog.editor.createStandardContextMenu()
        menu.popup(dialog.editor.mapToGlobal(QPoint(30, 30)))
        QTest.qWait(100)
        assert dialog.isVisible(), '自有右键菜单不应收起便签'
        QTest.mouseClick(outside, Qt.LeftButton)
        activate(outside)
        menu.close()
        QTest.qWait(150)
        assert not dialog.isVisible(), '关闭右键菜单后点击外部未收起'
        print('Windows焦点切换、草稿保留、固定和右键菜单验证通过')
    finally:
        dialog.close()
        outside.close()


if __name__ == '__main__':
    main()
