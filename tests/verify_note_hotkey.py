"""无可见窗口地验证Windows注册冲突、原生事件投递和释放。"""

import ctypes
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM'] = 'windows'
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from quick_notes.hotkey import NoteHotkey


def main():
    app = QApplication([])
    seen = []
    hotkey = NoteHotkey(app, lambda: (seen.append(True), app.quit()))
    if not hotkey.registered:
        raise RuntimeError('Ctrl+Alt+N已被占用，无法完成系统注册验证')
    try:
        # 不向其他应用发送按键，仅投递本进程已注册的快捷键消息。
        assert not ctypes.windll.user32.RegisterHotKey(None, 0x4E02, 0x4003, 0x4E)
        thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        QTimer.singleShot(0, lambda: ctypes.windll.user32.PostThreadMessageW(
            thread_id, 0x0312, hotkey.HOTKEY_ID, 0))
        QTimer.singleShot(2000, app.quit)
        app.exec_()
        assert seen == [True], '原生快捷键消息未触发回调'
    finally:
        hotkey.close()
        ctypes.windll.user32.UnregisterHotKey(None, 0x4E02)
    replacement = NoteHotkey(app, lambda: None)
    try:
        assert replacement.registered, '快捷键未正确释放'
    finally:
        replacement.close()
    print('Windows快捷键注册、冲突、原生事件投递和释放验证通过')


if __name__ == '__main__':
    main()
