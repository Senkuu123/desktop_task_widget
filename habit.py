"""
习惯数据模型定义
用于桌面任务小组件的习惯（每日例行）功能
"""

from datetime import datetime, date
from typing import Dict, Any


class Habit:
    """习惯类，表示一个每日例行任务"""

    def __init__(self, content: str, time: str = "08:00", habit_id: int = None):
        self.id = habit_id or self._generate_id()
        self.content = content.strip()
        self.time = time
        self.is_done_today = False
        self.done_date = None
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_id(self) -> int:
        return int(datetime.now().timestamp() * 1000)

    def mark_done_today(self):
        self.is_done_today = True
        self.done_date = date.today().isoformat()

    def mark_undone_today(self):
        self.is_done_today = False
        self.done_date = None

    def toggle_done_today(self):
        if self.is_done_today:
            self.mark_undone_today()
        else:
            self.mark_done_today()

    def check_daily_reset(self):
        today = date.today().isoformat()
        if self.is_done_today and self.done_date != today:
            self.is_done_today = False
            self.done_date = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'time': self.time,
            'is_done_today': self.is_done_today,
            'done_date': self.done_date,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Habit':
        habit = cls(
            content=data['content'],
            time=data.get('time', '08:00'),
            habit_id=data['id'],
        )
        habit.is_done_today = data.get('is_done_today', False)
        habit.done_date = data.get('done_date', None)
        habit.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        habit.check_daily_reset()
        return habit
