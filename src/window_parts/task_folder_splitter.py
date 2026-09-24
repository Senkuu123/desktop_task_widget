"""待办高度由分隔线设定，窗口新增高度交给文件夹区域。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QSplitter


class TaskFolderSplitter(QSplitter):
    allocation_changed = pyqtSignal()

    def __init__(self, preferred_task_height=None, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.preferred_task_height = preferred_task_height
        self.setChildrenCollapsible(False)
        self.setHandleWidth(6)
        self.setStyleSheet('''
            QSplitter::handle { background: transparent; }
            QSplitter::handle:hover { background: rgba(180,180,180,70); }
            QSplitter::handle:pressed { background: rgba(180,180,180,110); }
        ''')
        self.splitterMoved.connect(self.remember_allocation)

    def remember_allocation(self, position, index):
        if self.count() == 2 and not self.widget(1).collapsed:
            self.preferred_task_height = self.sizes()[0]
            self.allocation_changed.emit()

    def apply_allocation(self):
        if self.count() != 2:
            return
        folders = self.widget(1)
        expanded = not folders.isHidden() and not folders.collapsed
        self.setHandleWidth(6 if expanded else 0)
        self.handle(1).setFixedHeight(6 if expanded else 0)
        self.handle(1).setEnabled(expanded)
        self.handle(1).setVisible(expanded)
        self.handle(1).setToolTip('上下拖动，调整待办与文件夹区域高度')
        if not expanded:
            return
        if self.preferred_task_height is None:
            if not self.isVisible():
                return
            self.preferred_task_height = max(40, (self.height() - self.handleWidth()) // 2)
        available = max(0, self.height() - self.handleWidth())
        top = min(self.preferred_task_height, max(40, available - folders.minimumHeight()))
        self.setSizes([top, max(0, available - top)])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_allocation()

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_allocation()
