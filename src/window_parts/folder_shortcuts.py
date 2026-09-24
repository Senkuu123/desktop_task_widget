"""待办页底部的文件夹网格，支持名称和修改日期排序。"""

import os

from PyQt5.QtCore import Qt, QSize, QUrl, QRect, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QTextLayout, QTextOption, QPalette, QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView,
    QPushButton, QFileIconProvider, QFileDialog, QMenu, QMessageBox, QSizePolicy,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle,
)


class FolderDelegate(QStyledItemDelegate):
    """固定两行名称，避免长文件夹名侵入下一行图标。"""

    def paint(self, painter, option, index):
        painter.save()
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        text, icon = styled.text, styled.icon
        if option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect.adjusted(2, 2, -2, -2), QColor(255, 255, 255, 30))
        rect = option.rect.adjusted(8, 6, -8, -6)
        icon_size = self.parent().iconSize().width()
        painter.setClipRect(rect)
        font = QFont(option.font)
        font.setPixelSize(max(10, min(option.fontMetrics.height(), int(option.rect.width() * 0.14))))
        metrics = QFontMetrics(font)
        painter.setFont(font)
        painter.setPen(styled.palette.color(QPalette.Text))
        layout = QTextLayout(text, font)
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(text_option)
        layout.beginLayout()
        lines = []
        for row in range(2):
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(rect.width())
            part = text[line.textStart():line.textStart() + line.textLength()]
            if row == 1:
                part = metrics.elidedText(text[line.textStart():], Qt.ElideRight, rect.width())
            lines.append(part)
        layout.endLayout()
        gap = 8
        content_height = icon_size + gap + len(lines) * metrics.lineSpacing()
        top = rect.top() + (rect.height() - content_height) // 2
        left = rect.left() + (rect.width() - icon_size) // 2
        icon.paint(painter, QRect(left, top, icon_size, icon_size))
        top += icon_size + gap
        for part in lines:
            painter.drawText(QRect(rect.left(), top, rect.width(), metrics.lineSpacing()),
                             Qt.AlignHCenter | Qt.AlignVCenter, part)
            top += metrics.lineSpacing()
        painter.restore()

    def sizeHint(self, option, index):
        return self.parent().gridSize()


