from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QDialog, QGroupBox, QSpinBox, QTimeEdit
from PyQt5.QtCore import Qt, QTime


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
