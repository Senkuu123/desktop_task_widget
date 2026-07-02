import sys
import ctypes
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QListWidgetItem, QPushButton, QCheckBox,
                             QLabel, QDialog, QSlider, QGroupBox, QSizePolicy, QMessageBox,
                             QSpinBox, QTimeEdit, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QPoint, QTime, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QCursor, QIcon
from task import Task
from habit import Habit
from storage import (save_tasks_to_json, load_tasks_from_json, archive_task,
                     save_settings, load_settings, save_habits_to_json, load_habits_from_json,
                     save_water_reminder, load_water_reminder,
                     save_water_log, load_water_log,
                     save_habit_log, load_habit_log)
from add_task_dialog import AddTaskDialog
from edit_task_dialog import EditTaskDialog
from add_habit_dialog import AddHabitDialog
from water_reminder import WaterReminder
from autostart_manager import AutoStartManager, check_startup_permission


class WaterProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self.setFixedHeight(6)

    def set_progress(self, value):
        self._progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.setBrush(QColor(60, 60, 60))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)
        fill_w = int(w * self._progress)
        if fill_w > 0:
            painter.setBrush(QColor(59, 130, 246))
            painter.drawRoundedRect(0, 0, fill_w, h, 3, 3)
        painter.end()


class WaterDisplayWidget(QWidget):
    def __init__(self, water_reminder, parent_window, parent=None):
        super().__init__(parent)
        self.water = water_reminder
        self.parent_window = parent_window
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.update_countdown)
        self._refresh_timer.start(30000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # Title row
        top = QHBoxLayout()
        top.setSpacing(6)
        title = QLabel("今日饮水进度")
        title.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 10pt; font-weight: 600;")
        top.addWidget(title)
        top.addStretch()
        self.log_toggle_btn = QPushButton("▼")
        self.log_toggle_btn.setFixedSize(20, 20)
        self.log_toggle_btn.setToolTip("今日记录")
        self.log_toggle_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: rgba(255,255,255,0.5); font-size: 8pt; }
            QPushButton:hover { color: rgba(255,255,255,0.9); }
        """)
        self.log_toggle_btn.clicked.connect(self._toggle_log)
        top.addWidget(self.log_toggle_btn)
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(20, 20)
        settings_btn.setToolTip("饮水设置")
        settings_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: rgba(255,255,255,0.5); font-size: 9pt; }
            QPushButton:hover { color: rgba(255,255,255,0.9); }
        """)
        settings_btn.clicked.connect(self.show_settings)
        top.addWidget(settings_btn)
        root.addLayout(top)

        # Intake display
        self.intake_label = QLabel()
        self.intake_label.setTextFormat(Qt.RichText)
        self.intake_label.setStyleSheet("background: transparent;")
        self.intake_label.setContentsMargins(-4, 0, 0, 0)
        root.addWidget(self.intake_label)

        # Progress bar
        self.progress_bar = WaterProgressBar()
        root.addWidget(self.progress_bar)

        # Progress stats
        self.progress_stats = QLabel()
        self.progress_stats.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 9pt;")
        root.addWidget(self.progress_stats)

        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08);")
        root.addWidget(sep)

        # Countdown
        mid = QHBoxLayout()
        mid.setContentsMargins(0, 2, 0, 2)
        mid.setSpacing(8)
        self.reminder_time_label = QLabel("--:--")
        self.reminder_time_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 16pt; font-weight: 700;")
        self.reminder_time_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        mid.addWidget(self.reminder_time_label)
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 9pt;")
        self.countdown_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        mid.addWidget(self.countdown_label)
        mid.addStretch()
        root.addLayout(mid)

        # Buttons
        self._btn_row_widget = QWidget()
        btn_row = QHBoxLayout(self._btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)

        btn_style = """
            QPushButton {
                background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.85);
                border: none; border-radius: 6px; font-size: 10pt; padding: 6px 0;
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
            QPushButton:pressed { background: rgba(255,255,255,0.25); }
        """

        def make_btn(icon, line1, line2, callback):
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.setMinimumHeight(44)
            lbl = QLabel(f"{icon} {line1}\n{line2}" if icon else f"{line1}\n{line2}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.85); font-size: 10pt;")
            layout = QVBoxLayout(btn)
            layout.setContentsMargins(0, 4, 0, 4)
            layout.addWidget(lbl)
            btn.clicked.connect(callback)
            btn_row.addWidget(btn)
            return btn, lbl

        self._drink_full_btn, self._drink_full_lbl = make_btn(
            "🥛", "喝一杯", f"+{self.water.cup_size}ml", self.drink_full)
        self._drink_half_btn, self._drink_half_lbl = make_btn(
            "", "喝半杯", f"+{self.water.cup_size // 2}ml", self.drink_half)
        self._snooze_btn, self._snooze_lbl = make_btn(
            "⏰", "稍后提醒", f"{self.water.snooze_interval}分钟后", self.snooze)

        root.addWidget(self._btn_row_widget)

        # Log panel (collapsible, inserted into layout after buttons)
        self.log_container = QWidget()
        self.log_container.setVisible(False)
        log_inner = QVBoxLayout(self.log_container)
        log_inner.setContentsMargins(0, 0, 0, 0)
        log_inner.setSpacing(0)
        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_scroll.setFixedHeight(96)
        self.log_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; border-radius: 6px; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 0; border-radius: 4px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0); border-radius: 4px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: rgba(120, 120, 120, 220); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        self.log_entries_widget = QWidget()
        self.log_entries_layout = QVBoxLayout(self.log_entries_widget)
        self.log_entries_layout.setContentsMargins(8, 6, 8, 6)
        self.log_entries_layout.setSpacing(0)
        self.log_scroll.setWidget(self.log_entries_widget)
        log_inner.addWidget(self.log_scroll)
        root.addWidget(self.log_container)

        self._update_all()

    def _update_all(self):
        self._update_intake()
        self.update_countdown()

    def _update_intake(self):
        self.intake_label.setText(
            f'<span style="color:#3B82F6; font-size:18pt; font-weight:700;">💧{self.water.today_intake}</span>'
            f'<span style="color:rgba(255,255,255,0.35); font-size:11pt;">/{self.water.daily_goal}ml</span>'
        )
        pct = self.water.today_intake / self.water.daily_goal if self.water.daily_goal > 0 else 0
        self.progress_bar.set_progress(min(pct, 1.0))
        pct_int = int(pct * 100)
        remaining = max(0, self.water.daily_goal - self.water.today_intake)
        if self.water.today_intake >= self.water.daily_goal:
            self.progress_stats.setText("今日目标已达成！")
        else:
            self.progress_stats.setText(f"达成 {pct_int}% · 还差 {remaining}ml即可达成今日目标")

    def _update_btn_labels(self):
        self._drink_full_lbl.setText(f"🥛 喝一杯\n+{self.water.cup_size}ml")
        self._drink_half_lbl.setText(f"喝半杯\n+{self.water.cup_size // 2}ml")
        self._snooze_lbl.setText(f"⏰ 稍后提醒\n{self.water.snooze_interval}分钟后")

    def update_countdown(self):
        reset_result = self.water.check_daily_reset()
        if reset_result:
            old_date, old_intake, old_logs, old_completed = reset_result
            log = load_water_log()
            log[old_date] = {
                "total_intake": old_intake,
                "drink_count": len(old_logs),
                "logs": old_logs,
                "goal_completed": old_completed,
            }
            save_water_log(log)
        time_str, sub_text = self.water.get_next_reminder_display()
        self.reminder_time_label.setText(time_str)
        if (self.water.next_reminder_time and self.water.is_enabled
                and not self.water.is_completed_today
                and self.water._is_active_hours() and not self.water._is_quiet_hours()):
            diff = (self.water.next_reminder_time - datetime.now()).total_seconds()
            if diff > 0:
                mins = int(diff // 60)
                self.countdown_label.setText(f"还剩 {mins}分钟")
            else:
                self.countdown_label.setText("")
        else:
            self.countdown_label.setText(sub_text)
        self._update_intake()

    def drink_full(self):
        ml = self.water.cup_size
        self.water.add_water(ml)
        self.water.add_water_log(ml, "喝一杯")
        self._on_drink()

    def drink_half(self):
        ml = self.water.cup_size // 2
        self.water.add_water(ml)
        self.water.add_water_log(ml, "喝半杯")
        self._on_drink()

    def _on_drink(self):
        self._update_all()
        self._rebuild_log()
        self._sync_water_log()
        save_water_reminder(self.water)
        if self.water.is_completed_today:
            self.parent_window.show_deadline_notification(
                "今日饮水目标", 0,
                msg_override=f"真棒！今日已喝够{self.water.daily_goal}ml！")

    def _sync_water_log(self):
        """将当前饮水状态写入water_log.json按天分区"""
        log = load_water_log()
        today = date.today().isoformat()
        log[today] = {
            "total_intake": self.water.today_intake,
            "drink_count": len(self.water.today_logs),
            "logs": list(self.water.today_logs),
            "goal_completed": self.water.is_completed_today,
        }
        save_water_log(log)

    def snooze(self):
        self.water.snooze(30)
        self._update_all()
        save_water_reminder(self.water)

    def show_settings(self):
        dlg = _WaterSettingsDialog(self.water, self.parent_window)
        accepted = dlg.exec_() == QDialog.Accepted
        if accepted:
            self.water.is_enabled = dlg.get_is_enabled()
            self.water.cup_size = dlg.get_cup_size()
            self.water.reminder_interval = dlg.get_interval()
            self.water.snooze_interval = dlg.get_snooze_interval()
            self.water.active_start, self.water.active_end = dlg.get_active_range()
            self.water.quiet_start, self.water.quiet_end = dlg.get_quiet_range()
            self.water.daily_goal = dlg.get_goal()
            self.water.next_reminder_time = None
        if accepted or dlg._reset_done:
            self._update_all()
            self._update_btn_labels()
            if self.log_container.isVisible():
                self._rebuild_log()
            save_water_reminder(self.water)

    def _toggle_log(self):
        visible = not self.log_container.isVisible()
        self.log_container.setVisible(visible)
        self.log_toggle_btn.setText("▲" if visible else "▼")
        if visible:
            self._rebuild_log()

    def _rebuild_log(self):
        layout = self.log_entries_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        logs = self.water.today_logs
        if not logs:
            lbl = QLabel("暂无记录")
            lbl.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 9pt; padding: 8px 0;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
        else:
            for entry in reversed(logs):
                row = QHBoxLayout()
                row.setContentsMargins(0, 5, 0, 5)
                row.setSpacing(0)
                dot = QLabel("·")
                dot.setFixedWidth(8)
                dot.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10pt;")
                row.addWidget(dot)
                time_lbl = QLabel(entry["time"])
                time_lbl.setFixedWidth(38)
                time_lbl.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 9pt;")
                row.addWidget(time_lbl)
                type_lbl = QLabel(entry["type"])
                type_lbl.setFixedWidth(40)
                type_lbl.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 9pt;")
                row.addWidget(type_lbl)
                amt_lbl = QLabel(f"{entry['amount']}ml")
                amt_lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 9pt;")
                row.addWidget(amt_lbl)
                row.addStretch()
                container = QWidget()
                container.setLayout(row)
                layout.addWidget(container)
                sep = QLabel()
                sep.setFixedHeight(1)
                sep.setStyleSheet("background: rgba(255,255,255,0.08);")
                layout.addWidget(sep)


class _WaterSettingsDialog(QDialog):
    def __init__(self, water, parent=None):
        super().__init__(parent)
        self.water = water
        self._reset_done = False
        self.setWindowTitle("饮水设置")
        self.setWindowModality(Qt.ApplicationModal)

        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        def _labeled(label_text, widget):
            w = QWidget()
            row = QHBoxLayout(w)
            row.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(70)
            row.addWidget(lbl)
            row.addWidget(widget)
            return w

        def _range_widget(start_w, end_w):
            w = QWidget()
            r = QHBoxLayout(w)
            r.setContentsMargins(0, 0, 0, 0)
            r.addWidget(start_w)
            sep = QLabel("至")
            sep.setStyleSheet("color: #666;")
            r.addWidget(sep)
            r.addWidget(end_w)
            return w

        # 饮水设置组
        drink_group = QGroupBox("饮水设置")
        dg_layout = QVBoxLayout()

        self.enable_cb = QCheckBox("启用饮水提醒")
        self.enable_cb.setChecked(water.is_enabled)
        dg_layout.addWidget(self.enable_cb)

        self.cup_spin = QSpinBox()
        self.cup_spin.setRange(50, 2000)
        self.cup_spin.setValue(water.cup_size)
        self.cup_spin.setSuffix(" ml")
        self.cup_spin.setMinimumHeight(30)
        dg_layout.addWidget(_labeled("一杯容量", self.cup_spin))

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 300)
        self.interval_spin.setValue(water.reminder_interval)
        self.interval_spin.setSuffix(" 分钟")
        self.interval_spin.setMinimumHeight(30)
        dg_layout.addWidget(_labeled("提醒间隔", self.interval_spin))

        self.snooze_spin = QSpinBox()
        self.snooze_spin.setRange(5, 120)
        self.snooze_spin.setValue(water.snooze_interval)
        self.snooze_spin.setSuffix(" 分钟")
        self.snooze_spin.setMinimumHeight(30)
        dg_layout.addWidget(_labeled("稍后提醒", self.snooze_spin))

        drink_group.setLayout(dg_layout)
        layout.addWidget(drink_group)

        # 时段设置组
        time_group = QGroupBox("时段设置")
        tg_layout = QVBoxLayout()

        self.active_start = QTimeEdit()
        self.active_start.setDisplayFormat("HH:mm")
        h, m = water.active_start.split(":")
        self.active_start.setTime(QTime(int(h), int(m)))
        self.active_start.setMinimumHeight(30)
        self.active_end = QTimeEdit()
        self.active_end.setDisplayFormat("HH:mm")
        h, m = water.active_end.split(":")
        self.active_end.setTime(QTime(int(h), int(m)))
        self.active_end.setMinimumHeight(30)
        tg_layout.addWidget(_labeled("开启时段", _range_widget(self.active_start, self.active_end)))

        self.quiet_start = QTimeEdit()
        self.quiet_start.setDisplayFormat("HH:mm")
        h, m = water.quiet_start.split(":")
        self.quiet_start.setTime(QTime(int(h), int(m)))
        self.quiet_start.setMinimumHeight(30)
        self.quiet_end = QTimeEdit()
        self.quiet_end.setDisplayFormat("HH:mm")
        h, m = water.quiet_end.split(":")
        self.quiet_end.setTime(QTime(int(h), int(m)))
        self.quiet_end.setMinimumHeight(30)
        tg_layout.addWidget(_labeled("静音时段", _range_widget(self.quiet_start, self.quiet_end)))

        time_group.setLayout(tg_layout)
        layout.addWidget(time_group)

        # 每日目标组
        goal_group = QGroupBox("每日目标")
        gg_layout = QVBoxLayout()
        self.goal_spin = QSpinBox()
        self.goal_spin.setRange(500, 10000)
        self.goal_spin.setValue(water.daily_goal)
        self.goal_spin.setSuffix(" ml")
        self.goal_spin.setMinimumHeight(30)
        gg_layout.addWidget(self.goal_spin)
        goal_group.setLayout(gg_layout)
        layout.addWidget(goal_group)

        layout.addStretch()

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("重置今日")
        reset_btn.setFixedHeight(32)
        reset_btn.clicked.connect(self._do_reset)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("确定")
        ok.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.setMinimumSize(340, 440)

    def _do_reset(self):
        self.water.today_intake = 0
        self.water.today_logs = []
        self.water.is_completed_today = False
        self.water.next_reminder_time = None
        self._reset_done = True

    def get_cup_size(self):
        return self.cup_spin.value()

    def get_interval(self):
        return self.interval_spin.value()

    def get_snooze_interval(self):
        return self.snooze_spin.value()

    def get_active_range(self):
        return self.active_start.time().toString("HH:mm"), self.active_end.time().toString("HH:mm")

    def get_quiet_range(self):
        return self.quiet_start.time().toString("HH:mm"), self.quiet_end.time().toString("HH:mm")

    def get_goal(self):
        return self.goal_spin.value()

    def get_is_enabled(self):
        return self.enable_cb.isChecked()


