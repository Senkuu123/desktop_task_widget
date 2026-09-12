from datetime import datetime, date
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QSizePolicy, QScrollArea
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor
from storage import save_water_reminder, save_water_log, load_water_log
from .water_settings import _WaterSettingsDialog


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
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(10, 6, 10, 6)
        self.panel_layout.setSpacing(0)
        self.core = QWidget()
        root = QVBoxLayout(self.core)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        self.panel_layout.addWidget(self.core)

        # Title row
        top = QHBoxLayout()
        top.setSpacing(6)
        title = QLabel("今日饮水进度")
        self.title_label = title
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
        self.summary_separator = sep
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
        self.log_container.setMinimumHeight(0)
        self.log_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        log_inner = QVBoxLayout(self.log_container)
        log_inner.setContentsMargins(0, 0, 0, 0)
        log_inner.setSpacing(0)
        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_scroll.setMinimumHeight(0)
        self.log_scroll.setMaximumHeight(96)
        self.log_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; border-radius: 6px; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 0; border-radius: 4px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0); border-radius: 4px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: rgba(120, 120, 120, 220); }
            QScrollBar::handle:vertical:pressed { background: rgba(140, 140, 140, 255); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        self.log_entries_widget = QWidget()
        self.log_entries_layout = QVBoxLayout(self.log_entries_widget)
        self.log_entries_layout.setContentsMargins(8, 6, 8, 6)
        self.log_entries_layout.setSpacing(0)
        self.log_scroll.setWidget(self.log_entries_widget)
        log_inner.addWidget(self.log_scroll)
        self.panel_layout.addWidget(self.log_container, 1)
        self.panel_layout.addStretch(0)

        self._update_all()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_available_height()

    def fit_available_height(self):
        if not hasattr(self, 'log_container'):
            return
        # 核心操作区不参与压缩，先让记录区缩小，极小时收起次要统计。
        for widget in (self.intake_label, self.progress_stats, self.summary_separator):
            widget.show()
        self.core.layout().invalidate()
        available = max(0, self.height() - 12)
        if self.core.sizeHint().height() > available:
            for widget in (self.intake_label, self.progress_stats, self.summary_separator):
                widget.hide()
            self.core.layout().invalidate()
        self.core.setFixedHeight(self.core.sizeHint().height())

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
                container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                layout.addWidget(container)
                sep = QLabel()
                sep.setFixedHeight(1)
                sep.setStyleSheet("background: rgba(255,255,255,0.08);")
                layout.addWidget(sep)
        layout.addStretch()
