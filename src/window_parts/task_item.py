from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal


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
        self.label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
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
        from .window import TransparentTaskWindow

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