class TaskListWidgetItem(QWidget):
    """自定义任务列表项，支持任务和习惯两种模式"""

    task_status_changed = pyqtSignal(int, bool)  # task_id, is_done
    habit_status_changed = pyqtSignal(int, bool, object)  # habit_id, is_done_today, popup_msg

    def __init__(self, item, parent=None, mode='task'):
        super().__init__(parent)
        self.mode = mode
        if mode == 'habit':
            self.habit = item
            self.task = None
        else:
            self.task = item
            self.habit = None
        self.hovered = False
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # 统一边距
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignLeft)  # 确保左对齐
        
        # 复选框容器（固定位置）
        checkbox_container = QWidget()
        checkbox_container.setFixedWidth(25)  # 固定复选框容器的宽度
        checkbox_container.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(0)
        checkbox_layout.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        self.checkbox = QCheckBox()
        if self.mode == 'habit':
            self.checkbox.setChecked(self.habit.is_done_today)
        else:
            self.checkbox.setChecked(self.task.is_done)
        self.checkbox.setFixedSize(25, 25)  # 固定复选框大小
        self.checkbox.setStyleSheet("""
            QCheckBox {
                background: transparent;
                spacing: 0px;
                border: none;
                outline: none;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: none;
                background-color: white;
            }
           QCheckBox::indicator:hover {
                /* 悬停时只改变圆形指示器，不显示方形背景 */
                background-color: #e0e0e0;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: none;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #45a049;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: none;
            }
            /* 移除复选框的焦点框 */
            QCheckBox:focus {
                outline: none;
                border: none;
            }
            QCheckBox:focus::indicator {
                border: none;
            }
        """)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        
        checkbox_layout.addWidget(self.checkbox)
        
        # 任务内容标签
        self.label = QLabel()
        self.label.setWordWrap(False)  # 取消自动换行
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        
        # 设置标签的尺寸策略，允许水平扩展以支持滚动
        self.label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        # 移除文本选择功能，让双击事件能传递到父组件
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)
        
        layout.addWidget(checkbox_container)
        layout.addWidget(self.label, 1)
        
        self.update_text_style()
        self.setMouseTracking(True)
        
        # 初始化任务项背景色
        self._update_task_background()
        
    def update_text_style(self):
        """更新文本内容和样式"""
        if self.mode == 'habit':
            self._update_habit_text_style()
            return

        # 简化日期显示逻辑
        deadline_display = self._format_deadline()
        
        # 构建显示文本
        if self.task.is_overdue() and not self.task.is_done:
            text = f"⚠️ {self.task.content} ({deadline_display})"
        else:
            text = f"{self.task.content} ({deadline_display})"
        
        # 简化样式逻辑
        if self.task.is_done:
            text_style = "color: #9CA3AF; text-decoration: line-through;"
        elif self.is_task_urgent():
            text_style = "color: #DC2626;"
        else:
            priority_colors = {
                0: "#DC2626",  # P0 红色
                1: "#F97316",  # P1 橙色
                2: "#60A5FA",  # P2 浅蓝色
                3: "white"     # P3 白色
            }
            color = priority_colors.get(self.task.priority, "white")
            text_style = f"color: {color};"
        
        # 获取字体设置
        parent = self._get_parent_window()
        font_size = getattr(parent, 'current_font_size', 11)
        font_opacity = getattr(parent, 'current_font_opacity', 100)
        font_alpha = int(font_opacity * 255 / 100)  # 修复透明度计算
        
        # 应用样式，添加透明度
        if self.task.is_done:
            # 已完成任务使用固定透明度
            text_style = f"font-size: {font_size}pt; {text_style} font-family: 'Microsoft YaHei', sans-serif;"
        else:
            # 未完成任务使用动态透明度
            text_style = f"font-size: {font_size}pt; {text_style} font-family: 'Microsoft YaHei', sans-serif;"
        
        # 为文本颜色添加透明度
        if 'color:' in text_style:
            # 简化处理：直接使用rgba格式
            if 'white' in text_style:
                text_style = text_style.replace('color: white;', f'color: rgba(255, 255, 255, {font_alpha/255});')
            elif 'color: #DC2626' in text_style:
                text_style = text_style.replace('color: #DC2626;', f'color: rgba(220, 38, 38, {font_alpha/255});')
            elif 'color: #F97316' in text_style:
                text_style = text_style.replace('color: #F97316;', f'color: rgba(249, 115, 22, {font_alpha/255});')
            elif 'color: #60A5FA' in text_style:
                text_style = text_style.replace('color: #60A5FA;', f'color: rgba(96, 165, 250, {font_alpha/255});')
            elif 'color: #9CA3AF' in text_style:
                text_style = text_style.replace('color: #9CA3AF;', f'color: rgba(156, 163, 175, {font_alpha/255});')
        
        self.label.setStyleSheet(text_style)
        self.label.setText(text)

    def _update_habit_text_style(self):
        """习惯模式的文字样式"""
        text = f"{self.habit.content} ({self.habit.time} {self.habit.get_freq_label()})"

        parent = self._get_parent_window()
        font_size = getattr(parent, 'current_font_size', 11)
        font_opacity = getattr(parent, 'current_font_opacity', 100)
        font_alpha = int(font_opacity * 255 / 100)

        if self.habit.is_done_today:
            color = f"rgba(156, 163, 175, {font_alpha/255})"
            decoration = "text-decoration: line-through;"
        else:
            color = f"rgba(96, 165, 250, {font_alpha/255})"
            decoration = ""

        style = f"font-size: {font_size}pt; color: {color}; {decoration} font-family: 'Microsoft YaHei', sans-serif;"
        self.label.setStyleSheet(style)
        self.label.setText(text)
        
    def _format_deadline(self):
        """格式化截止时间显示"""
        try:
            parts = self.task.deadline.split('-')
            if len(parts) >= 2:
                month_day = parts[1] + '-' + parts[2].split()[0] if len(parts) > 2 else parts[1]
                if ' ' in self.task.deadline:
                    time_part = self.task.deadline.split(' ')[1]
                    return f"{month_day} {time_part}"
                return month_day
            return self.task.deadline
        except:
            return self.task.deadline
    
    def _get_parent_window(self):
        """获取父窗口"""
        parent = self.parent()
        while parent and not isinstance(parent, TransparentTaskWindow):
            parent = parent.parent()
        return parent
        
    def on_checkbox_changed(self, state):
        """复选框状态改变处理"""
        is_done = (state == Qt.Checked)

        if self.mode == 'habit':
            popup_msg = None
            if is_done:
                popup_msg = self.habit.record_completion()
            else:
                self.habit.undo_completion()
            self.update_text_style()
            self.habit_status_changed.emit(self.habit.id, is_done, popup_msg)
            return

        # 如果是从未完成变为完成，记录完成时间
        if not self.task.is_done and is_done and self.task.completed_at is None:
            self.task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.task.is_done = is_done
        self.update_text_style()
        self.task_status_changed.emit(self.task.id, is_done)
        
    def is_task_urgent(self):
        """检查任务是否紧急（1小时内到期）"""
        if self.mode == 'habit' or self.task.is_done:
            return False
        try:
            deadline_time = self.task.get_deadline_datetime()
            time_diff = (deadline_time - datetime.now()).total_seconds()
            return 0 < time_diff <= 3600
        except:
            return False
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'label'):
            self.label.setMinimumWidth(120)
            self.label.setMaximumWidth(16777215)
            self.updateGeometry()
            self.label.adjustSize()
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        # 只悬停整个项目，不特别处理复选框
        self.hovered = True
        self._update_hover_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hovered = False
        self._update_hover_style()
        super().leaveEvent(event)
    
    def sizeHint(self):
        """返回任务项的推荐尺寸"""
        # 动态计算高度，自适应字体大小
        parent = self._get_parent_window()
        font_size = getattr(parent, 'current_font_size', 11)
        
        # 单行文字的高度计算：字体大小 + 上下内边距
        # 字体实际渲染高度通常比字体大小大4-6像素
        font_render_height = font_size + 5
        item_height = font_render_height + 20  # 单行文字 + 上下内边距
        
        # 确保最小高度足够显示单行文字
        min_height = max(40, item_height)
        
        size = super().sizeHint()
        size.setHeight(min_height)
        return size
    
    def minimumSizeHint(self):
        """返回最小尺寸"""
        return self.sizeHint()
    
    def _update_task_background(self):
        """更新任务项背景色"""
        # 将任务项背景设为透明，让窗口背景直接显示
        current_style = self.label.styleSheet()
        # 移除已有的背景色设置
        import re
        current_style = re.sub(r'background-color:.*?;', '', current_style)
        current_style = re.sub(r'border-radius:.*?;', '', current_style)
        
        # 设置透明背景
        self.label.setStyleSheet(f"""
            {current_style}
            background-color: transparent;
            border-radius: 3px;
        """)
    
    def _update_hover_style(self):
        """更新悬停样式"""
        parent = self._get_parent_window()
        bg_alpha = int(getattr(parent, 'window_background_opacity', 0.8) * 255)
        
        if self.hovered:
            # 悬停时设置悬停背景
            self.label.setStyleSheet(f"""
                {self.label.styleSheet()}
                background-color: rgba(70, 70, 70, {int(bg_alpha * 0.3)});
                border-radius: 3px;
            """)
        else:
            # 常态下恢复透明背景
            current_style = self.label.styleSheet()
            import re
            current_style = re.sub(r'background-color:.*?;', '', current_style)
            current_style = re.sub(r'border-radius:.*?;', '', current_style)
            self.label.setStyleSheet(f"""
                {current_style}
                background-color: transparent;
                border-radius: 3px;
            """)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.autostart_manager = AutoStartManager()
        self.initUI()
        
    def initUI(self):
        """初始化设置界面"""
        self.setWindowTitle("设置")
        self.setWindowModality(Qt.ApplicationModal)
        # self.setFixedSize(300, 420)  # 注释掉固定尺寸

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)

        # 创建设置组
        settings = [
            ("窗口背景透明度", "opacity_slider", 10, 100, int(self.parent_window.window_background_opacity * 100)),
            ("文字大小", "font_slider", 8, 20, self.parent_window.current_font_size),
            ("文字透明度", "font_opacity_slider", 10, 100, self.parent_window.current_font_opacity)
        ]
        
        for title, slider_name, min_val, max_val, current_val in settings:
            group = QGroupBox(title)
            group_layout = QVBoxLayout()
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(current_val)
            
            label = QLabel(f"{current_val}{'%' if 'opacity' in slider_name else 'pt'}")
            
            slider.valueChanged.connect(lambda value, lbl=label, unit='%' if 'opacity' in slider_name else 'pt': lbl.setText(f"{value}{unit}"))
            
            group_layout.addWidget(slider)
            group_layout.addWidget(label)
            group.setLayout(group_layout)
            layout.addWidget(group)
            
            setattr(self, slider_name, slider)
            setattr(self, slider_name.replace('slider', 'label'), label)
        
        # 添加开机自启动选项
        autostart_group = self._create_autostart_group()
        layout.addWidget(autostart_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setMinimumSize(300, 380)

    def _create_autostart_group(self):
        """创建开机自启动设置组"""
        group = QGroupBox("开机自启动")
        group_layout = QVBoxLayout()
        
        # 创建复选框和状态标签
        checkbox_layout = QHBoxLayout()
        
        self.autostart_checkbox = QCheckBox("开机时自动启动")
        self.autostart_checkbox.setChecked(self.autostart_manager.is_enabled())
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)

        # 设置复选框字体（增大字体以适应高DPI）
        checkbox_font = self.autostart_checkbox.font()
        checkbox_font.setPointSize(self.font().pointSize())
        self.autostart_checkbox.setFont(checkbox_font)

        self.autostart_status_label = QLabel()
        self.autostart_status_label.setStyleSheet("color: #666;")
        self.update_autostart_status()
        
        checkbox_layout.addWidget(self.autostart_checkbox)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.autostart_status_label)
        
        # 权限提示
        permission_layout = QHBoxLayout()
        self.permission_label = QLabel()
        self.permission_label.setStyleSheet("color: #FF6B6B;")
        self.update_permission_status()
        
        permission_layout.addWidget(self.permission_label)
        permission_layout.addStretch()
        
        group_layout.addLayout(checkbox_layout)
        group_layout.addLayout(permission_layout)
        group.setLayout(group_layout)
        
        return group

    def showEvent(self, event):
        """显示时调整大小"""
        super().showEvent(event)
        self.adjustSize()
        
        # 确保对话框不会太大
        screen = QApplication.primaryScreen().availableGeometry()
        if self.width() > screen.width() * 0.7:
            self.setFixedWidth(int(screen.width() * 0.7))
        if self.height() > screen.height() * 0.7:
            self.setFixedHeight(int(screen.height() * 0.7))

    def update_autostart_status(self):
        """更新开机自启动状态显示"""
        status_text = self.autostart_manager.get_status_text()
        self.autostart_status_label.setText(status_text)

        if self.autostart_manager.is_enabled():
            self.autostart_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.autostart_status_label.setStyleSheet("color: #666;")

    def on_autostart_changed(self, state):
        """开机自启动复选框状态改变"""
        try:
            if state == Qt.Checked:
                success = self.autostart_manager.enable()
            else:
                success = self.autostart_manager.disable()
            
            self.update_autostart_status()
            
            if not success:
                # 如果操作失败，恢复原来的状态
                self.autostart_checkbox.setChecked(not (state == Qt.Checked))
                self.update_autostart_status()
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
            # 出错时恢复原来的状态
            self.autostart_checkbox.setChecked(self.autostart_manager.is_enabled())
    
    def update_autostart_status(self):
        """更新开机自启动状态显示"""
        status_text = self.autostart_manager.get_status_text()
        self.autostart_status_label.setText(status_text)

        if self.autostart_manager.is_enabled():
            self.autostart_status_label.setStyleSheet("color: #4CAF50; font-size: 10pt;")
        else:
            self.autostart_status_label.setStyleSheet("color: #666; font-size: 10pt;")

    def update_permission_status(self):
        """更新权限状态显示"""
        if not check_startup_permission():
            self.permission_label.setText("⚠️ 可能需要管理员权限")
        else:
            self.permission_label.setText("")
        
    def get_settings(self):
        """获取设置"""
        return {
            'opacity': self.opacity_slider.value() / 100.0,
            'font_size': self.font_slider.value(),
            'font_opacity': self.font_opacity_slider.value()
        }


class TransparentTaskWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.habits = []
        self.task_widgets = {}
        self.current_font_size = 11
        self.current_font_opacity = 100
        self.window_background_opacity = 0.8
        self.current_page = 'tasks'  # 'tasks' 或 'habits'
        self.notified_task_ids = set()  # 已弹窗提醒的任务ID集合
        self.water_reminder = load_water_reminder()
        self.water_widget = None

        # 贴边隐藏状态
        self.edge_hidden = False
        self.edge_hide_pos = None
        self.edge_restore_timer = None
        self._hide_anim = None
        self._show_anim = None
        self._rehide_timer = None
        self._should_rehide = False
        self._current_edge = None
        self._original_pos = None
        self._temp_shown = False
        self._restoring = False
        self._edge_show_pos = None
        self._pending_hide = False
        self._pending_hide_edge = None
        self._pending_hide_geometry = None
        self._pending_hide_timer = None

        # 加载保存的设置
        self.load_window_settings()
        
        # 开机自启动管理器
        self.autostart_manager = AutoStartManager()
        
        # 窗口交互状态
        self.dragging = False
        self.drag_position = None
        self.resizing = False
        self.resize_direction = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        
        # 窗口边框设置
        self.border_width = 3  # 边框宽度，用于调整大小检测（从5减小到3，提高检测精度）
        
        # 新增：光标状态同步定时器
        self.cursor_sync_timer = QTimer()
        self.cursor_sync_timer.timeout.connect(self.sync_cursor_state)
        self.cursor_sync_timer.start(50)  # 每50ms同步一次光标状态
        
        # 新增：记录上一次的光标位置和状态，用于检测变化
        self.last_cursor_pos = None
        self.last_cursor_shape = Qt.ArrowCursor
        
        self.setMinimumSize(300, 400)
        self.setMaximumSize(800, 1200)
        
        # 先设置基本窗口属性，再初始化UI
        self.setup_basic_window_properties()
        self.initUI()
        
        # 延迟加载任务，确保窗口完全初始化后再加载数据
        QTimer.singleShot(100, self.delayed_task_load)
        
        # 检查是否是通过开机自启动启动的
        self.check_autostart_launch()
        
        # 监听窗口关闭事件以保存设置
        self.setAttribute(Qt.WA_DeleteOnClose, False)
    
    def setup_basic_window_properties(self):
        """设置基本窗口属性 - 优化版本"""
        # 先设置窗口标题和基本属性
        self.setWindowTitle("桌面任务小组件")
        
        # 设置窗口标志，但避免影响任务栏图标
        # 先使用基本窗口标志，后续再添加置顶等属性
        basic_flags = Qt.FramelessWindowHint | Qt.Window
        self.setWindowFlags(basic_flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口几何属性（初始值，后续会被加载的设置覆盖）
        self.setGeometry(100, 100, 350, 450)
        
        print("✅ 基本窗口属性设置完成")
    
    def setDpiSettings(self):
        """设置窗口DPI相关属性"""
        try:
            # 启用高DPI图标（如果属性存在）
            if hasattr(Qt, 'WA_UseHighDpiPixmaps'):
                self.setAttribute(Qt.WA_UseHighDpiPixmaps, True)
            print(f"✅ 窗口DPI设置完成，缩放因子: {self.devicePixelRatio()}")
        except Exception as e:
            print(f"⚠️ 窗口DPI设置失败: {e}")

    def setup_windows_specific(self):
        """Windows特定设置，优化任务栏图标显示 - 延迟执行"""
        if sys.platform == 'win32':
            # 延迟设置窗口置顶等属性，确保任务栏图标已正确显示
            QTimer.singleShot(500, self.enable_window_topmost)
    
    def enable_window_topmost(self):
        """启用窗口置顶属性（延迟执行）"""
        try:
            current_flags = self.windowFlags()
            new_flags = current_flags | Qt.WindowStaysOnTopHint
            self.setWindowFlags(new_flags)
            self.show()  # 重新显示窗口以应用新标志
            print("✅ 窗口置顶属性已启用")
        except Exception as e:
            print(f"⚠️ 启用窗口置顶属性失败: {e}")

    def check_autostart_launch(self):
        """检查是否是通过开机自启动启动的"""
        try:
            if self.autostart_manager.is_enabled():
                print("✓ 开机自启动已启用")
            else:
                print("✗✗ 开机自启动未启用")
        except Exception as e:
            print(f"检查开机自启动状态失败: {e}")

    def initUI(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部栏
        self.drag_area = self._create_top_bar()
        
        # 任务列表容器
        self.list_container = QWidget()
        list_layout = QVBoxLayout(self.list_container)
        list_layout.setContentsMargins(5, 5, 5, 5)  # 容器边距
        list_layout.setSpacing(0)  # 容器内无间距

        # 饮水小组件（习惯页顶部固定显示）
        self.water_widget = WaterDisplayWidget(self.water_reminder, self)
        self.water_widget.setVisible(False)
        list_layout.addWidget(self.water_widget, 0)

        self.task_list_widget = QListWidget()
        # 为列表控件设置唯一ID，防止样式继承冲突
        self.task_list_widget.setObjectName("TaskListWidget")
        self.task_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 启用水平滚动条的自动显示
        self.task_list_widget.setHorizontalScrollMode(QListWidget.ScrollPerPixel)
        self.task_list_widget.setWrapping(False)  # 禁用自动换行
        self.task_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 设置列表控件的边距，确保与任务项边距一致
        self.task_list_widget.setContentsMargins(0, 0, 0, 0)
        
        list_layout.addWidget(self.task_list_widget, 1)
        
        main_layout.addWidget(self.drag_area)
        main_layout.addWidget(self.list_container)
        self.setLayout(main_layout)
        
        # 设置鼠标跟踪
        for widget in [self, self.drag_area, self.list_container, self.task_list_widget]:
            widget.setMouseTracking(True)
        
        # 定时器和事件过滤器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_task_display)
        self.refresh_timer.start(60000)

        # 截止时间提醒定时器（每30秒检查一次）
        self.deadline_notify_timer = QTimer()
        self.deadline_notify_timer.timeout.connect(self.check_deadline_notifications)
        self.deadline_notify_timer.start(30000)

        self.installEventFilter(self)
        self.update_window_style()
        
        # 延迟执行Windows特定设置
        self.setup_windows_specific()
    
    def _create_top_bar(self):
        """创建顶部栏"""
        drag_area = QWidget()
        drag_area.setFixedHeight(30)

        layout = QHBoxLayout(drag_area)
        layout.setContentsMargins(5, 0, 5, 0)

        layout.addStretch()

        # 页面切换按钮
        self.page_toggle_btn = QPushButton("📋")
        self.page_toggle_btn.setFixedSize(25, 25)
        self.page_toggle_btn.setToolTip("切换到习惯页")
        self.page_toggle_btn.clicked.connect(self.toggle_page)

        # 按钮配置
        buttons = [
            ("📍", "取消置顶", self.toggle_window_topmost, True),  # 置顶按钮
            ("➕", None, self.show_add_dialog, False),  # 添加按钮
            (None, None, None, None),  # 占位：切换按钮在此处插入
            ("⚙️", None, self.show_settings_dialog, False)   # 设置按钮
        ]
        
        for icon, tooltip, callback, checkable in buttons:
            if icon is None:
                layout.addWidget(self.page_toggle_btn)
                continue
            btn = QPushButton(icon)
            btn.setFixedSize(25, 25)
            btn.setCheckable(checkable)
            if checkable:
                btn.setChecked(True)
            if tooltip:
                btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            
            if icon == "📍":
                self.pin_button = btn
            elif icon == "➕":
                self.add_button = btn
            elif icon == "⚙️":
                self.settings_button = btn
        
        return drag_area

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            self.window_background_opacity = settings['opacity']
            self.current_font_size = settings['font_size']
            self.current_font_opacity = settings['font_opacity']
            self.update_window_style()
            self.refresh_task_display()

    def update_window_style(self):
        """更新窗口样式"""
        bg_alpha = int(self.window_background_opacity * 255)
        font_alpha = int(self.current_font_opacity * 255 / 100)

        # 1. 设置列表控件的基本样式，使用ID选择器
        list_widget_style = f"""
            #TaskListWidget {{
                background: transparent;
                color: rgba(255, 255, 255, {font_alpha});
                border: none;
                font-size: {self.current_font_size}pt;
                font-family: 'Microsoft YaHei', sans-serif;
                outline: none;
            }}
            #TaskListWidget::item {{
                border-bottom: 1px solid rgba(255, 255, 255, {max(15, font_alpha//4)});
                background: transparent;
                padding: 0px;
                border: none;
            }}
            #TaskListWidget::item:selected {{
                background: transparent;
            }}
        """
        self.task_list_widget.setStyleSheet(list_widget_style)

        # 2. 核心修改：设置VS Code风格且支持悬停显示的滚动条样式
        scrollbar_style = f"""
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(100, 100, 100, 0); /* 初始完全透明 */
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(120, 120, 120, 220); /* 悬停时显示 */
            }}
            QScrollBar::handle:vertical:pressed {{
                background: rgba(140, 140, 140, 255);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(100, 100, 100, 0); /* 初始完全透明 */
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(120, 120, 120, 220); /* 悬停时显示 */
            }}
            QScrollBar::handle:horizontal:pressed {{
                background: rgba(140, 140, 140, 255);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """
        # 直接应用样式到滚动条对象
        self.task_list_widget.verticalScrollBar().setStyleSheet(scrollbar_style)
        self.task_list_widget.horizontalScrollBar().setStyleSheet(scrollbar_style)
        # 确保滚动条策略设置为"需要时出现"，这是悬停显示的基础
        self.task_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 3. 其他控件的样式保持不变
        button_style = f"""
            QPushButton {{
                background: transparent;
                color: rgba(255, 255, 255, {font_alpha});
                border: none;
                font-size: 12pt;
                font-weight: 375;  /* 轻微加粗，优化字体渲染效果 */
                width: 25px;
                height: 25px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 50);
                border-radius: 3px;
            }}
            QPushButton:focus {{
                outline: none;  /* 仅移除焦点轮廓，不影响选中状态 */
            }}
        """
        
        self.drag_area.setStyleSheet(f"background: transparent; border-top-left-radius: 5px; border-top-right-radius: 5px;")
        self.list_container.setStyleSheet(f"background: transparent;")
        
        for btn in [self.add_button, self.pin_button, self.settings_button, self.page_toggle_btn]:
            btn.setStyleSheet(button_style)

        # 饮水模块按钮样式
        if hasattr(self, 'water_widget') and self.water_widget:
            water_btn_style = f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 15);
                    color: rgba(255, 255, 255, {font_alpha});
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 9pt;
                }}
                QPushButton:hover {{ background: rgba(255, 255, 255, 30); }}
            """
            for btn in self.water_widget.findChildren(QPushButton):
                if btn.text() in ("喝一杯", "喝半杯", "抿一口", "稍后"):
                    btn.setStyleSheet(water_btn_style)

        # 4. 更新所有任务项的样式和布局，并立即刷新任务项宽度
        self._update_all_task_items_style()
        self._update_task_items_layout()
        # 立即强制更新一次任务项宽度，解决初始显示或缩放后可能出现的截断问题
        QTimer.singleShot(0, self.update_task_item_widths)
        
        # 更新所有任务项的样式和布局
        self._update_all_task_items_style()
        self._update_task_items_layout()
    
    def _update_all_task_items_style(self):
        """更新所有任务项的样式"""
        for task_id, task_widget in self.task_widgets.items():
            if hasattr(task_widget, 'update_text_style'):
                task_widget.update_text_style()
            if hasattr(task_widget, '_update_task_background'):
                task_widget._update_task_background()
    
    def _update_task_items_layout(self):
        """更新任务项布局，确保高度适应字体大小"""
        if self.task_list_widget.count() > 0:
            for i in range(self.task_list_widget.count()):
                item = self.task_list_widget.item(i)
                widget = self.task_list_widget.itemWidget(item)
                if widget:
                    # 更新项的大小提示
                    item.setSizeHint(widget.sizeHint())
            
            # 强制刷新列表视图
            self.task_list_widget.updateGeometry()
            self.task_list_widget.update()

    def show_add_task_dialog(self):
        """显示添加任务对话框"""
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            content, deadline, priority = dialog.get_task_data()
            if content:
                self.add_new_task(content, deadline, priority)

    def add_new_task(self, content, deadline, priority):
        """添加新任务"""
        task = Task(content, deadline, priority)
        self._check_and_update_urgency(task)
        self.tasks.append(task)
        self.save_tasks()
        self.refresh_task_display()

    def refresh_task_display(self):
        """刷新任务/习惯显示"""
        if self.current_page == 'habits':
            self.water_widget.setVisible(True)
            self.water_widget.update_countdown()
            self.refresh_habit_display()
            return
        self.water_widget.setVisible(False)

        # 首先检查并更新所有任务的紧急状态
        for task in self.tasks:
            self._check_and_update_urgency(task)
        
        self.task_list_widget.clear()
        self.task_widgets.clear()
        
        # 过滤掉已归档的任务
        active_tasks = [task for task in self.tasks if not getattr(task, 'is_archived', False)]
        
        # 分类和排序任务
        done_tasks = [task for task in active_tasks if task.is_done]
        undone_tasks = [task for task in active_tasks if not task.is_done]
        overdue_tasks = [task for task in undone_tasks if task.is_overdue()]
        active_tasks = [task for task in undone_tasks if not task.is_overdue()]
        
        # 按照要求排序：首先按优先级，优先级相同则按截止日期升序
        active_tasks.sort(key=lambda t: (t.priority, t.deadline))
        overdue_tasks.sort(key=lambda t: (t.priority, t.deadline))
        done_tasks.sort(key=lambda t: (t.priority, t.deadline), reverse=True)
        
        # 显示任务
        for task in active_tasks + overdue_tasks + done_tasks:
            task_widget = TaskListWidgetItem(task, self)
            self.task_widgets[task.id] = task_widget
            task_widget.task_status_changed.connect(self.on_task_status_changed)

            item = QListWidgetItem(self.task_list_widget)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.task_list_widget.setItemWidget(item, task_widget)
            task_widget.update_text_style()
            item.setSizeHint(task_widget.sizeHint())

    def on_task_status_changed(self, task_id, is_done):
        """任务状态改变处理"""
        for task in self.tasks:
            if task.id == task_id:
                task.is_done = is_done
                break
        self.save_tasks()
        self.refresh_task_display()
    
    def on_item_double_clicked(self, item):
        """列表项双击事件处理"""
        if self.current_page == 'habits':
            self.on_habit_double_clicked(item)
            return

        task_widget = self.task_list_widget.itemWidget(item)
        if task_widget and hasattr(task_widget, 'task'):
            dialog = EditTaskDialog(task_widget.task, self)
            result = dialog.exec_()
            
            content, deadline, priority, to_delete, to_archive = dialog.get_task_data()
            
            if to_delete:
                self.tasks = [task for task in self.tasks if task.id != task_widget.task.id]
            elif to_archive:
                # 归档任务
                success = archive_task(task_widget.task)
                if success:
                    # 任务已标记为已归档，保留在任务列表中
                    # 不需要从列表中移除，因为refresh_task_display会过滤掉已归档的任务
                    pass
                else:
                    QMessageBox.warning(self, "归档失败", "任务归档失败，请重试")
            elif result == QDialog.Accepted and content:
                task_widget.task.content = content
                task_widget.task.deadline = deadline
                task_widget.task.priority = priority
                task_widget.task.original_priority = priority  # 同时更新原始优先级
                # 重新评估任务的紧急状态，确保优先级正确还原
                self._check_and_update_urgency(task_widget.task)
            
            if to_delete or to_archive or result == QDialog.Accepted:
                self.save_tasks()
                self.refresh_task_display()

    def _check_and_update_urgency(self, task):
        """检查并更新任务的紧急状态"""
        if not task.is_done:
            try:
                time_diff = (task.get_deadline_datetime() - datetime.now()).total_seconds()
                
                if task.is_overdue():
                    # 过期任务：还原为原始优先级颜色
                    task.priority = task.original_priority
                elif 0 < time_diff <= 3600:  # 剩余时间在1小时以内
                    # 剩余时间小于等于1小时的任务：变为红色（P0）
                    task.priority = 0
                else:
                    # 正常任务（剩余时间大于1小时）：还原为原始优先级
                    task.priority = task.original_priority
            except:
                pass

    def paintEvent(self, event):
        """绘制窗口边框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_alpha = int(self.window_background_opacity * 255)
        border_alpha = int(bg_alpha * 0.5)
        
        # 绘制窗口背景
        painter.setBrush(QBrush(QColor(50, 50, 50, bg_alpha)))
        # 使用透明边框，避免显示白色边框
        painter.setPen(QPen(QColor(50, 50, 50, bg_alpha), 1))
        painter.drawRoundedRect(self.rect(), 5, 5)
    
    def _get_resize_info(self, pos):
        """获取调整大小信息（优化版本）"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        
        # 使用更精确的边界检测，避免内部区域误判
        left_edge = x <= self.border_width
        right_edge = x >= w - self.border_width
        top_edge = y <= self.border_width
        bottom_edge = y >= h - self.border_width
        
        # 只有当鼠标确实在边界上时才返回调整大小方向
        if left_edge and top_edge:
            return 'left_top', Qt.SizeFDiagCursor
        elif right_edge and top_edge:
            return 'right_top', Qt.SizeBDiagCursor
        elif left_edge and bottom_edge:
            return 'left_bottom', Qt.SizeBDiagCursor
        elif right_edge and bottom_edge:
            return 'right_bottom', Qt.SizeFDiagCursor
        elif left_edge:
            return 'left', Qt.SizeHorCursor
        elif right_edge:
            return 'right', Qt.SizeHorCursor
        elif top_edge:
            return 'top', Qt.SizeVerCursor
        elif bottom_edge:
            return 'bottom', Qt.SizeVerCursor
        else:
            return None, Qt.ArrowCursor
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 取消待触发的贴边隐藏
            if self._pending_hide:
                self._pending_hide = False
                self._stop_pending_hide_timer()
            pos = event.pos()
            
            direction, cursor = self._get_resize_info(pos)
            if direction:
                self.resizing = True
                self.resize_direction = direction
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                self.setCursor(cursor)
                self.grabMouse()
                event.accept()
                return
            
            if self.drag_area.geometry().contains(pos):
                self.dragging = True
                self.drag_position = event.globalPos() - self.pos()
                self.grabMouse()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 优化版本"""
        pos = event.pos()
        
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            # 拖动时立即更新光标位置记录
            self.last_cursor_pos = pos
        elif self.resizing:
            self._resize_window(event.globalPos())
            # 调整大小时立即更新光标位置记录
            self.last_cursor_pos = pos
        else:
            # 立即更新光标状态，不依赖定时器
            direction, cursor = self._get_resize_info(pos)
            
            # 立即设置光标，不等待定时器
            self.setCursor(cursor)
            self.last_cursor_shape = cursor
            self.last_cursor_pos = pos
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        was_dragging = self.dragging

        if self.dragging or self.resizing:
            self.releaseMouse()

        self.dragging = False
        self.resizing = False
        self.resize_direction = None

        # 贴边隐藏：拖动结束后触发
        if was_dragging:
            edge = self._check_near_edge()
            if edge:
                # 吸附到屏幕边缘
                geo = self.geometry()
                screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
                sg = screen.geometry()
                snap = {'left': sg.left(), 'right': sg.right() + 1 - geo.width(),
                        'top': sg.top()}
                if edge in snap:
                    sx = snap[edge] if edge != 'top' else geo.x()
                    sy = geo.y() if edge != 'top' else snap['top']
                    self.move(sx, sy)
                # 等鼠标离开窗口后再触发隐藏（参考QQ逻辑）
                self._pending_hide = True
                self._pending_hide_edge = edge
                self._pending_hide_geometry = self.geometry()
                self._start_pending_hide_timer()
                return
            # 拖动离开边缘，取消自动再隐藏
            if self._should_rehide:
                self._should_rehide = False
                self._stop_rehide_timer()

        # 释放后立即同步光标状态
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        if self.rect().contains(cursor_pos):
            direction, cursor = self._get_resize_info(cursor_pos)
            self.setCursor(cursor)
            self.last_cursor_shape = cursor
            self.last_cursor_pos = cursor_pos
        else:
            self.setCursor(Qt.ArrowCursor)
            self.last_cursor_shape = Qt.ArrowCursor
            self.last_cursor_pos = None
    
    def sync_cursor_state(self):
        """同步光标状态 - 定时器驱动，确保光标状态正确"""
        # 如果正在拖动或调整大小，不干扰用户操作
        if self.dragging or self.resizing:
            return
            
        try:
            # 获取当前鼠标在屏幕上的位置
            global_pos = QCursor.pos()
            # 转换为窗口相对坐标
            window_pos = self.mapFromGlobal(global_pos)
            
            # 检查鼠标是否在窗口内
            if not self.rect().contains(window_pos):
                # 鼠标不在窗口内，不需要处理
                self.last_cursor_pos = None
                return
                
            # 检查位置是否发生变化
            if self.last_cursor_pos == window_pos:
                # 位置未变化，不需要更新
                return
                
            # 记录新位置
            self.last_cursor_pos = window_pos
            
            # 根据当前位置计算应该显示的光标
            direction, expected_cursor = self._get_resize_info(window_pos)
            current_cursor = self.cursor().shape()
            
            # 只有当实际光标与期望光标不一致时才更新
            if current_cursor != expected_cursor:
                self.setCursor(expected_cursor)
                self.last_cursor_shape = expected_cursor
                
        except Exception as e:
            # 避免定时器异常导致程序崩溃
            print(f"光标状态同步异常: {e}")

    def force_cursor_update(self):
        """强制更新光标状态（简化为调用同步方法）"""
        self.sync_cursor_state()

    def enterEvent(self, event):
        """鼠标进入窗口事件 - 优化版本"""
        super().enterEvent(event)
        
        # 鼠标进入时立即强制同步光标状态
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        direction, cursor = self._get_resize_info(cursor_pos)
        
        # 立即设置，不等待定时器
        self.setCursor(cursor)
        self.last_cursor_shape = cursor
        self.last_cursor_pos = cursor_pos

    def leaveEvent(self, event):
        """鼠标离开窗口事件 - 优化版本"""
        super().leaveEvent(event)
        
        # 鼠标离开时立即恢复默认光标
        self.setCursor(Qt.ArrowCursor)
        self.last_cursor_shape = Qt.ArrowCursor
        self.last_cursor_pos = None
    
    def closeEvent(self, event):
        """窗口关闭事件 - 保存设置"""
        print("📝 窗口关闭中，正在保存设置...")
        
        # 保存窗口设置
        self.save_window_settings()
        
        # 接受关闭事件
        event.accept()
        
        print("✅ 窗口设置已保存，程序退出")
    
    def _resize_window(self, global_pos):
        """调整窗口大小"""
        if not self.resize_direction:
            return
            
        dx = global_pos.x() - self.resize_start_pos.x()
        dy = global_pos.y() - self.resize_start_pos.y()
        
        geo = self.resize_start_geometry
        directions = self.resize_direction.split('_')
        
        new_x, new_y = geo.x(), geo.y()
        new_w, new_h = geo.width(), geo.height()
        
        for direction in directions:
            if direction == 'left':
                new_w = max(self.minimumWidth(), min(geo.width() - dx, self.maximumWidth()))
                if new_w != geo.width():
                    new_x = geo.x() + (geo.width() - new_w)
            elif direction == 'right':
                new_w = max(self.minimumWidth(), min(geo.width() + dx, self.maximumWidth()))
            elif direction == 'top':
                new_h = max(self.minimumHeight(), min(geo.height() - dy, self.maximumHeight()))
                if new_h != geo.height():
                    new_y = geo.y() + (geo.height() - new_h)
            elif direction == 'bottom':
                new_h = max(self.minimumHeight(), min(geo.height() + dy, self.maximumHeight()))
        
        self.setGeometry(new_x, new_y, new_w, new_h)
        self.update_task_item_widths()
    
    def update_task_item_widths(self):
        """更新任务项宽度"""
        if self.task_list_widget.count() > 0:
            for i in range(self.task_list_widget.count()):
                item = self.task_list_widget.item(i)
                widget = self.task_list_widget.itemWidget(item)
                if widget and hasattr(widget, 'label'):
                    widget.label.setMinimumWidth(120)
                    widget.label.setMaximumWidth(16777215)
                    widget.updateGeometry()
                    item.setSizeHint(widget.sizeHint())
            
            self.task_list_widget.update()
    
    def update_content_only(self):
        """只更新内容区域，避免全窗口重绘"""
        # 只更新列表容器的内容，不重绘窗口边框
        self.list_container.update()
        if self.task_list_widget.count() > 0:
            self.task_list_widget.update()
    
    def animate_content_transition(self):
        """添加微小的视觉过渡效果"""
        # 使用定时器创建平滑过渡效果
        QTimer.singleShot(10, self._finish_content_transition)
    
    def _finish_content_transition(self):
        """完成内容过渡效果"""
        # 确保所有任务项都正确更新
        self.update_task_item_widths()
        # 轻微刷新界面，确保视觉一致性
        self.task_list_widget.update()
    
    def resizeEvent(self, event):
        """窗口大小改变事件 - 优化版本"""
        super().resizeEvent(event)
        
        if event.oldSize() != event.size():
            # 优化：减少重绘区域
            if self.resizing:
                # 只更新必要的内容区域，避免全窗口重绘
                self.update_content_only()
            else:
                # 正常情况下的完整更新
                self.update_task_item_widths()
            
            # 添加微小的视觉过渡
            self.animate_content_transition()

    def load_tasks(self):
        """加载任务"""
        self.tasks = load_tasks_from_json()

    def save_tasks(self):
        """保存任务"""
        save_tasks_to_json(self.tasks)

    def eventFilter(self, obj, event):
        """事件过滤器"""
        if event.type() == event.WindowDeactivate:
            self.task_list_widget.clearSelection()
        return super().eventFilter(obj, event)
    
    def toggle_window_topmost(self):
        """切换窗口置顶状态"""
        is_topmost = self.pin_button.isChecked()

        try:
            current_flags = self.windowFlags()

            if is_topmost:
                new_flags = current_flags | Qt.WindowStaysOnTopHint
                self.pin_button.setText("📍")
                self.pin_button.setToolTip("取消置顶")
            else:
                new_flags = current_flags & ~Qt.WindowStaysOnTopHint
                self.pin_button.setText("📌")
                self.pin_button.setToolTip("窗口置顶")

            current_geometry = self.geometry()
            self.setWindowFlags(new_flags)
            self.setGeometry(current_geometry)
            self.show()

        except Exception as e:
            print(f"⚠️ 切换窗口置顶状态失败: {e}")
            self.pin_button.setChecked(not is_topmost)
    
    def delayed_task_load(self):
        """延迟加载任务，确保窗口完全初始化后再加载数据"""
        print("🕐 开始延迟加载任务...")

        # 加载任务数据
        self.load_tasks()
        self.habits = load_habits_from_json()
        self.water_reminder = load_water_reminder()
        self.water_widget.water = self.water_reminder
        self.water_widget._update_all()

        # 刷新任务显示
        self.refresh_task_display()

        print("✅ 任务加载完成，任务栏图标应正常显示")
        
        # 应用加载的窗口位置和大小
        self.apply_loaded_settings()
    
    def load_window_settings(self):
        """加载窗口设置"""
        try:
            settings = load_settings()
            
            # 加载窗口透明度
            if 'window_background_opacity' in settings:
                self.window_background_opacity = settings['window_background_opacity']
                print(f"✅ 加载窗口透明度: {self.window_background_opacity}")
            
            # 加载文字大小
            if 'current_font_size' in settings:
                self.current_font_size = settings['current_font_size']
                print(f"✅ 加载文字大小: {self.current_font_size}")
            
            # 加载文字透明度
            if 'current_font_opacity' in settings:
                self.current_font_opacity = settings['current_font_opacity']
                print(f"✅ 加载文字透明度: {self.current_font_opacity}")
            
            # 保存窗口几何信息用于后续应用
            self._loaded_geometry = settings.get('window_geometry', None)
            
        except Exception as e:
            print(f"⚠️ 加载窗口设置失败: {e}")
            self._loaded_geometry = None
    
    def apply_loaded_settings(self):
        """应用加载的设置（在窗口显示后调用）"""
        try:
            # 应用窗口位置和大小
            if hasattr(self, '_loaded_geometry') and self._loaded_geometry:
                parts = self._loaded_geometry.split(',')
                if len(parts) == 4:
                    x, y, width, height = map(int, parts)
                    # 确保窗口在屏幕范围内
                    screen = QApplication.primaryScreen().availableGeometry()
                    x = max(0, min(x, screen.width() - 100))
                    y = max(0, min(y, screen.height() - 100))
                    self.setGeometry(x, y, width, height)
                    print(f"✅ 应用窗口位置: ({x}, {y}), 大小: {width}x{height}")
            
            # 更新窗口样式
            self.update_window_style()
            
        except Exception as e:
            print(f"⚠️ 应用设置失败: {e}")
    
    def save_window_settings(self):
        """保存窗口设置"""
        try:
            settings = {
                'window_background_opacity': self.window_background_opacity,
                'current_font_size': self.current_font_size,
                'current_font_opacity': self.current_font_opacity,
                'window_geometry': f"{self.x()},{self.y()},{self.width()},{self.height()}"
            }

            save_settings(settings)
            print(f"✅ 窗口设置已保存: 位置({self.x()}, {self.y()}), 大小({self.width()}x{self.height()})")

        except Exception as e:
            print(f"⚠️ 保存窗口设置失败: {e}")

    # ========== 页面切换 ==========

    def toggle_page(self):
        if self.current_page == 'tasks':
            self.current_page = 'habits'
            self.page_toggle_btn.setText("🔄")
            self.page_toggle_btn.setToolTip("切换到任务页")
        else:
            self.current_page = 'tasks'
            self.page_toggle_btn.setText("📋")
            self.page_toggle_btn.setToolTip("切换到习惯页")
        self.refresh_task_display()

    def show_add_dialog(self):
        if self.current_page == 'tasks':
            self.show_add_task_dialog()
        else:
            self.show_add_habit_dialog()

    # ========== 习惯管理 ==========

    def show_add_habit_dialog(self):
        dialog = AddHabitDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_habit_data()
            if data.content:
                self.add_new_habit(data)

    def add_new_habit(self, data):
        habit = Habit(
            content=data.content,
            time=data.time_str,
            freq_mode=data.freq_mode,
            weekdays=data.weekdays,
            weekly_target=data.weekly_target,
            interval_days=data.interval_days,
        )
        self.habits.append(habit)
        self.save_habits()
        self.refresh_task_display()

    def save_habits(self):
        save_habits_to_json(self.habits)

    def _sync_habit_log(self, record_type="status"):
        log = load_habit_log()
        today = date.today().isoformat()
        if today not in log:
            log[today] = {}
        for h in self.habits:
            log[today][str(h.id)] = {
                "content": h.content,
                "is_done": h.is_done_today,
                "is_archived": h.is_archived,
                "time": h.time,
                "freq_mode": h.freq_mode,
                "weekly_completed": h.weekly_completed,
                "current_streak": h.current_streak,
                "record_type": record_type,
            }
        save_habit_log(log)

    def _sync_habit_log_for_date(self, log_date):
        log = load_habit_log()
        if log_date not in log:
            log[log_date] = {}
        for h in self.habits:
            log[log_date][str(h.id)] = {
                "content": h.content,
                "is_done": h.is_done_today,
                "is_archived": h.is_archived,
                "time": h.time,
                "freq_mode": h.freq_mode,
                "weekly_completed": h.weekly_completed,
                "current_streak": h.current_streak,
                "record_type": "archive",
            }
        save_habit_log(log)

    def refresh_habit_display(self):
        # 检查周切和日切，归档昨天的习惯日志
        today = date.today().isoformat()
        for h in self.habits:
            if h.is_done_today and h.done_date and h.done_date != today:
                old_date = h.done_date
                old_done = h.is_done_today
                h.check_daily_reset()
                # 用重置前的状态归档
                h.is_done_today = old_done
                self._sync_habit_log_for_date(old_date)
                h.is_done_today = False
        for h in self.habits:
            h.check_weekly_reset()
            h.check_daily_reset()

        self.task_list_widget.clear()
        self.task_widgets.clear()

        habits_sorted = sorted(self.habits, key=lambda h: h.time)
        active_habits = [h for h in habits_sorted if not h.is_archived]
        done_habits = [h for h in active_habits if h.is_done_today]
        undone_habits = [h for h in active_habits if not h.is_done_today]

        for habit in undone_habits + done_habits:
            widget = TaskListWidgetItem(habit, self, mode='habit')
            self.task_widgets[habit.id] = widget
            widget.habit_status_changed.connect(self.on_habit_status_changed)

            item = QListWidgetItem(self.task_list_widget)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.task_list_widget.setItemWidget(item, widget)
            widget.update_text_style()
            item.setSizeHint(widget.sizeHint())

    def on_habit_status_changed(self, habit_id, is_done, popup_msg=None):
        self.save_habits()
        self._sync_habit_log()
        self.refresh_task_display()
        if popup_msg:
            self.show_deadline_notification("习惯养成", 0, msg_override=popup_msg)

    def on_habit_double_clicked(self, item):
        widget = self.task_list_widget.itemWidget(item)
        if not widget or not hasattr(widget, 'habit'):
            return

        dialog = AddHabitDialog(habit=widget.habit, parent=self)
        dialog.exec_()

        data = dialog.get_habit_data()

        if data.to_delete:
            self.habits = [h for h in self.habits if h.id != widget.habit.id]
        elif data.to_archive:
            widget.habit.archive()
            self._sync_habit_log(record_type="archive")
        elif data.content:
            widget.habit.content = data.content
            widget.habit.time = data.time_str
            widget.habit.freq_mode = data.freq_mode
            widget.habit.weekdays = data.weekdays
            widget.habit.weekly_target = data.weekly_target
            widget.habit.interval_days = data.interval_days

        self.save_habits()
        self.refresh_task_display()

    # ========== 截止时间弹窗提醒 ==========

    def check_deadline_notifications(self):
        now = datetime.now()
        all_tasks = [t for t in self.tasks if not t.is_archived]
        all_habits = self.habits

        # 检查任务
        for task in all_tasks:
            if task.is_done:
                self.notified_task_ids.discard(task.id)
                continue
            try:
                time_diff = (task.get_deadline_datetime() - now).total_seconds()
                if 0 < time_diff <= 3600 and task.id not in self.notified_task_ids:
                    self.notified_task_ids.add(task.id)
                    minutes_left = int(time_diff / 60)
                    self.show_deadline_notification(task.content, minutes_left)
            except Exception:
                pass

        # 检查习惯（设置了时间、当前未完成、今天活跃、未归档）
        for habit in all_habits:
            if habit.is_done_today:
                continue
            if habit.is_archived:
                continue
            if not habit.is_active_today():
                continue
            try:
                h, m = habit.time.split(":")
                habit_dt = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                time_diff = (habit_dt - now).total_seconds()
                if 0 < time_diff <= 3600 and habit.id not in self.notified_task_ids:
                    self.notified_task_ids.add(habit.id)
                    minutes_left = int(time_diff / 60)
                    self.show_deadline_notification(habit.content, minutes_left)
            except Exception:
                pass

        # 饮水提醒
        if self.water_reminder:
            water_msg = self.water_reminder.update_reminder()
            if water_msg:
                self.show_deadline_notification("饮水提醒", 0, msg_override=water_msg)
            if self.water_widget and self.water_widget.isVisible():
                self.water_widget.update_countdown()

    def show_deadline_notification(self, content, minutes_left, msg_override=None):
        """弹出Windows系统通知（右下角通知中心）"""
        title = "任务提醒"
        if msg_override:
            msg = msg_override
        else:
            msg = f"「{content}」将在 {minutes_left} 分钟后到期！"
        try:
            from winotify import Notification, audio
            toast = Notification(
                app_id="桌面任务小组件",
                title=title,
                msg=msg,
                duration="long",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except ImportError:
            # winotify未安装，回退到MessageBoxW
            try:
                ctypes.windll.user32.MessageBoxW(
                    0, msg, title,
                    0x00000040 | 0x00001000
                )
            except Exception as e:
                print(f"弹窗提醒失败: {e}")
        except Exception as e:
            print(f"通知发送失败: {e}")

    def _check_near_edge(self):
        geo = self.geometry()
        screen = QApplication.screenAt(self.pos())
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()
        threshold = 5

        dists = {}
        if abs(geo.left() - sg.left()) <= threshold:
            dists['left'] = abs(geo.left() - sg.left())
        if abs(sg.right() - geo.right()) <= threshold:
            dists['right'] = abs(sg.right() - geo.right())
        if abs(geo.top() - sg.top()) <= threshold:
            dists['top'] = abs(geo.top() - sg.top())

        if not dists:
            return None
        best_dist = min(dists.values())
        candidates = [e for e, d in dists.items() if d == best_dist]
        if len(candidates) == 1:
            return candidates[0]
        # 等距离时优先 top > right > left
        for preferred in ('top', 'right', 'left'):
            if preferred in candidates:
                return preferred
        return candidates[0]

    def _hide_at_edge(self, edge):
        """窗口完全滑出屏幕边缘，靠2px条触发恢复"""
        if self.edge_hidden:
            return
        self.edge_hidden = True
        self._current_edge = edge
        self._should_rehide = True
        self._original_pos = self.pos()
        self._temp_shown = False
        self._restoring = False
        self._edge_show_pos = None
        self._stop_restore_timer()
        self._stop_rehide_timer()

        geo = self.geometry()
        # 用窗口位置取屏幕，比center()更可靠（边缘处center可能跨屏）
        screen = QApplication.screenAt(self.pos())
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()

        targets = {
            'left':   (sg.left() - geo.width(), geo.y()),
            'right':  (sg.right() + 1, geo.y()),
            'top':    (geo.x(), sg.top() - geo.height()),
        }
        show_targets = {
            'left':   (sg.left() - geo.width() + 2, geo.y()),
            'right':  (sg.right() - 1, geo.y()),
            'top':    (geo.x(), sg.top() - geo.height() + 2),
        }
        tx, ty = targets.get(edge, (geo.x(), geo.y()))

        # 方向校验：target必须在正确的一侧，否则回退到主屏幕
        bad = False
        if edge == 'left' and tx >= sg.left():
            bad = True
        elif edge == 'right' and tx <= sg.right():
            bad = True
        elif edge == 'top' and ty >= sg.top():
            bad = True
        if bad:
            screen = QApplication.primaryScreen()
            sg = screen.geometry()
            targets = {
                'left':   (sg.left() - geo.width(), geo.y()),
                'right':  (sg.right() + 1, geo.y()),
                'top':    (geo.x(), sg.top() - geo.height()),
            }
            show_targets = {
                'left':   (sg.left() - geo.width() + 2, geo.y()),
                'right':  (sg.right() - 1, geo.y()),
                'top':    (geo.x(), sg.top() - geo.height() + 2),
            }
            tx, ty = targets.get(edge, (geo.x(), geo.y()))

        self._edge_hide_pos = (tx, ty)
        self._edge_show_pos = show_targets.get(edge, (geo.x(), geo.y()))

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setEndValue(QPoint(tx, ty))
        anim.finished.connect(self._on_hide_anim_done)
        self._hide_anim = anim
        anim.start()

    def _on_hide_anim_done(self):
        if self.edge_hidden:
            # 隐藏完成后始终保持TopMost，确保2px条可被鼠标触发
            try:
                import ctypes
                hwnd = int(self.winId())
                SWP_NOACTIVATE = 0x0010
                HWND_TOPMOST = -1
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    0x0002 | 0x0001 | SWP_NOACTIVATE)  # SWP_NOMOVE | SWP_NOSIZE
            except Exception:
                pass
            self._start_restore_timer()

    def _restore_from_edge(self):
        """窗口滑回原始位置"""
        if not self.edge_hidden:
            return
        self.edge_hidden = False
        self._temp_shown = False
        self._restoring = True
        self._stop_restore_timer()

        if self._hide_anim and self._hide_anim.state() == QPropertyAnimation.Running:
            self._hide_anim.stop()
        if self._show_anim and self._show_anim.state() == QPropertyAnimation.Running:
            self._show_anim.stop()

        orig = self._original_pos if self._original_pos else self.pos()
        screen = QApplication.screenAt(orig)
        if screen:
            sg = screen.geometry()
        else:
            sg = QApplication.primaryScreen().geometry()
        ox = max(sg.left(), min(orig.x(), sg.right() - self.width()))
        oy = max(sg.top(), min(orig.y(), sg.bottom() - self.height()))

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setEndValue(QPoint(ox, oy))
        anim.finished.connect(self._on_restore_anim_done)
        self._show_anim = anim
        anim.start()

    def _on_restore_anim_done(self):
        # 恢复动画结束，取消TopMost
        if self._restoring:
            self._restoring = False
            try:
                import ctypes
                hwnd = int(self.winId())
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                HWND_NOTOPMOST = -2
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            except Exception:
                pass
        if self._should_rehide and self._current_edge:
            self._start_rehide_timer()

    def _start_restore_timer(self):
        if self.edge_restore_timer:
            return
        self.edge_restore_timer = QTimer(self)
        self.edge_restore_timer.timeout.connect(self._check_cursor_near_hidden_edge)
        self.edge_restore_timer.start(100)

    def _stop_restore_timer(self):
        if self.edge_restore_timer:
            self.edge_restore_timer.stop()
            self.edge_restore_timer = None

    def _check_cursor_near_hidden_edge(self):
        """检测光标是否进入被隐藏边缘的2px条，触发恢复"""
        if not self.edge_hidden or not self._current_edge or self._restoring:
            return
        if self._hide_anim and self._hide_anim.state() == QPropertyAnimation.Running:
            return

        pos = QCursor.pos()
        edge = self._current_edge
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()

        enter = False
        if edge == 'left':
            enter = pos.x() <= sg.left() + 1
        elif edge == 'right':
            enter = pos.x() >= sg.right() - 1
        elif edge == 'top':
            enter = pos.y() <= sg.top() + 1

        if enter:
            self._restore_from_edge()

    def _start_rehide_timer(self):
        if self._rehide_timer:
            return
        self._rehide_timer = QTimer(self)
        self._rehide_timer.timeout.connect(self._check_rehide)
        self._rehide_timer.start(200)

    def _stop_rehide_timer(self):
        if self._rehide_timer:
            self._rehide_timer.stop()
            self._rehide_timer = None

    def _check_rehide(self):
        if not self._should_rehide or not self._current_edge:
            self._stop_rehide_timer()
            return
        if self._pending_hide:
            return
        cursor = QCursor.pos()
        geo = self.geometry()
        if not geo.contains(cursor):
            self._stop_rehide_timer()
            edge = self._current_edge
            self._hide_at_edge(edge)

    # ---------- 延迟隐藏（吸附后等鼠标离开窗口） ----------

    def _start_pending_hide_timer(self):
        if self._pending_hide_timer:
            return
        self._should_rehide = False
        self._stop_rehide_timer()
        self._pending_hide_timer = QTimer(self)
        self._pending_hide_timer.timeout.connect(self._check_pending_hide)
        self._pending_hide_timer.start(150)

    def _stop_pending_hide_timer(self):
        if self._pending_hide_timer:
            self._pending_hide_timer.stop()
            self._pending_hide_timer = None

    def _check_pending_hide(self):
        if not self._pending_hide:
            self._stop_pending_hide_timer()
            return
        geo = self._pending_hide_geometry or self.geometry()
        if not geo.contains(QCursor.pos()):
            self._stop_pending_hide_timer()
            edge = self._pending_hide_edge
            self._pending_hide = False
            if edge:
                self._hide_at_edge(edge)


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