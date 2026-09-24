"""Enter保存，Shift+Enter换行；中文输入法选词时不提交。"""

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QSize, QPointF, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF, QTextCursor
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QPlainTextEdit, QPushButton, QWidget, QGraphicsOpacityEffect)
from ui_styles import SCROLLBAR_STYLE


def toolbar_icon(kind, color='#999999', filled=False):
    """使用矢量线条绘制工具图标，避免系统emoji样式差异。"""
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if kind == 'close':
        painter.drawLine(7, 7, 17, 17)
        painter.drawLine(17, 7, 7, 17)
    elif kind == 'pin':
        painter.translate(12, 12)
        painter.rotate(40)
        painter.setBrush(QColor(color) if filled else Qt.NoBrush)
        painter.drawPolygon(QPolygonF([QPointF(-4, -7), QPointF(4, -7),
                                      QPointF(3, 0), QPointF(5, 2),
                                      QPointF(-5, 2), QPointF(-3, 0)]))
        painter.drawLine(0, 2, 0, 8)
    elif kind == 'send':
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPolygon(QPolygonF([QPointF(3, 3), QPointF(22, 12), QPointF(3, 21),
                                      QPointF(5, 13.5), QPointF(15, 12), QPointF(5, 10.5)]))
    elif kind == 'tag':
        painter.drawLine(9, 3, 6, 21)
        painter.drawLine(17, 3, 14, 21)
        painter.drawLine(3, 9, 21, 9)
        painter.drawLine(2, 15, 20, 15)
    else:
        for index, y in enumerate((5, 12, 19), 1):
            painter.drawLine(9, y, 22, y)
            if kind == 'bullets':
                painter.drawPoint(3, y)
            else:
                font = painter.font()
                font.setPixelSize(7)
                painter.setFont(font)
                painter.drawText(1, y + 2, str(index))
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


class NoteEditor(QPlainTextEdit):
    submit = pyqtSignal()
    popup_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.composing = False

    def inputMethodEvent(self, event):
        self.composing = bool(event.preeditString())
        super().inputMethodEvent(event)

    def createStandardContextMenu(self, *args):
        menu = super().createStandardContextMenu(*args)
        menu.aboutToHide.connect(self.popup_closed.emit)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec_(event.globalPos())
        menu.deleteLater()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.composing:
                super().keyPressEvent(event)
                return
            if not event.modifiers() & Qt.ShiftModifier:
                if not event.isAutoRepeat():
                    self.submit.emit()
                event.accept()
                return
        super().keyPressEvent(event)


