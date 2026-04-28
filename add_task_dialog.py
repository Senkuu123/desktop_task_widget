"""
桌面任务小组件 - 添加任务对话框
用于输入新任务的内容、时间和优先级
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QDateTimeEdit, QComboBox, QPushButton,
                             QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
from task import Task


class AddTaskDialog(QDialog):
    """添加任务对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 设置对话框属性
        self.setWindowTitle("添加新任务")
        self.setWindowModality(Qt.ApplicationModal)  # 模态对话框
        self.setFixedSize(350, 250)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QLabel {
                font-size: 12pt;
                color: #333;
                font-weight: bold;
            }
            QLineEdit, QDateTimeEdit, QComboBox {
                font-size: 11pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                font-size: 11pt;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#okButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#okButton:hover {
                background-color: #45a049;
            }
            QPushButton#cancelButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #da190b;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 1. 任务内容输入框
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("请输入任务内容...")
        self.content_edit.setMinimumHeight(35)
        form_layout.addRow("任务内容:", self.content_edit)
        
        # 2. 截止时间选择器
        self.deadline_edit = QDateTimeEdit()
        # 设置默认时间为当前时间加一小时
        current_time = QDateTime.currentDateTime()
        one_hour_later = current_time.addSecs(3600)  # 添加3600秒（1小时）
        self.deadline_edit.setDateTime(one_hour_later)
        self.deadline_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.deadline_edit.setMinimumHeight(35)
        self.deadline_edit.setCalendarPopup(True)  # 显示日历弹窗
        form_layout.addRow("截止时间:", self.deadline_edit)
        
        # 3. 优先级选择下拉框
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["P1 - 重要/中", "P2 - 普通/低", "P3 - 轻微/待定"])
        self.priority_combo.setCurrentIndex(0)  # 默认P1
        self.priority_combo.setMinimumHeight(35)
        form_layout.addRow("优先级:", self.priority_combo)
        
        # 添加表单布局到主布局
        main_layout.addLayout(form_layout)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        
        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setObjectName("okButton")
        self.ok_button.clicked.connect(self.accept_task)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 设置Tab键顺序
        self.setTabOrder(self.content_edit, self.deadline_edit)
        self.setTabOrder(self.deadline_edit, self.priority_combo)
        self.setTabOrder(self.priority_combo, self.ok_button)
        self.setTabOrder(self.ok_button, self.cancel_button)
        
        # 默认焦点在内容输入框
        self.content_edit.setFocus()
        
    def accept_task(self):
        """确认添加任务"""
        # 验证输入
        content = self.content_edit.text().strip()
        if not content:
            QMessageBox.warning(self, "输入错误", "请输入任务内容！")
            self.content_edit.setFocus()
            return
            
        # 验证截止时间
        deadline = self.deadline_edit.dateTime()
        if deadline <= QDateTime.currentDateTime():
            QMessageBox.warning(self, "输入错误", "截止时间必须晚于当前时间！")
            self.deadline_edit.setFocus()
            return
            
        # 接受对话框，关闭窗口
        self.accept()
        
    def get_task_data(self):
        """获取任务数据"""
        if self.result() == QDialog.Accepted:
            content = self.content_edit.text().strip()
            deadline = self.deadline_edit.dateTime().toString("yyyy-MM-dd hh:mm")
            # 获取优先级：P1=1, P2=2, P3=3
            priority_map = {0: 1, 1: 2, 2: 3}
            priority = priority_map[self.priority_combo.currentIndex()]
            
            return content, deadline, priority
        else:
            return None, None, None
            
    def reset_form(self):
        """重置表单"""
        self.content_edit.clear()
        # 重置时也使用当前时间加一小时
        current_time = QDateTime.currentDateTime()
        one_hour_later = current_time.addSecs(3600)  # 添加3600秒（1小时）
        self.deadline_edit.setDateTime(one_hour_later)
        self.priority_combo.setCurrentIndex(1)
        self.content_edit.setFocus()


# 测试代码
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = AddTaskDialog()
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        content, deadline, priority = dialog.get_task_data()
        print(f"添加任务: {content}")
        print(f"截止时间: {deadline}")
        print(f"优先级: {priority}")
        
        # 创建任务对象测试
        task = Task(content, deadline, priority)
        print(f"任务对象: {task}")
    else:
        print("用户取消了添加任务")
        
    sys.exit()