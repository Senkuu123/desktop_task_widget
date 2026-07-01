from datetime import datetime, date, timedelta


class WaterReminder:
    def __init__(self):
        self.is_enabled = False
        self.cup_size = 250
        self.reminder_interval = 60
        self.snooze_interval = 30
        self.active_start = "08:00"
        self.active_end = "22:00"
        self.quiet_start = "12:00"
        self.quiet_end = "13:00"
        self.daily_goal = 2000

        self.today_intake = 0
        self.today_date = date.today().isoformat()
        self.next_reminder_time = None
        self.is_completed_today = False
        self.today_logs = []  # [{"time": "HH:MM", "amount": 250, "type": "喝一杯"}, ...]
        self._reminder_notified = False

    def check_daily_reset(self):
        today = date.today().isoformat()
        if self.today_date != today:
            self.today_date = today
            self.today_intake = 0
            self.is_completed_today = False
            self.next_reminder_time = None
            self.today_logs = []
            self._reminder_notified = False

    def add_water(self, ml):
        self.today_intake += ml
        self._reminder_notified = False
        if self.today_intake >= self.daily_goal:
            self.is_completed_today = True
            self.next_reminder_time = None
        else:
            self._schedule_next()

    def add_water_log(self, ml, drink_type):
        self.today_logs.append({
            "time": datetime.now().strftime("%H:%M"),
            "amount": ml,
            "type": drink_type,
        })

    def _schedule_next(self):
        self.next_reminder_time = datetime.now() + timedelta(minutes=self.reminder_interval)

    def snooze(self, minutes=None):
        if minutes is None:
            minutes = self.snooze_interval
        self.next_reminder_time = datetime.now() + timedelta(minutes=minutes)
        self._reminder_notified = False

    def update_reminder(self):
        if not self.is_enabled:
            return None
        if self.is_completed_today:
            return None
        if not self._is_active_hours():
            return None
        if self._is_quiet_hours():
            return None

        now = datetime.now()
        if self.next_reminder_time is None:
            self.next_reminder_time = now + timedelta(minutes=self.reminder_interval)
            return None

        diff = (self.next_reminder_time - now).total_seconds()

        # 已过期的提醒不再弹出，直接安排下一次
        if diff < 0:
            self._reminder_notified = False
            self.next_reminder_time = now + timedelta(minutes=self.reminder_interval)
            return None

        # 剩余10秒内触发提醒（只触发一次）
        if diff <= 10 and not self._reminder_notified:
            self._reminder_notified = True
            self.next_reminder_time = now + timedelta(minutes=self.reminder_interval)
            return self._make_reminder_text()
        return None

    def _make_reminder_text(self):
        remaining = max(0, self.daily_goal - self.today_intake)
        cups = remaining / self.cup_size if self.cup_size > 0 else 0
        return f"该喝水了！今日还差{remaining}ml（约{cups:.1f}杯）"

    def _is_active_hours(self):
        now_time = datetime.now().strftime("%H:%M")
        if self.active_start <= self.active_end:
            return self.active_start <= now_time <= self.active_end
        return now_time >= self.active_start or now_time <= self.active_end

    def _is_quiet_hours(self):
        now_time = datetime.now().strftime("%H:%M")
        if self.quiet_start <= self.quiet_end:
            return self.quiet_start <= now_time <= self.quiet_end
        return now_time >= self.quiet_start or now_time <= self.quiet_end

    def _parse_time_today(self, time_str):
        h, m = map(int, time_str.split(":"))
        return datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

    def get_next_reminder_display(self):
        if not self.is_enabled:
            return "未启用", ""
        if self.is_completed_today:
            return "目标完成", ""
        if not self._is_active_hours():
            return "未到开启时段", ""
        if self._is_quiet_hours():
            quiet_range = f"{self.quiet_start}-{self.quiet_end}"
            return "静音时段", quiet_range

        now = datetime.now()
        if self.next_reminder_time is None:
            self.next_reminder_time = now + timedelta(minutes=self.reminder_interval)

        diff = (self.next_reminder_time - now).total_seconds()
        if diff <= 0:
            return self.next_reminder_time.strftime("%H:%M"), ""
        mins = int(diff / 60)
        if mins >= 60:
            h = mins // 60
            m = mins % 60
            time_str = f"{h}小时{m}分" if m > 0 else f"{h}小时"
        else:
            time_str = f"{mins}分钟"
        return self.next_reminder_time.strftime("%H:%M"), time_str

    def to_dict(self):
        d = {
            'is_enabled': self.is_enabled,
            'cup_size': self.cup_size,
            'reminder_interval': self.reminder_interval,
            'snooze_interval': self.snooze_interval,
            'active_start': self.active_start,
            'active_end': self.active_end,
            'quiet_start': self.quiet_start,
            'quiet_end': self.quiet_end,
            'daily_goal': self.daily_goal,
            'today_intake': self.today_intake,
            'today_date': self.today_date,
            'is_completed_today': self.is_completed_today,
            'today_logs': self.today_logs,
        }
        if self.next_reminder_time:
            d['next_reminder_time'] = self.next_reminder_time.strftime("%Y-%m-%d %H:%M:%S")
        return d

    @classmethod
    def from_dict(cls, data):
        w = cls()
        w.is_enabled = data.get('is_enabled', False)
        w.cup_size = data.get('cup_size', 250)
        w.reminder_interval = data.get('reminder_interval', 60)
        w.snooze_interval = data.get('snooze_interval', 30)
        w.active_start = data.get('active_start', '08:00')
        w.active_end = data.get('active_end', '22:00')
        w.quiet_start = data.get('quiet_start', '12:00')
        w.quiet_end = data.get('quiet_end', '13:00')
        w.daily_goal = data.get('daily_goal', 2000)
        w.today_intake = data.get('today_intake', 0)
        w.today_date = data.get('today_date', date.today().isoformat())
        w.is_completed_today = data.get('is_completed_today', False)
        w.today_logs = data.get('today_logs', [])
        if 'next_reminder_time' in data:
            try:
                w.next_reminder_time = datetime.strptime(data['next_reminder_time'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                w.next_reminder_time = None
        w.check_daily_reset()
        return w
