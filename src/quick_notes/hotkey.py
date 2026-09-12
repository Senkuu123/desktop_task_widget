"""Windows线程级全局快捷键，不依赖会被置顶操作重建的窗口句柄。"""

import ctypes
import sys
from ctypes import wintypes
from PyQt5.QtCore import QAbstractNativeEventFilter, QTimer


class NoteHotkey(QAbstractNativeEventFilter):
    HOTKEY_ID = 0x4E01

    def __init__(self, app, callback):
        super().__init__()
        self.app = app
        self.callback = callback
        self.registered = False
        if sys.platform == 'win32':
            # MOD_CONTROL | MOD_ALT | MOD_NOREPEAT，N。
            self.registered = bool(ctypes.windll.user32.RegisterHotKey(
                None, self.HOTKEY_ID, 0x0002 | 0x0001 | 0x4000, 0x4E))
        if self.registered:
            app.installNativeEventFilter(self)
            app.aboutToQuit.connect(self.close)

    def nativeEventFilter(self, event_type, message):
        if self.registered and bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.HOTKEY_ID:
                QTimer.singleShot(0, self.callback)
                return True, 0
        return False, 0

    def close(self):
        if self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, self.HOTKEY_ID)
            self.app.removeNativeEventFilter(self)
            self.registered = False
