import ctypes
from datetime import datetime


class WindowNotificationsMixin:
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
