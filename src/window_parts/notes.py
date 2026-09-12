from datetime import datetime
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor
from quick_notes.store import NoteStore
from quick_notes.dialog import QuickNoteDialog
from quick_notes.card import NoteCard
from storage import get_data_dir


class WindowNotesMixin:
    def load_notes(self):
        try:
            if self.note_store is None:
                self.note_store = NoteStore(get_data_dir())
            self.notes = self.note_store.load_notes()
            self.note_load_error = False
        except Exception:
            self.note_load_error = True

    def refresh_notes_display(self):
        if list(self.note_cards) != [note['id'] for note in self.notes]:
            self.note_cards.clear()
        if not self.note_cards:
            self.task_list_widget.clear()
            self.task_widgets.clear()
        if self.note_load_error:
            status = '便签读取失败，切换回便签页可重试。\n存档目录：' + get_data_dir()
        elif not self.notes:
            status = '暂无便签，点＋或按Ctrl＋Alt＋N记一条。'
        else:
            status = ''
        if self.note_store and self.note_store.log_error:
            status += '\n便签已保存，CSV导出失败；下次打开便签列表时重试。'
        self.notes_status.setText(status)
        self.notes_status.setVisible(bool(status))
        for index, note in enumerate(self.notes):
            card = self.note_cards.get(note['id'])
            if card is None:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, note)
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.task_list_widget.insertItem(index, item)
                card = NoteCard(note, self, item)
                self.note_cards[note['id']] = card
                self.task_widgets[note['id']] = card
                self.task_list_widget.setItemWidget(item, card)
            elif not card.is_editing:
                card.note = dict(note)
                card.content_label.setText(note['content'])
                card.item.setData(Qt.UserRole, note)
                card.update_metadata()
            card.sync_size()

    def resize_note_cards(self):
        if self.current_page == 'notes':
            for card in self.note_cards.values():
                card.sync_size()

    def apply_note_state(self, updated):
        self.notes = [note for note in self.notes if note['id'] != updated['id']]
        if not updated.get('archived_at') and not updated.get('deleted_at'):
            self.notes.append(updated)
        self.notes.sort(key=lambda note: (note.get('pinned', False),
                        datetime.fromisoformat(note.get('display_at', note['created_at'])), note['id']), reverse=True)

    def update_inline_note(self, note_id, content):
        updated = self.note_store.update_note(note_id, content)
        self.apply_note_state(updated)
        QTimer.singleShot(0, self.refresh_task_display)
        return updated

    def show_quick_note(self):
        if self.note_dialog is None:
            self.note_dialog = QuickNoteDialog(self.save_quick_note, self, get_data_dir())
        if not self.note_dialog.isVisible():
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            center = screen.availableGeometry().center()
            self.note_dialog.move(center - self.note_dialog.rect().center())
        self.note_dialog.show()
        self.note_dialog.raise_()
        self.note_dialog.activateWindow()
        self.note_dialog.editor.setFocus()

    def save_quick_note(self, content):
        self.load_notes()
        if self.note_load_error:
            raise OSError('便签存档不可读')
        note = self.note_store.create_note(content)
        self.apply_note_state(note)
        # 写入成功后刷新界面，避免显示异常被误认为保存失败而重复提交。
        QTimer.singleShot(0, self.show_saved_notes)

    def show_saved_notes(self):
        self.current_page = 'notes'
        self.refresh_task_display()
        if self.note_toast is None:
            self.note_toast = QLabel('便签已保存', self, Qt.ToolTip | Qt.WindowStaysOnTopHint)
            self.note_toast.setAttribute(Qt.WA_ShowWithoutActivating)
            self.note_toast.setStyleSheet('background: #333; color: white; padding: 12px 20px; border-radius: 5px;')
            self.note_toast_timer = QTimer(self)
            self.note_toast_timer.setSingleShot(True)
            self.note_toast_timer.timeout.connect(self.note_toast.hide)
        self.note_toast.adjustSize()
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        self.note_toast.move(screen.availableGeometry().center() - self.note_toast.rect().center())
        self.note_toast.show()
        self.note_toast_timer.start(1600)
        if self.note_store.log_error:
            QMessageBox.warning(self, '便签已保存', 'CSV文件暂时无法导出。便签已保存在JSONL文件中，重新打开便签列表会重试导出。')

    def show_note_hotkey_warning(self):
        QMessageBox.warning(self, '便签快捷键不可用',
                            'Ctrl＋Alt＋N注册失败，可能已被其他程序占用。可切换到便签页后点＋记录。关闭占用程序并重启本程序可重试。')
