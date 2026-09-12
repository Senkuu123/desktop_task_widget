import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from window_parts.water_widgets import WaterProgressBar, WaterDisplayWidget
from window_parts.water_settings import _WaterSettingsDialog
from window_parts.task_item import TaskListWidgetItem
from window_parts.settings_dialog import SettingsDialog
from window_parts.window import TransparentTaskWindow

__all__ = [
    "WaterProgressBar", "WaterDisplayWidget", "_WaterSettingsDialog",
    "TaskListWidgetItem", "SettingsDialog", "TransparentTaskWindow",
]


if __name__ == '__main__':
    # 高DPI缩放支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # 设置高DPI缩放策略（PyQt5 >= 5.14）
    try:
        app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass
    
    window = TransparentTaskWindow()
    window.show()
    sys.exit(app.exec_())
