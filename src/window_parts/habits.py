from datetime import date
from PyQt5.QtWidgets import QListWidgetItem, QDialog
from PyQt5.QtCore import Qt
from habit import Habit
from storage import save_habits_to_json, save_habit_log, load_habit_log
from add_habit_dialog import AddHabitDialog
from .task_item import TaskListWidgetItem


class WindowHabitsMixin:
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
