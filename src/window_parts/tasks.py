from datetime import datetime
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from quick_notes.card import NoteCard
from task import Task
from storage import save_tasks_to_json, load_tasks_from_json, archive_task
from add_task_dialog import AddTaskDialog
from edit_task_dialog import EditTaskDialog
from .task_item import TaskListWidgetItem


class WindowTasksMixin:
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
        if self.current_page in ('tasks', 'notes'):
            self.last_content_page = self.current_page
        icon, label = ('📋', '待办事项') if self.last_content_page == 'tasks' else ('📝', '快捷便签')
        target = '快捷便签' if self.last_content_page == 'tasks' else '待办事项'
        self.content_page_btn.setText(icon)
        self.content_page_btn.setAccessibleName(label)
        self.content_page_btn.setToolTip(f'返回{label}' if self.current_page in ('water', 'habits') else f'切换到{target}')
        if self.current_page in ('water', 'habits'):
            self.last_water_page = self.current_page
        is_habits = self.last_water_page == 'habits'
        self.water_page_btn.setText('🔄' if is_habits else '')
        self.water_page_btn.setIcon(QIcon() if is_habits else self.create_water_cup_icon())
        self.water_page_btn.setAccessibleName('习惯列表' if is_habits else '饮水小助手')
        self.water_page_btn.setToolTip(('切换到饮水小助手' if is_habits else '切换到习惯列表')
                                     if self.current_page in ('water', 'habits') else ('打开习惯列表' if is_habits else '打开饮水小助手'))
        self.task_list_widget.setVisible(self.current_page != 'water')
        self.water_widget.setVisible(self.current_page == 'water')
        if self.current_page != 'notes':
            self.note_cards.clear()
            self.notes_status.hide()
        self.task_list_widget.setWordWrap(self.current_page == 'notes')
        self.task_list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel if self.current_page == 'notes' else QListWidget.ScrollPerItem)
        self.task_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff if self.current_page == 'notes' else Qt.ScrollBarAsNeeded)
        if self.current_page == 'notes':
            self.water_widget.setVisible(False)
            self.refresh_notes_display()
            return
        if self.current_page == 'water':
            self.water_widget.update_countdown()
            self.water_widget.fit_available_height()
            return
        if self.current_page == 'habits':
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
        if self.current_page == 'notes':
            card = self.task_list_widget.itemWidget(item)
            if isinstance(card, NoteCard):
                card.begin_edit()
            return
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

    def load_tasks(self):
        """加载任务"""
        self.tasks = load_tasks_from_json()

    def save_tasks(self):
        """保存任务"""
        save_tasks_to_json(self.tasks)
