from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QCursor


class WindowInteractionMixin:
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

        # 点击、缩放和拖动松手后都按当前位置续接隐藏，避免点击清掉待隐藏状态。
        self._schedule_edge_hide()

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

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._schedule_edge_hide)

    def leaveEvent(self, event):
        """鼠标离开窗口事件 - 优化版本"""
        super().leaveEvent(event)
        
        # 鼠标离开时立即恢复默认光标
        self.setCursor(Qt.ArrowCursor)
        self.last_cursor_shape = Qt.ArrowCursor
        self.last_cursor_pos = None

    def closeEvent(self, event):
        """窗口关闭事件 - 保存设置"""
        self.note_hotkey.close()
        self.note_actions.close()
        if self.note_dialog:
            self.note_dialog.close()
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
        if self.current_page == 'notes':
            self.resize_note_cards()
            return
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

    def eventFilter(self, obj, event):
        """事件过滤器"""
        if (event.type() == event.Resize and hasattr(self, 'task_list_widget')
                and obj is self.task_list_widget.viewport() and self.current_page == 'notes'):
            QTimer.singleShot(0, self.resize_note_cards)
        if event.type() == event.WindowDeactivate:
            self.task_list_widget.clearSelection()
        return super().eventFilter(obj, event)
