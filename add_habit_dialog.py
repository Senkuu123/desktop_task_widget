from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTimeEdit, QPushButton,
                             QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt, QTime


class AddHabitDialog(QDialog):
    def __init__(self, habit=None, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.delete_result = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle("编辑习惯" if self.habit else "添加习惯")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(350, 230 if self.habit else 200)

        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QLabel {
                font-size: 12pt;
                color: #333;
                font-weight: bold;
            }
            QLineEdit, QTimeEdit {
                font-size: 11pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus, QTimeEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                font-size: 11pt;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#okButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#okButton:hover {
                background-color: #45a049;
            }
            QPushButton#cancelButton {
                background-color: #9CA3AF;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #6B7280;
            }
            QPushButton#deleteButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton#deleteButton:hover {
                background-color: #da190b;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("例：跑步30分钟、背单词、喝8杯水...")
        self.content_edit.setMinimumHeight(35)
        if self.habit:
            self.content_edit.setText(self.habit.content)
        form_layout.addRow("习惯内容:", self.content_edit)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setMinimumHeight(35)
        if self.habit:
            h, m = self.habit.time.split(":")
            self.time_edit.setTime(QTime(int(h), int(m)))
        else:
            self.time_edit.setTime(QTime(8, 0))
        form_layout.addRow("每日时间:", self.time_edit)

        main_layout.addLayout(form_layout)

        # 编辑模式下显示删除按钮
        if self.habit:
            delete_layout = QHBoxLayout()
            self.delete_button = QPushButton("删除此习惯")
            self.delete_button.setObjectName("deleteButton")
            self.delete_button.clicked.connect(self.delete_habit)
            delete_layout.addWidget(self.delete_button)
            delete_layout.addStretch()
            main_layout.addLayout(delete_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        self.ok_button = QPushButton("确定")
        self.ok_button.setObjectName("okButton")
        self.ok_button.clicked.connect(self.accept_habit)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.content_edit.setFocus()

    def accept_habit(self):
        content = self.content_edit.text().strip()
        if not content:
            QMessageBox.warning(self, "输入错误", "请输入习惯内容！")
            self.content_edit.setFocus()
            return
        self.accept()

    def delete_habit(self):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除习惯「{self.habit.content}」吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_result = True
            self.accept()

    def get_habit_data(self):
        if self.delete_result:
            return None, None, True
        if self.result() == QDialog.Accepted:
            content = self.content_edit.text().strip()
            time_str = self.time_edit.time().toString("HH:mm")
            return content, time_str, False
        return None, None, False
