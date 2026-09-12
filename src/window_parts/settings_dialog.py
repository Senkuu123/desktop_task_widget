from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QDialog, QSlider, QGroupBox
from PyQt5.QtCore import Qt
from autostart_manager import AutoStartManager, check_startup_permission


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.autostart_manager = AutoStartManager()
        self.initUI()
        
    def initUI(self):
        """初始化设置界面"""
        self.setWindowTitle("设置")
        self.setWindowModality(Qt.ApplicationModal)
        # self.setFixedSize(300, 420)  # 注释掉固定尺寸

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)

        # 创建设置组
        settings = [
            ("窗口背景透明度", "opacity_slider", 10, 100, int(self.parent_window.window_background_opacity * 100)),
            ("文字大小", "font_slider", 8, 20, self.parent_window.current_font_size),
            ("文字透明度", "font_opacity_slider", 10, 100, self.parent_window.current_font_opacity)
        ]
        
        for title, slider_name, min_val, max_val, current_val in settings:
            group = QGroupBox(title)
            group_layout = QVBoxLayout()
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(current_val)
            
            label = QLabel(f"{current_val}{'%' if 'opacity' in slider_name else 'pt'}")
            
            slider.valueChanged.connect(lambda value, lbl=label, unit='%' if 'opacity' in slider_name else 'pt': lbl.setText(f"{value}{unit}"))
            
            group_layout.addWidget(slider)
            group_layout.addWidget(label)
            group.setLayout(group_layout)
            layout.addWidget(group)
            
            setattr(self, slider_name, slider)
            setattr(self, slider_name.replace('slider', 'label'), label)
        
        # 添加开机自启动选项
        autostart_group = self._create_autostart_group()
        layout.addWidget(autostart_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setMinimumSize(300, 380)

    def _create_autostart_group(self):
        """创建开机自启动设置组"""
        group = QGroupBox("开机自启动")
        group_layout = QVBoxLayout()
        
        # 创建复选框和状态标签
        checkbox_layout = QHBoxLayout()
        
        self.autostart_checkbox = QCheckBox("开机时自动启动")
        self.autostart_checkbox.setChecked(self.autostart_manager.is_enabled())
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)

        # 设置复选框字体（增大字体以适应高DPI）
        checkbox_font = self.autostart_checkbox.font()
        checkbox_font.setPointSize(self.font().pointSize())
        self.autostart_checkbox.setFont(checkbox_font)

        self.autostart_status_label = QLabel()
        self.autostart_status_label.setStyleSheet("color: #666;")
        self.update_autostart_status()
        
        checkbox_layout.addWidget(self.autostart_checkbox)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.autostart_status_label)
        
        # 权限提示
        permission_layout = QHBoxLayout()
        self.permission_label = QLabel()
        self.permission_label.setStyleSheet("color: #FF6B6B;")
        self.update_permission_status()
        
        permission_layout.addWidget(self.permission_label)
        permission_layout.addStretch()
        
        group_layout.addLayout(checkbox_layout)
        group_layout.addLayout(permission_layout)
        group.setLayout(group_layout)
        
        return group

    def showEvent(self, event):
        """显示时调整大小"""
        super().showEvent(event)
        self.adjustSize()
        
        # 确保对话框不会太大
        screen = QApplication.primaryScreen().availableGeometry()
        if self.width() > screen.width() * 0.7:
            self.setFixedWidth(int(screen.width() * 0.7))
        if self.height() > screen.height() * 0.7:
            self.setFixedHeight(int(screen.height() * 0.7))

    def update_autostart_status(self):
        """更新开机自启动状态显示"""
        status_text = self.autostart_manager.get_status_text()
        self.autostart_status_label.setText(status_text)

        if self.autostart_manager.is_enabled():
            self.autostart_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.autostart_status_label.setStyleSheet("color: #666;")

    def on_autostart_changed(self, state):
        """开机自启动复选框状态改变"""
        try:
            if state == Qt.Checked:
                success = self.autostart_manager.enable()
            else:
                success = self.autostart_manager.disable()
            
            self.update_autostart_status()
            
            if not success:
                # 如果操作失败，恢复原来的状态
                self.autostart_checkbox.setChecked(not (state == Qt.Checked))
                self.update_autostart_status()
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
            # 出错时恢复原来的状态
            self.autostart_checkbox.setChecked(self.autostart_manager.is_enabled())
    
    def update_autostart_status(self):
        """更新开机自启动状态显示"""
        status_text = self.autostart_manager.get_status_text()
        self.autostart_status_label.setText(status_text)

        if self.autostart_manager.is_enabled():
            self.autostart_status_label.setStyleSheet("color: #4CAF50; font-size: 10pt;")
        else:
            self.autostart_status_label.setStyleSheet("color: #666; font-size: 10pt;")

    def update_permission_status(self):
        """更新权限状态显示"""
        if not check_startup_permission():
            self.permission_label.setText("⚠️ 可能需要管理员权限")
        else:
            self.permission_label.setText("")
        
    def get_settings(self):
        """获取设置"""
        return {
            'opacity': self.opacity_slider.value() / 100.0,
            'font_size': self.font_slider.value(),
            'font_opacity': self.font_opacity_slider.value()
        }
