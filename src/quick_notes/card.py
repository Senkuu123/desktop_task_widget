"""便签卡片：列表内编辑，草稿由主窗口保留。"""

from datetime import datetime
from PyQt5.QtCore import Qt, QEvent, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from quick_notes.dialog import NoteEditor, toolbar_icon


class InlineEditor(NoteEditor):
    cancel = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and not self.composing:
            self.cancel.emit()
            return
        super().keyPressEvent(event)


class NoteCard(QWidget):
    def __init__(self, note, owner, item):
        super().__init__()
        self.note = dict(note)
        self.owner = owner
        self.item = item
        self.is_editing = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 8)
        self.surface = QFrame()
        self.surface.setObjectName('noteCard')
        outer.addWidget(self.surface)
        layout = QVBoxLayout(self.surface)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.meta = QWidget()
        meta_row = QHBoxLayout(self.meta)
        meta_row.setContentsMargins(0, 0, 0, 0)
        self.time_label = QLabel()
        meta_row.addWidget(self.time_label)
        meta_row.addStretch()
        self.menu_button = QPushButton('···')
        self.menu_button.setFixedSize(28, 24)
        self.menu_button.setToolTip('便签操作')
        self.menu_button.setAccessibleName('便签操作')
        self.menu_button.clicked.connect(self.show_menu)
        meta_row.addWidget(self.menu_button)
        layout.addWidget(self.meta)
        self.update_metadata()
        self.content_label = QLabel(note['content'])
        self.content_label.setTextFormat(Qt.PlainText)
        self.content_label.setWordWrap(True)
        self.content_label.setCursor(Qt.IBeamCursor)
        layout.addWidget(self.content_label)
        self.editor = InlineEditor()
        self.editor.setFixedHeight(156)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.submit.connect(self.save)
        self.editor.cancel.connect(self.cancel)
        self.editor.textChanged.connect(self.keep_draft)
        layout.addWidget(self.editor)
        self.error = QLabel()
        self.error.setTextFormat(Qt.PlainText)
        self.error.setWordWrap(True)
        self.error.setStyleSheet('color: #ffb3aa; background: transparent; font-size: 10pt;')
        self.error.hide()
        layout.addWidget(self.error)
        self.toolbar = QWidget()
        row = QHBoxLayout(self.toolbar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        for kind, marker, tip in [('tag', '#', '插入标签'), ('bullets', '- ', '插入无序列表'), ('numbers', '1. ', '插入有序列表')]:
            button = QPushButton()
            button.setIcon(toolbar_icon(kind, '#aaa'))
            button.setFixedSize(24, 28)
            button.setToolTip(tip)
            button.setAccessibleName(tip)
            button.clicked.connect(lambda checked=False, text=marker: self.insert_marker(text))
            row.addWidget(button)
        row.addStretch()
        self.count = QLabel()
        self.count.setStyleSheet('color: #999; background: transparent; font-size: 9pt;')
        row.addWidget(self.count)
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.cancel)
        row.addWidget(self.cancel_button)
        self.save_button = QPushButton()
        self.save_button.setObjectName('saveCard')
        self.save_button.setIcon(toolbar_icon('send', 'white'))
        self.save_button.setFixedSize(38, 28)
        self.save_button.setToolTip('保存修改')
        self.save_button.setAccessibleName('保存修改')
        self.save_button.clicked.connect(self.save)
        row.addWidget(self.save_button)
        layout.addWidget(self.toolbar)
        for widget in (self.surface, self.time_label, self.content_label):
            widget.installEventFilter(self)
        self.editor.hide()
        self.toolbar.hide()
        self.update_text_style()
        if note['id'] in owner.note_drafts and note['id'] not in owner.note_actions.popups:
            self.begin_edit(focus=False)

    def update_metadata(self):
        displayed = datetime.fromisoformat(self.note.get('display_at', self.note['created_at'])).astimezone()
        self.time_label.setText(('置顶 · ' if self.note.get('pinned') else '') + displayed.strftime('%Y-%m-%d %H:%M'))

    def show_menu(self):
        menu = self.owner.note_actions.menu(self)
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        menu.deleteLater()

    def update_text_style(self):
        alpha = int(255 * self.owner.current_font_opacity / 100)
        font_size = self.owner.current_font_size
        self.time_label.setStyleSheet(f'color: #999; background: transparent; font-size: {max(8, font_size - 2)}pt;')
        self.content_label.setStyleSheet(f'color: rgba(255,255,255,{alpha}); background: transparent; font-size: {font_size}pt;')
        border = '#60bb89' if self.is_editing else 'rgba(255,255,255,22)'
        self.surface.setStyleSheet(f'''
            QWidget {{ font-family: 'Microsoft YaHei UI'; }}
            QFrame#noteCard {{ background: rgba(255,255,255,9); border: 1px solid {border}; border-radius: 7px; }}
            QPlainTextEdit {{ background: transparent; color: rgba(255,255,255,{alpha});
                border: none; font-family: 'Microsoft YaHei UI'; font-size: {font_size}pt;
                selection-background-color: #387a59; }}
            QPushButton {{ color: #bbb; background: transparent; border: none; padding: 3px; border-radius: 4px; }}
            QPushButton:hover {{ background: rgba(255,255,255,18); }}
            QPushButton#saveCard {{ background: #57ae83; }}
            QPushButton#saveCard:disabled {{ background: #555; }}
        ''')
        self.sync_size()

    def sync_size(self):
        # 始终预留4像素滚动条和4像素间隔，避免滚动条显隐改变卡片宽度。
        width = max(100, self.owner.task_list_widget.contentsRect().width() - 8)
        self.setFixedWidth(width)
        self.content_label.setFixedHeight(max(24, self.content_label.heightForWidth(max(60, width - 26))))
        self.surface.layout().activate()
        self.layout().activate()
        self.item.setSizeHint(QSize(width, self.layout().totalSizeHint().height()))

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
            self.begin_edit()
            return True
        return super().eventFilter(watched, event)

    def begin_edit(self, focus=True):
        self.owner.note_actions.take_inline(self.note['id'])
        if not self.is_editing:
            self.is_editing = True
            self.editor.setPlainText(self.owner.note_drafts.get(self.note['id'], self.note['content']))
            self.meta.hide()
            self.content_label.hide()
            self.editor.show()
            self.toolbar.show()
            self.keep_draft()
            self.update_text_style()
        if focus:
            self.editor.setFocus()
            self.owner.task_list_widget.doItemsLayout()
            self.owner.task_list_widget.scrollToItem(self.item)

    def keep_draft(self):
        if self.is_editing:
            text = self.editor.toPlainText()
            self.owner.note_drafts[self.note['id']] = text
            self.count.setText(str(len(text)))
            self.save_button.setEnabled(bool(text.strip()))

    def insert_marker(self, marker):
        self.editor.insertPlainText(marker)
        self.editor.setFocus()

    def save(self):
        content = self.editor.toPlainText().strip()
        if not content:
            self.error.setText('请输入便签内容。')
            self.error.show()
            self.sync_size()
            return
        self.save_button.setEnabled(False)
        try:
            updated = self.owner.update_inline_note(self.note['id'], content)
        except Exception:
            self.error.setText('保存失败，修改内容已保留，请重试。')
            self.error.show()
            self.save_button.setEnabled(True)
            self.sync_size()
            return
        self.note = updated
        self.item.setData(Qt.UserRole, updated)
        self.cancel()

    def cancel(self):
        self.owner.note_drafts.pop(self.note['id'], None)
        self.is_editing = False
        self.editor.hide()
        self.toolbar.hide()
        self.error.hide()
        self.update_metadata()
        self.meta.show()
        self.content_label.setText(self.note['content'])
        self.content_label.show()
        self.update_text_style()
