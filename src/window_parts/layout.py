from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QIcon, QPixmap, QPainterPath
from .water_widgets import WaterDisplayWidget
from .settings_dialog import SettingsDialog
from .folder_shortcuts import FolderShortcuts
from .task_folder_splitter import TaskFolderSplitter
from ui_styles import SCROLLBAR_STYLE


class WindowLayoutMixin:
    def initUI(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部栏
        self.drag_area = self._create_top_bar()
        
        # 任务列表容器
        self.list_container = QWidget()
        list_layout = QVBoxLayout(self.list_container)
        list_layout.setContentsMargins(5, 5, 5, 5)  # 容器边距
        list_layout.setSpacing(0)  # 容器内无间距

        # 饮水独立页，习惯任务使用下方独立列表
        self.water_widget = WaterDisplayWidget(self.water_reminder, self)
        self.water_widget.setVisible(False)
        list_layout.addWidget(self.water_widget, 1)

        self.notes_status = QLabel()
        self.notes_status.setWordWrap(True)
        self.notes_status.setStyleSheet('color: #ddd; padding: 6px; font-size: 10pt;')
        self.notes_status.hide()
        list_layout.addWidget(self.notes_status)

        self.task_list_widget = QListWidget()
        # 为列表控件设置唯一ID，防止样式继承冲突
        self.task_list_widget.setObjectName("TaskListWidget")
        self.task_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 启用水平滚动条的自动显示
        self.task_list_widget.setHorizontalScrollMode(QListWidget.ScrollPerPixel)
        self.task_list_widget.setWrapping(False)  # 禁用自动换行
        self.task_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.task_list_widget.viewport().installEventFilter(self)
        
        # 设置列表控件的边距，确保与任务项边距一致
        self.task_list_widget.setContentsMargins(0, 0, 0, 0)
        
        self.task_folder_splitter = TaskFolderSplitter(self.task_area_height, self.list_container)
        self.task_list_widget.setMinimumHeight(40)
        self.task_folder_splitter.addWidget(self.task_list_widget)
        self.folder_shortcuts = FolderShortcuts(
            self.folder_paths, self.folders_collapsed, self.list_container,
            sort_key=self.folder_sort_key, sort_desc=self.folder_sort_desc)
        self.task_folder_splitter.addWidget(self.folder_shortcuts)
        list_layout.addWidget(self.task_folder_splitter, 1)
        self.folder_shortcuts.changed.connect(self.task_folder_splitter.apply_allocation)
        self.folder_shortcuts.changed.connect(self.save_window_settings)
        self.task_folder_splitter.allocation_changed.connect(self.save_window_settings)
        
        main_layout.addWidget(self.drag_area)
        main_layout.addWidget(self.list_container)
        self.setLayout(main_layout)
        
        # 设置鼠标跟踪
        for widget in [self, self.drag_area, self.list_container, self.task_list_widget]:
            widget.setMouseTracking(True)
        
        # 定时器和事件过滤器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_task_display)
        self.refresh_timer.start(60000)

        # 截止时间提醒定时器（每30秒检查一次）
        self.deadline_notify_timer = QTimer()
        self.deadline_notify_timer.timeout.connect(self.check_deadline_notifications)
        self.deadline_notify_timer.start(30000)

        self.installEventFilter(self)
        self.update_window_style()
        
        # 延迟执行Windows特定设置
        self.setup_windows_specific()

    def _create_top_bar(self):
        """创建顶部栏"""
        drag_area = QWidget()
        drag_area.setFixedHeight(30)

        layout = QHBoxLayout(drag_area)
        layout.setContentsMargins(5, 0, 5, 0)

        layout.addStretch()

        self.content_page_btn = QPushButton('📋')
        self.content_page_btn.setFixedSize(25, 25)
        self.content_page_btn.clicked.connect(self.toggle_content_page)
        self.water_page_btn = QPushButton()
        self.water_page_btn.setFixedSize(25, 25)
        self.water_page_btn.setToolTip('饮水小助手')
        self.water_page_btn.setAccessibleName('饮水小助手')
        self.water_page_btn.clicked.connect(self.toggle_water_page)
        self.water_page_btn.setIcon(self.create_water_cup_icon())

        # 按钮配置
        buttons = [
            ("📍", "取消置顶", self.toggle_window_topmost, True),  # 置顶按钮
            ("➕", None, self.show_add_dialog, False),  # 添加按钮
            (None, None, None, None),  # 占位：切换按钮在此处插入
            ("⚙️", None, self.show_settings_dialog, False)   # 设置按钮
        ]
        
        for icon, tooltip, callback, checkable in buttons:
            if icon is None:
                layout.addWidget(self.content_page_btn)
                layout.addWidget(self.water_page_btn)
                continue
            btn = QPushButton(icon)
            btn.setFixedSize(25, 25)
            btn.setCheckable(checkable)
            if checkable:
                btn.setChecked(True)
            if tooltip:
                btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            
            if icon == "📍":
                self.pin_button = btn
            elif icon == "➕":
                self.add_button = btn
            elif icon == "⚙️":
                self.settings_button = btn
        
        return drag_area

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            self.window_background_opacity = settings['opacity']
            self.current_font_size = settings['font_size']
            self.current_font_opacity = settings['font_opacity']
            self.update_window_style()
            self.refresh_task_display()

    def update_window_style(self):
        """更新窗口样式"""
        bg_alpha = int(self.window_background_opacity * 255)
        font_alpha = int(self.current_font_opacity * 255 / 100)

        # 1. 设置列表控件的基本样式，使用ID选择器
        list_widget_style = f"""
            #TaskListWidget {{
                background: transparent;
                color: rgba(255, 255, 255, {font_alpha});
                border: none;
                font-size: {self.current_font_size}pt;
                font-family: 'Microsoft YaHei', sans-serif;
                outline: none;
            }}
            #TaskListWidget::item {{
                border-bottom: 1px solid rgba(255, 255, 255, {max(15, font_alpha//4)});
                background: transparent;
                padding: 0px;
                border: none;
            }}
            #TaskListWidget::item:selected {{
                background: transparent;
            }}
        """
        self.task_list_widget.setStyleSheet(list_widget_style)
        self.folder_shortcuts.apply_style(self.current_font_size, self.current_font_opacity)

        # 2. 核心修改：设置VS Code风格且支持悬停显示的滚动条样式
        scrollbar_style = SCROLLBAR_STYLE
        # 直接应用样式到滚动条对象
        self.task_list_widget.verticalScrollBar().setStyleSheet(scrollbar_style)
        self.task_list_widget.horizontalScrollBar().setStyleSheet(scrollbar_style)
        # 确保滚动条策略设置为"需要时出现"，这是悬停显示的基础
        self.task_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 3. 其他控件的样式保持不变
        button_style = f"""
            QPushButton {{
                background: transparent;
                color: rgba(255, 255, 255, {font_alpha});
                border: none;
                font-size: 12pt;
                font-weight: 375;  /* 轻微加粗，优化字体渲染效果 */
                width: 25px;
                height: 25px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 50);
                border-radius: 3px;
            }}
            QPushButton:focus {{
                outline: none;  /* 仅移除焦点轮廓，不影响选中状态 */
            }}
        """
        
        self.drag_area.setStyleSheet(f"background: transparent; border-top-left-radius: 5px; border-top-right-radius: 5px;")
        self.list_container.setStyleSheet(f"background: transparent;")
        
        for btn in [self.add_button, self.pin_button, self.settings_button, self.content_page_btn, self.water_page_btn]:
            btn.setStyleSheet(button_style)

        # 饮水模块按钮样式
        if hasattr(self, 'water_widget') and self.water_widget:
            water_btn_style = f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 15);
                    color: rgba(255, 255, 255, {font_alpha});
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 9pt;
                }}
                QPushButton:hover {{ background: rgba(255, 255, 255, 30); }}
            """
            for btn in self.water_widget.findChildren(QPushButton):
                if btn.text() in ("喝一杯", "喝半杯", "抿一口", "稍后"):
                    btn.setStyleSheet(water_btn_style)

        # 4. 更新所有任务项的样式和布局，并立即刷新任务项宽度
        self._update_all_task_items_style()
        self._update_task_items_layout()
        # 立即强制更新一次任务项宽度，解决初始显示或缩放后可能出现的截断问题
        QTimer.singleShot(0, self.update_task_item_widths)
        
        # 更新所有任务项的样式和布局
        self._update_all_task_items_style()
        self._update_task_items_layout()

    def _update_all_task_items_style(self):
        """更新所有任务项的样式"""
        for task_id, task_widget in self.task_widgets.items():
            if hasattr(task_widget, 'update_text_style'):
                task_widget.update_text_style()
            if hasattr(task_widget, '_update_task_background'):
                task_widget._update_task_background()

    def _update_task_items_layout(self):
        """更新任务项布局，确保高度适应字体大小"""
        if self.task_list_widget.count() > 0:
            for i in range(self.task_list_widget.count()):
                item = self.task_list_widget.item(i)
                widget = self.task_list_widget.itemWidget(item)
                if widget:
                    # 更新项的大小提示
                    item.setSizeHint(widget.sizeHint())
            
            # 强制刷新列表视图
            self.task_list_widget.updateGeometry()
            self.task_list_widget.update()

    @staticmethod
    def create_water_cup_icon():
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        # 图标按几何中心排布，旁边emoji按字体基线排布；向下补偿约1个逻辑像素。
        painter.translate(0, 2.5)
        water = QPainterPath()
        water.moveTo(11, 19)
        water.quadTo(16, 16, 21, 19)
        water.quadTo(26, 21, 29, 18)
        water.lineTo(26, 33)
        water.lineTo(14, 33)
        water.closeSubpath()
        painter.fillPath(water, QColor('#62b9ee'))
        glass = QPainterPath()
        glass.moveTo(9, 7)
        glass.lineTo(13, 34)
        glass.quadTo(20, 37, 27, 34)
        glass.lineTo(31, 7)
        glass.closeSubpath()
        painter.setPen(QPen(QColor('#e1ecf2'), 2.5))
        painter.drawPath(glass)
        painter.end()
        return QIcon(pixmap)

    def toggle_water_page(self):
        if self.current_page == 'water':
            self.show_page('habits')
        elif self.current_page == 'habits':
            self.show_page('water')
        else:
            self.show_page(self.last_water_page)

    def toggle_content_page(self):
        if self.current_page in ('water', 'habits'):
            self.show_page(self.last_content_page)
        else:
            self.show_page('notes' if self.current_page == 'tasks' else 'tasks')

    def show_page(self, page):
        if page == 'notes':
            self.load_notes()
        if self.current_page == page:
            if page == 'notes':
                self.refresh_task_display()
            return
        self.current_page = page
        self.refresh_task_display()

    def show_add_dialog(self):
        if self.current_page == 'notes':
            self.show_quick_note()
        elif self.current_page == 'tasks':
            self.show_add_task_dialog()
        elif self.current_page == 'water':
            self.water_widget.show_settings()
        else:
            self.show_add_habit_dialog()
