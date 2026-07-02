from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTimeEdit, QPushButton,
                             QMessageBox, QFormLayout, QCheckBox,
                             QComboBox, QSpinBox, QStackedWidget, QWidget)
from PyQt5.QtCore import Qt, QTime
from collections import namedtuple

HabitData = namedtuple('HabitData', ['content', 'time_str', 'to_delete',
                                      'to_archive', 'freq_mode', 'weekdays',
                                      'weekly_target', 'interval_days'])


class AddHabitDialog(QDialog):
    MODE_KEYS = ["daily", "weekly", "interval"]
    MODE_LABELS = ["按天", "按周", "按时间间隔"]

    def __init__(self, habit=None, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.delete_result = False
        self.archive_result = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle("编辑习惯" if self.habit else "添加习惯")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(380, 370 if self.habit else 320)

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
            QLineEdit, QTimeEdit, QComboBox, QSpinBox {
                font-size: 11pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus, QTimeEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QPushButton#archiveButton {
                background-color: #F97316;
                color: white;
            }
            QPushButton#archiveButton:hover {
                background-color: #ea580c;
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
        form_layout.addRow("提醒时间:", self.time_edit)

        freq_label = QLabel("频率:")
        freq_label.setStyleSheet("font-size: 12pt; color: #333; font-weight: bold;")
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(self.MODE_LABELS)
        self.freq_combo.currentIndexChanged.connect(self._on_mode_changed)
        form_layout.addRow(freq_label, self.freq_combo)

        self.mode_stack = QStackedWidget()
        self._build_daily_page()
        self._build_weekly_page()
        self._build_interval_page()
        form_layout.addRow(self.mode_stack)

        main_layout.addLayout(form_layout)

        # Bottom button row: [删除] [归档] ... [取消] [确定]
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        if self.habit:
            self.delete_button = QPushButton("删除")
            self.delete_button.setObjectName("deleteButton")
            self.delete_button.clicked.connect(self.delete_habit)
            button_layout.addWidget(self.delete_button)

            self.archive_button = QPushButton("归档")
            self.archive_button.setObjectName("archiveButton")
            self.archive_button.clicked.connect(self.archive_habit)
            button_layout.addWidget(self.archive_button)

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

        if self.habit:
            self._load_existing()
        else:
            self._on_mode_changed(0)

    def _center_layout(self, layout):
        """Wrap a layout with stretches on both sides for centering."""
        wrapper = QHBoxLayout()
        wrapper.addStretch()
        wrapper.addLayout(layout)
        wrapper.addStretch()
        return wrapper

    def _build_daily_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        day_names = ["一", "二", "三", "四", "五", "六", "日"]
        self.weekday_cbs = []
        inner = QHBoxLayout()
        inner.setSpacing(2)
        for i, name in enumerate(day_names):
            cb = QCheckBox(name)
            cb.setChecked(i in [0, 1, 2, 3, 4])
            cb.setMaximumWidth(36)
            cb.setStyleSheet("font-size: 10pt; color: #333; font-weight: normal;")
            self.weekday_cbs.append(cb)
            inner.addWidget(cb)
        outer.addLayout(self._center_layout(inner))
        self.mode_stack.addWidget(page)

    def _build_weekly_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        inner = QHBoxLayout()
        inner.setSpacing(6)
        label = QLabel("每周完成")
        label.setStyleSheet("font-size: 11pt; color: #555; font-weight: normal;")
        self.weekly_spin = QSpinBox()
        self.weekly_spin.setRange(1, 7)
        self.weekly_spin.setValue(3)
        self.weekly_spin.setFixedWidth(50)
        suffix = QLabel("次")
        suffix.setStyleSheet("font-size: 11pt; color: #555; font-weight: normal;")
        inner.addWidget(label)
        inner.addWidget(self.weekly_spin)
        inner.addWidget(suffix)
        outer.addLayout(self._center_layout(inner))
        self.mode_stack.addWidget(page)

    def _build_interval_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        inner = QHBoxLayout()
        inner.setSpacing(6)
        label = QLabel("每")
        label.setStyleSheet("font-size: 11pt; color: #555; font-weight: normal;")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 30)
        self.interval_spin.setValue(2)
        self.interval_spin.setFixedWidth(50)
        suffix = QLabel("天")
        suffix.setStyleSheet("font-size: 11pt; color: #555; font-weight: normal;")
        inner.addWidget(label)
        inner.addWidget(self.interval_spin)
        inner.addWidget(suffix)
        outer.addLayout(self._center_layout(inner))
        self.mode_stack.addWidget(page)

    def _on_mode_changed(self, index):
        self.mode_stack.setCurrentIndex(index)

    def _load_existing(self):
        if self.habit.freq_mode == "daily":
            self.freq_combo.setCurrentIndex(0)
        elif self.habit.freq_mode == "weekly":
            self.freq_combo.setCurrentIndex(1)
        else:
            self.freq_combo.setCurrentIndex(2)
        for i, cb in enumerate(self.weekday_cbs):
            cb.setChecked(i in (self.habit.weekdays or []))
        self.weekly_spin.setValue(self.habit.weekly_target)
        self.interval_spin.setValue(self.habit.interval_days)
        self._on_mode_changed(self.freq_combo.currentIndex())

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

    def archive_habit(self):
        reply = QMessageBox.question(
            self, "确认归档",
            f"确定要归档习惯「{self.habit.content}」吗？\n归档后可在日志中查看历史记录。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.archive_result = True
            self.accept()

    def get_habit_data(self):
        if self.delete_result:
            return HabitData(None, None, True, False, None, None, None, None)
        if self.archive_result:
            return HabitData(None, None, False, True, None, None, None, None)
        if self.result() == QDialog.Accepted:
            content = self.content_edit.text().strip()
            time_str = self.time_edit.time().toString("HH:mm")
            freq_mode = self.MODE_KEYS[self.freq_combo.currentIndex()]
            weekdays = [i for i, cb in enumerate(self.weekday_cbs) if cb.isChecked()]
            weekly_target = self.weekly_spin.value()
            interval_days = self.interval_spin.value()
            return HabitData(content, time_str, False, False, freq_mode, weekdays,
                             weekly_target, interval_days)
        return HabitData(None, None, False, False, None, None, None, None)