class QuickNoteDialog(QDialog):
    SHADOW_MARGIN = 12

    def __init__(self, save_note, parent=None, data_dir=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.save_note = save_note
        self.data_dir = data_dir
        self._drag_offset = None
        self._resize_edges = ''
        self.bottom_effects = {}
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setWindowTitle('快速便签')
        self.resize(460 + 2 * self.SHADOW_MARGIN, 480 + 2 * self.SHADOW_MARGIN)
        self.setMinimumSize(320 + 2 * self.SHADOW_MARGIN, 300 + 2 * self.SHADOW_MARGIN)
        self.setStyleSheet('''
            QDialog { background: transparent; }
            QWidget { font-family: 'Microsoft YaHei UI'; }
            QLabel { color: #999; font-size: 12px; }
            QLabel#noteTitle { color: #242424; font-size: 22px; font-weight: 700; }
            QLabel#noteStatus { color: #b54c43; }
            QPlainTextEdit { background: white; color: #333; border: none;
                padding: 0; font-size: 16px; selection-background-color: #d4eee2;
                selection-color: #222; }
            QPushButton { border: none; border-radius: 5px; background: transparent; }
            QPushButton:hover { background: #f3f3f3; }
            QPushButton:checked { background: transparent; }
            QPushButton#saveNote { background: #57ae83; border-radius: 8px; }
            QPushButton#saveNote:hover { background: #429c70; }
            QPushButton#saveNote:disabled { background: #d0d0d0; }
        ''' + SCROLLBAR_STYLE)
        layout = QVBoxLayout(self)
        margin = self.SHADOW_MARGIN
        layout.setContentsMargins(16 + margin, 16 + margin, 12 + margin, 12 + margin)
        layout.setSpacing(10)
        self.header = QWidget(self)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        title = QLabel('快速便签')
        title.setObjectName('noteTitle')
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.pin_button = self.make_tool('pin', '固定窗口，点击外部时保持展开')
        self.pin_button.setCheckable(True)
        self.pin_button.toggled.connect(self.update_pin)
        header_layout.addWidget(self.pin_button)
        self.close_button = self.make_tool('close', '收起便签')
        self.close_button.clicked.connect(self.reject)
        header_layout.addWidget(self.close_button)
        self.header.installEventFilter(self)
        layout.addWidget(self.header)
        self.editor = NoteEditor(self)
        self.editor.setPlaceholderText('记下此刻的想法…')
        self.editor.document().setDocumentMargin(0)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.submit.connect(self.submit)
        self.editor.popup_closed.connect(lambda: QTimer.singleShot(0, self.dismiss_if_inactive))
        layout.addWidget(self.editor, 1)
        self.status = QLabel('')
        self.status.setObjectName('noteStatus')
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.PlainText)
        self.status.hide()
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.tag_button = self.make_tool('tag', '插入标签')
        self.tag_button.clicked.connect(lambda: self.insert_marker('#'))
        buttons.addWidget(self.tag_button)
        divider = QWidget()
        divider.setFixedSize(1, 20)
        divider.setStyleSheet('background: #ededed;')
        buttons.addWidget(divider)
        self.bullet_button = self.make_tool('bullets', '插入无序列表')
        self.bullet_button.clicked.connect(lambda: self.insert_marker('- ', new_line=True))
        buttons.addWidget(self.bullet_button)
        self.number_button = self.make_tool('numbers', '插入有序列表')
        self.number_button.clicked.connect(lambda: self.insert_marker('1. ', new_line=True))
        buttons.addWidget(self.number_button)
        buttons.addStretch()
        self.save_button = self.make_tool('send', '保存便签', color='white')
        self.save_button.setObjectName('saveNote')
        self.save_button.setFixedSize(56, 34)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.submit)
        self.editor.textChanged.connect(self.update_save_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)
        for button in (self.tag_button, self.bullet_button, self.number_button, self.save_button):
            effect = QGraphicsOpacityEffect(button)
            effect.setOpacity(1.0)
            button.setGraphicsEffect(effect)
            self.bottom_effects[button] = effect
        QApplication.instance().installEventFilter(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = self.SHADOW_MARGIN + 0.5
        body = QRectF(self.rect()).adjusted(margin, margin, -margin, -margin)
        # 在预留的透明边距内叠加柔和阴影，避免被窗口边界裁切。
        painter.setPen(Qt.NoPen)
        for spread in range(10, 0, -1):
            painter.setBrush(QColor(0, 0, 0, 2 if spread > 5 else 3))
            shadow = body.translated(0, 2).adjusted(-spread, -spread, spread, spread)
            painter.drawRoundedRect(shadow, 6 + spread, 6 + spread)
        painter.setPen(QPen(QColor('#d9d9d9'), 1))
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(body, 6, 6)

    def resize_edges_at(self, pos):
        edges = ''
        edge_width = self.SHADOW_MARGIN + 7
        if pos.x() < edge_width:
            edges += 'l'
        elif pos.x() >= self.width() - edge_width:
            edges += 'r'
        if pos.y() < edge_width:
            edges += 't'
        elif pos.y() >= self.height() - edge_width:
            edges += 'b'
        return edges

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_edges = self.resize_edges_at(event.pos())
            if self._resize_edges:
                self._resize_origin = event.globalPos()
                self._resize_geometry = self.geometry()
                self.grabMouse()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_edges:
            delta = event.globalPos() - self._resize_origin
            rect = self._resize_geometry
            x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
            if 'l' in self._resize_edges:
                width = max(self.minimumWidth(), rect.width() - delta.x())
                x = rect.right() + 1 - width
            if 'r' in self._resize_edges:
                width = max(self.minimumWidth(), rect.width() + delta.x())
            if 't' in self._resize_edges:
                height = max(self.minimumHeight(), rect.height() - delta.y())
                y = rect.bottom() + 1 - height
            if 'b' in self._resize_edges:
                height = max(self.minimumHeight(), rect.height() + delta.y())
            self.setGeometry(x, y, width, height)
            event.accept()
            return
        edges = self.resize_edges_at(event.pos())
        cursor = Qt.ArrowCursor
        if edges in ('lt', 'rb'):
            cursor = Qt.SizeFDiagCursor
        elif edges in ('rt', 'lb'):
            cursor = Qt.SizeBDiagCursor
        elif edges in ('l', 'r'):
            cursor = Qt.SizeHorCursor
        elif edges in ('t', 'b'):
            cursor = Qt.SizeVerCursor
        self.setCursor(cursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._resize_edges:
            self._resize_edges = ''
            self.releaseMouse()
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        if self._resize_edges:
            self._resize_edges = ''
            self.releaseMouse()
        self._drag_offset = None
        self.unsetCursor()
        super().hideEvent(event)

    def make_tool(self, kind, label, color='#999999'):
        button = QPushButton(self)
        button.setFixedSize(28, 30)
        button.setIcon(toolbar_icon(kind, color))
        button.setIconSize(QSize(23, 23))
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.setAutoDefault(False)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def update_save_button(self):
        self.save_button.setEnabled(bool(self.editor.toPlainText().strip()))

    def update_pin(self, pinned):
        self.pin_button.setIcon(toolbar_icon('pin', '#57ae83' if pinned else '#999999', filled=pinned))
        self.pin_button.setToolTip('取消固定，点击外部时自动收起' if pinned else '固定窗口，点击外部时保持展开')
        for button, effect in self.bottom_effects.items():
            effect.setOpacity(0.18 if pinned and not button.underMouse() else 1.0)

    def insert_marker(self, marker, new_line=False):
        cursor = self.editor.textCursor()
        if new_line:
            cursor.movePosition(QTextCursor.EndOfBlock)
            if cursor.block().text():
                cursor.insertText('\n')
        cursor.insertText(marker)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate and self.isVisible():
            # 延后一轮检查，窗口内部焦点变化和自有弹出菜单不触发收起。
            QTimer.singleShot(0, self.dismiss_if_inactive)
        return super().event(event)

    def dismiss_if_inactive(self):
        if (self.isVisible() and not self.pin_button.isChecked()
                and not self.isActiveWindow() and QApplication.activePopupWidget() is None):
            self.reject()

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.Enter and isinstance(watched, QWidget)
                and self.isAncestorOf(watched) and not self._resize_edges):
            self.unsetCursor()
        if watched in self.bottom_effects:
            if event.type() == QEvent.Enter:
                self.bottom_effects[watched].setOpacity(1.0)
            elif event.type() == QEvent.Leave:
                self.bottom_effects[watched].setOpacity(0.18 if self.pin_button.isChecked() else 1.0)
        if (event.type() == QEvent.MouseButtonPress and self.isVisible()
                and not self.pin_button.isChecked() and isinstance(watched, QWidget)
                and watched is not self and not self.isAncestorOf(watched)):
            # 同一应用内的点击也要收起，包括右键菜单持有焦点的情况。
            self.reject()
        if watched is self.header:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.MouseMove and self._drag_offset is not None:
                self.move(event.globalPos() - self._drag_offset)
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self._drag_offset = None
        return super().eventFilter(watched, event)

    def submit(self):
        content = self.editor.toPlainText().strip()
        if not content:
            self.status.setText('请输入便签内容。')
            self.status.show()
            self.editor.setFocus()
            return
        self.save_button.setEnabled(False)
        try:
            self.save_note(content)
        except Exception:
            message = '保存失败，内容已保留。请检查数据目录是否可写后重试。'
            if self.data_dir:
                message += '\n数据目录：' + str(self.data_dir)
            self.status.setText(message)
            self.status.show()
            return
        finally:
            self.save_button.setEnabled(True)
        self.editor.clear()
        self.status.clear()
        self.status.hide()
        self.accept()
