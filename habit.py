"""
习惯数据模型定义
用于桌面任务小组件的习惯（每日例行）功能
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional


class Habit:
    """习惯类，表示一个每日例行任务"""

    FREQ_MODE_DAILY = "daily"
    FREQ_MODE_WEEKLY = "weekly"
    FREQ_MODE_INTERVAL = "interval"

    MODE_LABELS = {"daily": "按天", "weekly": "按周", "interval": "按时间间隔"}
    DAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]

    def __init__(self, content: str, time: str = "08:00", habit_id: int = None,
                 freq_mode: str = "daily", weekdays: list = None,
                 weekly_target: int = 3, interval_days: int = 2):
        self.id = habit_id or self._generate_id()
        self.content = content.strip()
        self.time = time
        self.freq_mode = freq_mode
        self.weekdays = weekdays if weekdays is not None else [0, 1, 2, 3, 4]
        self.weekly_target = weekly_target
        self.interval_days = interval_days
        self.is_archived = False
        self.is_done_today = False
        self.done_date = None
        self.weekly_completed = 0
        self.current_streak = 0
        self.last_completed_date = None
        self.week_completed_dates = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_id(self) -> int:
        return int(datetime.now().timestamp() * 1000)

    def mark_done_today(self):
        self.is_done_today = True
        self.done_date = date.today().isoformat()

    def mark_undone_today(self):
        self.is_done_today = False
        self.done_date = None

    def archive(self):
        self.is_archived = True

    def unarchive(self):
        self.is_archived = False

    def is_daily_mode(self) -> bool:
        return self.freq_mode == self.FREQ_MODE_DAILY

    def is_weekly_mode(self) -> bool:
        return self.freq_mode == self.FREQ_MODE_WEEKLY

    def is_interval_mode(self) -> bool:
        return self.freq_mode == self.FREQ_MODE_INTERVAL

    def get_freq_label(self) -> str:
        if self.is_daily_mode():
            wd_abbr = "".join([self.DAY_NAMES[d] for d in (self.weekdays or [])])
            return f"周{wd_abbr}" if wd_abbr else "每天"
        elif self.is_weekly_mode():
            return f"{self.weekly_completed}/{self.weekly_target}次 本周"
        else:
            return f"每{self.interval_days}天 连续{self.current_streak}天"

    def is_active_today(self) -> bool:
        if self.freq_mode == self.FREQ_MODE_DAILY:
            return date.today().weekday() in (self.weekdays or [])
        elif self.freq_mode == self.FREQ_MODE_WEEKLY:
            return True
        elif self.freq_mode == self.FREQ_MODE_INTERVAL:
            if self.last_completed_date is None:
                return True
            last_date = date.fromisoformat(self.last_completed_date)
            return (date.today() - last_date).days >= self.interval_days
        return False

    def check_daily_reset(self):
        today = date.today().isoformat()
        if self.is_done_today and self.done_date != today:
            self.is_done_today = False
            self.done_date = None

    def check_weekly_reset(self) -> bool:
        today = date.today()
        if not self.week_completed_dates:
            if self.weekly_completed > 0:
                self.weekly_completed = 0
                return True
            return False
        last_date = date.fromisoformat(self.week_completed_dates[-1])
        if today.isocalendar()[1] != last_date.isocalendar()[1] or today.year != last_date.year:
            self.weekly_completed = 0
            self.week_completed_dates = []
            return True
        return False

    def record_completion(self) -> Optional[str]:
        self.mark_done_today()
        today = date.today().isoformat()

        if self.freq_mode == self.FREQ_MODE_DAILY:
            if today not in self.week_completed_dates:
                self.week_completed_dates.append(today)
            if self._is_daily_week_complete():
                return f"恭喜！本周{self.content}已养成！"
            return None

        elif self.freq_mode == self.FREQ_MODE_WEEKLY:
            if today not in self.week_completed_dates:
                self.week_completed_dates.append(today)
                self.weekly_completed = len(self.week_completed_dates)
            if self.weekly_completed >= self.weekly_target:
                return f"恭喜！本周{self.content}已养成！"
            return None

        elif self.freq_mode == self.FREQ_MODE_INTERVAL:
            if self.last_completed_date == today:
                return f"已坚持打卡{self.content} {self.current_streak}天！"
            prev_date = self.last_completed_date
            self.last_completed_date = today
            if prev_date:
                last = date.fromisoformat(prev_date)
                expected_days = (date.today() - last).days
                if expected_days == self.interval_days:
                    self.current_streak += 1
                else:
                    self.current_streak = 1
            else:
                self.current_streak = 1
            return f"已坚持打卡{self.content} {self.current_streak}天！"
        return None

    def undo_completion(self):
        self.mark_undone_today()
        today = date.today().isoformat()

        if self.freq_mode == self.FREQ_MODE_WEEKLY:
            if today in self.week_completed_dates:
                self.week_completed_dates.remove(today)
                self.weekly_completed = len(self.week_completed_dates)
        elif self.freq_mode == self.FREQ_MODE_DAILY:
            if today in self.week_completed_dates:
                self.week_completed_dates.remove(today)
        elif self.freq_mode == self.FREQ_MODE_INTERVAL:
            if self.current_streak > 0:
                self.current_streak -= 1
                self.last_completed_date = None

    def _is_daily_week_complete(self) -> bool:
        if self.freq_mode != self.FREQ_MODE_DAILY or not self.weekdays:
            return False
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        for offset in range(7):
            d = monday + timedelta(days=offset)
            if d > today:
                break
            if d.weekday() in self.weekdays:
                if d.isoformat() not in self.week_completed_dates:
                    return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'time': self.time,
            'freq_mode': self.freq_mode,
            'weekdays': self.weekdays,
            'weekly_target': self.weekly_target,
            'interval_days': self.interval_days,
            'is_archived': self.is_archived,
            'is_done_today': self.is_done_today,
            'done_date': self.done_date,
            'weekly_completed': self.weekly_completed,
            'current_streak': self.current_streak,
            'last_completed_date': self.last_completed_date,
            'week_completed_dates': self.week_completed_dates,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Habit':
        habit = cls(
            content=data['content'],
            time=data.get('time', '08:00'),
            habit_id=data['id'],
            freq_mode=data.get('freq_mode', 'daily'),
            weekdays=data.get('weekdays'),
            weekly_target=data.get('weekly_target', 3),
            interval_days=data.get('interval_days', 2),
        )
        habit.is_archived = data.get('is_archived', False)
        habit.is_done_today = data.get('is_done_today', False)
        habit.done_date = data.get('done_date', None)
        habit.weekly_completed = data.get('weekly_completed', 0)
        habit.current_streak = data.get('current_streak', 0)
        habit.last_completed_date = data.get('last_completed_date', None)
        habit.week_completed_dates = data.get('week_completed_dates', [])
        habit.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        habit.check_daily_reset()
        habit.check_weekly_reset()
        return habit