class FolderGrid(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideRight)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumSize(0, 0)
        self.setAutoScroll(True)
        self.setAutoScrollMargin(24)
        self.setAccessibleName('文件夹快捷访问，右键选择排序方式')
        self.setItemDelegate(FolderDelegate(self))
        self.fit_grid()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_grid()

    def fit_grid(self):
        # 滚动条不显示、不占位；按固定外部宽度计算，避免布局反馈振荡。
        width = max(3, self.contentsRect().width())
        columns = max(3, width // 96)
        # QListView换行需要比整排列宽多1像素，将这1像素计入右侧余量。
        side = max(1, (width - 1) // columns)
        remainder = width - columns * side
        left = remainder // 2
        right = max(0, remainder - left - 1)
        margins = self.viewportMargins()
        if margins.left() != left or margins.right() != right:
            self.setViewportMargins(left, 0, right, 0)
        size = QSize(side, side)
        if self.gridSize() != size:
            self.setGridSize(size)
        icon_size = max(16, int(side * 0.43))
        size = QSize(icon_size, icon_size)
        if self.iconSize() != size:
            self.setIconSize(size)


class FolderShortcuts(QWidget):
    changed = pyqtSignal()

    def __init__(self, paths=None, collapsed=False, parent=None, sort_key=None, sort_desc=False):
        super().__init__(parent)
        self.setObjectName('FolderShortcuts')
        self.collapsed = bool(collapsed)
        self.sort_key = sort_key if sort_key in ('name', 'modified') else None
        self.sort_desc = bool(sort_desc)
        self.icon_provider = QFileIconProvider()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = QPushButton()
        self.header.setFixedHeight(32)
        self.header.clicked.connect(self.toggle_collapsed)
        layout.addWidget(self.header)
        self.grid = FolderGrid(self)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.show_menu)
        self.grid.itemDoubleClicked.connect(self.open_folder)
        layout.addWidget(self.grid, 1)
        self.header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header.customContextMenuRequested.connect(self.show_header_menu)
        seen = set()
        for path in paths if isinstance(paths, list) else []:
            if not isinstance(path, str) or not path.strip():
                continue
            path = os.path.normpath(path)
            key = os.path.normcase(path)
            if key not in seen:
                self.add_item(path)
                seen.add(key)
        self.apply_sort()
        self.apply_collapsed()

    def paths(self):
        return [self.grid.item(i).data(Qt.UserRole) for i in range(self.grid.count())]

    def add_item(self, path):
        item = QListWidgetItem(self.icon_provider.icon(QFileIconProvider.Folder), '')
        self.update_item(item, path)
        self.grid.addItem(item)
        return item

    @staticmethod
    def update_item(item, path):
        item.setText(os.path.basename(path) or path)
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)

    def set_path(self, path, item=None):
        path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
        if not os.path.isdir(path):
            QMessageBox.warning(self, '文件夹不可用', '该文件夹不存在或暂时无法访问，请重新选择。')
            return False
        if any(os.path.normcase(existing) == os.path.normcase(path)
               for existing in self.paths() if item is None or existing != item.data(Qt.UserRole)):
            QMessageBox.information(self, '文件夹已添加', '这个文件夹已经在快捷访问中。')
            return False
        if item is None:
            self.add_item(path)
        else:
            self.update_item(item, path)
        self.apply_sort()
        self.changed.emit()
        return True

    def choose_folder(self, item=None):
        initial = item.data(Qt.UserRole) if item else ''
        path = QFileDialog.getExistingDirectory(
            self, '修改文件夹路径' if item else '新增文件夹', initial,
            QFileDialog.ShowDirsOnly)
        if path:
            self.set_path(path, item)

    def remove_folder(self, item):
        self.grid.takeItem(self.grid.row(item))
        self.changed.emit()

    def open_folder(self, item):
        path = item.data(Qt.UserRole)
        if not os.path.isdir(path) or not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            QMessageBox.warning(self, '无法打开文件夹', '文件夹不存在或无法打开，可右键修改路径。')

    def create_menu(self):
        menu = QMenu(self)
        # 与快捷便签菜单一致，显式覆盖透明父窗口传下来的背景样式。
        menu.setStyleSheet('''
            QMenu { background: #303030; color: #ddd; border: 1px solid #555; padding: 5px; }
            QMenu::item { padding: 7px 26px 7px 14px; }
            QMenu::item:selected { background: #484848; }
        ''')
        return menu

    def show_header_menu(self, position):
        menu = self.create_menu()
        self.add_blank_actions(menu)
        menu.exec_(self.header.mapToGlobal(position))

    def show_menu(self, position):
        item = self.grid.itemAt(position)
        menu = self.create_menu()
        if item is None:
            self.add_blank_actions(menu)
        else:
            menu.addAction('修改路径…', lambda: self.choose_folder(item))
            menu.addAction('删除快捷入口', lambda: self.remove_folder(item))
        menu.exec_(self.grid.viewport().mapToGlobal(position))

    def add_blank_actions(self, menu):
        menu.addAction('新增文件夹…', lambda: self.choose_folder())
        menu.addSeparator()
        for key, label in (('name', '名称'), ('modified', '修改日期')):
            direction = '降序 ↓' if self.sort_desc else '升序 ↑'
            active = self.sort_key == key
            action = menu.addAction(f'{label}（{direction}）' if active else f'按{label}排序')
            action.setCheckable(True)
            action.setChecked(active)
            action.triggered.connect(lambda checked=False, key=key: self.select_sort(key))

    def select_sort(self, key):
        self.sort_desc = not self.sort_desc if self.sort_key == key else False
        self.sort_key = key
        self.apply_sort()
        self.changed.emit()

    def apply_sort(self):
        if self.sort_key is None:
            return
        selected = self.grid.currentItem()
        items = [self.grid.takeItem(0) for _ in range(self.grid.count())]
        name_key = lambda item: (item.text().casefold(), item.data(Qt.UserRole).casefold())
        if self.sort_key == 'name':
            items.sort(key=name_key, reverse=self.sort_desc)
        else:
            available, missing = [], []
            for item in items:
                try:
                    available.append((os.path.getmtime(item.data(Qt.UserRole)), name_key(item), item))
                except OSError:
                    missing.append(item)
            available.sort(key=lambda entry: entry[:2], reverse=self.sort_desc)
            items = [entry[2] for entry in available] + sorted(missing, key=name_key)
        for item in items:
            self.grid.addItem(item)
        if selected is not None:
            self.grid.setCurrentItem(selected)

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        self.apply_collapsed()
        self.changed.emit()

    def apply_collapsed(self):
        self.header.setText('我的文件夹  ▴' if self.collapsed else '我的文件夹  ▾')
        self.header.setToolTip('点击展开文件夹' if self.collapsed else '点击向下折叠文件夹')
        self.grid.setVisible(not self.collapsed)
        self.setMaximumHeight(self.header.height() if self.collapsed else 16777215)
        self.setMinimumHeight(self.header.height())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed if self.collapsed else QSizePolicy.Ignored)
        self.updateGeometry()

    def apply_style(self, font_size, font_opacity):
        alpha = int(font_opacity * 255 / 100)
        self.setStyleSheet(f'''
            #FolderShortcuts {{ border-top: 1px solid rgba(255,255,255,45); }}
            QPushButton {{ color: rgba(255,255,255,{alpha}); background: transparent;
                border: none; font: {font_size}pt "Microsoft YaHei"; }}
            QPushButton:hover {{ background: rgba(255,255,255,18); }}
            QListWidget {{ color: rgba(255,255,255,{alpha}); background: transparent;
                border: none; outline: none; font: {font_size}pt "Microsoft YaHei"; }}
            QListWidget::item {{ padding: 5px; border-radius: 5px; }}
            QListWidget::item:hover {{ background: rgba(255,255,255,18); }}
        ''')
        self.grid.fit_grid()
        self.header.setFixedHeight(max(32, self.header.fontMetrics().height() + 8))
        self.apply_collapsed()
        self.grid.setToolTip('双击打开文件夹；右键空白处新增文件夹或选择排序方式')
