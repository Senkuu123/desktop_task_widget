"""便签菜单、历史、展示日期及已有便签浮窗。"""
from datetime import datetime

from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtWidgets import (QMenu, QWidgetAction, QPushButton, QDialog, QVBoxLayout,
                             QDialogButtonBox, QDateTimeEdit, QListWidget,
                             QPlainTextEdit, QMessageBox, QLabel)
from quick_notes.dialog import QuickNoteDialog


class NoteActions:
    def __init__(self, owner):
        self.owner = owner
        self.popups = {}

    def menu(self, card):
        menu = QMenu(card)
        menu.setStyleSheet('''
            QMenu { background: #303030; color: #ddd; border: 1px solid #555; padding: 5px; }
            QMenu::item { padding: 7px 26px 7px 14px; }
            QMenu::item:selected { background: #484848; }
        ''')
        note_id = card.note['id']
        def add(label, callback, parent=menu):
            action = parent.addAction(label)
            # 菜单关闭后执行，避免刷新列表销毁正在处理事件的卡片。
            action.triggered.connect(lambda: QTimer.singleShot(0, callback))
            return action
        add('编辑', card.begin_edit)
        add('取消置顶' if card.note.get('pinned') else '置顶',
            lambda: self.mutate(note_id, 'pin', not card.note.get('pinned', False)))
        add('弹出浮窗', lambda: self.open_popup(note_id))
        add('归档', lambda: self.mutate(note_id, 'archive'))
        more = menu.addMenu('更多')
        add('显示历史版本', lambda: self.show_history(note_id), more)
        add('修改日期', lambda: self.change_date(note_id), more)
        menu.addSeparator()
        delete = QWidgetAction(menu)
        delete.setText('删除')
        button = QPushButton('删除')
        button.setAccessibleName('删除')
        button.setStyleSheet('QPushButton { color: #ff7777; text-align: left; padding: 7px 14px; border: none; background: transparent; } QPushButton:hover { background: #484848; }')
        button.clicked.connect(lambda: (menu.close(), QTimer.singleShot(0, lambda: self.mutate(note_id, 'delete'))))
        delete.setDefaultWidget(button)
        menu.addAction(delete)
        return menu

    def mutate(self, note_id, action, value=None):
        note = next(n for n in self.owner.notes if n['id'] == note_id)
        if action in ('archive', 'delete') and self.owner.note_drafts.get(note_id, note['content']) != note['content']:
            QMessageBox.information(self.owner, '便签正在编辑', '请先保存或取消修改，再执行此操作。')
            return
        try:
            store = self.owner.note_store
            if action == 'pin':
                updated = store.set_pinned(note_id, value)
            elif action == 'date':
                updated = store.change_date(note_id, value)
            elif action == 'archive':
                updated = store.archive_note(note_id)
            elif action == 'delete':
                updated = store.delete_note(note_id)
            if action in ('archive', 'delete'):
                self.take_inline(note_id)
                self.owner.note_drafts.pop(note_id, None)
            self.owner.apply_note_state(updated)
            self.owner.refresh_task_display()
        except Exception as error:
            QMessageBox.warning(self.owner, '操作失败', f'便签未完成此操作，请重试。\n{error}')

    def take_inline(self, note_id):
        popup = self.popups.pop(note_id, None)
        if popup:
            self.owner.note_drafts[note_id] = popup.editor.toPlainText()
            popup.close()
            popup.deleteLater()

    def open_popup(self, note_id):
        popup = self.popups.get(note_id)
        if popup is None:
            note = next(n for n in self.owner.notes if n['id'] == note_id)
            text = self.owner.note_drafts.get(note_id, note['content'])
            card = self.owner.note_cards.get(note_id)
            if card and card.is_editing:
                card.cancel()
            self.owner.note_drafts[note_id] = text
            popup = QuickNoteDialog(lambda content: self.owner.update_inline_note(note_id, content),
                                    self.owner, self.owner.note_store.data_dir)
            popup.setWindowTitle('编辑便签')
            popup.editor.setPlainText(text)
            popup.editor.textChanged.connect(lambda: self.keep_popup_draft(note_id, popup))
            popup.accepted.connect(lambda: self.finish_popup(note_id, popup))
            self.popups[note_id] = popup
            screen = self.owner.screen()
            popup.move(screen.availableGeometry().center() - popup.rect().center())
        popup.show()
        popup.raise_()
        popup.activateWindow()
        popup.editor.setFocus()

    def keep_popup_draft(self, note_id, popup):
        self.owner.note_drafts[note_id] = popup.editor.toPlainText()

    def finish_popup(self, note_id, popup):
        self.owner.note_drafts.pop(note_id, None)
        self.popups.pop(note_id, None)
        popup.deleteLater()

    def show_history(self, note_id):
        try:
            versions = self.owner.note_store.history(note_id)
        except Exception as error:
            QMessageBox.warning(self.owner, '读取失败', str(error))
            return
        dialog = QDialog(self.owner)
        dialog.setWindowTitle('历史版本')
        dialog.resize(520, 440)
        layout = QVBoxLayout(dialog)
        listing = QListWidget()
        content = QPlainTextEdit()
        content.setReadOnly(True)
        for version in reversed(versions):
            listing.addItem(datetime.fromisoformat(version['occurred_at']).astimezone().strftime('%Y-%m-%d %H:%M:%S'))
        ordered = list(reversed(versions))
        listing.currentRowChanged.connect(lambda row: content.setPlainText(ordered[row]['content']) if row >= 0 else None)
        layout.addWidget(listing, 1)
        layout.addWidget(content, 2)
        if ordered:
            listing.setCurrentRow(0)
        else:
            content.setPlainText('暂无历史版本')
        dialog.exec_()
        dialog.deleteLater()

    def change_date(self, note_id):
        note = next(n for n in self.owner.notes if n['id'] == note_id)
        dialog = QDialog(self.owner)
        dialog.setWindowTitle('修改日期')
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('展示日期和时间'))
        edit = QDateTimeEdit(QDateTime(datetime.fromisoformat(note.get('display_at', note['created_at'])).astimezone().replace(tzinfo=None)))
        edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        edit.setCalendarPopup(True)
        layout.addWidget(edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('保存')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            self.mutate(note_id, 'date', edit.dateTime().toPyDateTime().astimezone().isoformat())
        dialog.deleteLater()

    def close(self):
        for popup in list(self.popups.values()):
            popup.close()
