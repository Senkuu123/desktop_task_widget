"""
桌面任务小组件 - 编辑任务对话框
用于编辑任务的内容、时间和优先级
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QDateTimeEdit, QComboBox, QPushButton,
                             QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt, QDateTime


class EditTaskDialog(QDialog):
    """编辑任务对话框"""
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 设置对话框属性
        self.setWindowTitle("编辑任务")
        self.setWindowModality(Qt.ApplicationModal)  # 模态对话框
        self.setFixedSize(400, 300)
        
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
            QPushButton#saveButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#saveButton:hover {
                background-color: #45a049;
            }
            QPushButton#deleteButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton#deleteButton:hover {
                background-color: #da190b;
            }
            QPushButton#cancelButton {
                background-color: #9CA3AF;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #6B7280;
            }
            QPushButton#archiveButton {
                background-color: #F59E0B;
                color: white;
            }
            QPushButton#archiveButton:hover {
                background-color: #D97706;
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
        self.content_edit.setText(self.task.content)
        self.content_edit.setPlaceholderText("请输入任务内容...")
        self.content_edit.setMinimumHeight(35)
        form_layout.addRow("任务内容:", self.content_edit)
        
        # 2. 截止时间选择器
        self.deadline_edit = QDateTimeEdit()
        deadline_datetime = self._parse_deadline(self.task.deadline)
        self.deadline_edit.setDateTime(deadline_datetime)
        self.deadline_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.deadline_edit.setMinimumHeight(35)
        self.deadline_edit.setCalendarPopup(True)  # 显示日历弹窗
        form_layout.addRow("截止时间:", self.deadline_edit)
        
        # 3. 优先级选择下拉框（不包含P0，因为P0是自动设置的紧急状态）
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["P1 - 重要/中", "P2 - 普通/低", "P3 - 轻微/待定"])
        
        # 设置当前优先级：显示用户原本设置的优先级，而不是自动设置的P0
        # 使用original_priority而不是priority，因为priority可能被自动设置为P0
        original_priority = self.task.original_priority if hasattr(self.task, 'original_priority') else self.task.priority
        # 将原始优先级映射到下拉框索引：P1->0, P2->1, P3->2
        priority_map = {1: 0, 2: 1, 3: 2}
        current_priority = priority_map.get(original_priority, 0)
        self.priority_combo.setCurrentIndex(current_priority)
        self.priority_combo.setMinimumHeight(35)
        form_layout.addRow("优先级:", self.priority_combo)
        
        # 添加表单布局到主布局
        main_layout.addLayout(form_layout)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.delete_task)
        
        # 归档按钮
        self.archive_button = QPushButton("归档")
        self.archive_button.setObjectName("archiveButton")
        self.archive_button.clicked.connect(self.archive_task)
        
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.archive_button)
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save_task)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 设置Tab键顺序
        self.setTabOrder(self.content_edit, self.deadline_edit)
        self.setTabOrder(self.deadline_edit, self.priority_combo)
        self.setTabOrder(self.priority_combo, self.save_button)
        self.setTabOrder(self.save_button, self.cancel_button)
        self.setTabOrder(self.cancel_button, self.delete_button)
        self.setTabOrder(self.delete_button, self.archive_button)
        
        # 默认焦点在内容输入框
        self.content_edit.setFocus()
        
    def _parse_deadline(self, deadline_str):
        """解析截止时间字符串为QDateTime对象"""
        try:
            # 尝试解析 "yyyy-MM-dd hh:mm" 格式
            if ' ' in deadline_str:
                date_part, time_part = deadline_str.split(' ')
                year, month, day = map(int, date_part.split('-'))
                hour, minute = map(int, time_part.split(':'))
                return QDateTime(year, month, day, hour, minute)
            else:
                # 如果只有日期，设置时间为23:59
                year, month, day = map(int, deadline_str.split('-'))
                return QDateTime(year, month, day, 23, 59)
        except:
            # 如果解析失败，使用当前时间
            return QDateTime.currentDateTime()
        
    def save_task(self):
        """保存任务修改"""
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
        
    def delete_task(self):
        """删除任务（需要二次确认）"""
        reply = QMessageBox.question(self, "确认删除", 
                                    "确定要删除这个任务吗？",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.delete_result = True
            self.accept()
        else:
            self.delete_result = False
    
    def archive_task(self):
        """归档任务（需要二次确认）"""
        reply = QMessageBox.question(self, "确认归档", 
                                    "确定要归档这个任务吗？归档后任务将保留在日志文件中，但不再显示在主窗口。",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.archive_result = True
            self.accept()
        else:
            self.archive_result = False
        
    def get_task_data(self):
        """获取修改后的任务数据"""
        if hasattr(self, 'delete_result') and self.delete_result:
            return None, None, None, True, False  # 返回删除标志
        
        if hasattr(self, 'archive_result') and self.archive_result:
            return None, None, None, False, True  # 返回归档标志
        
        if self.result() == QDialog.Accepted:
            content = self.content_edit.text().strip()
            deadline = self.deadline_edit.dateTime().toString("yyyy-MM-dd hh:mm")
            # 获取优先级：下拉框索引0=P1, 1=P2, 2=P3
            priority_map = {0: 1, 1: 2, 2: 3}  # 索引0->P1, 1->P2, 2->P3
            priority = priority_map[self.priority_combo.currentIndex()]
            
            return content, deadline, priority, False, False
        else:
            return None, None, None, False, False


# 测试代码
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from task import Task
    
    app = QApplication(sys.argv)
    
    # 创建测试任务
    test_task = Task("测试任务", "2025-12-31 18:00", 1)
    
    dialog = EditTaskDialog(test_task)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        content, deadline, priority, to_delete = dialog.get_task_data()
        if not to_delete:
            print(f"修改任务: {content}")
            print(f"截止时间: {deadline}")
            print(f"优先级: {priority}")
    else:
        content, deadline, priority, to_delete = dialog.get_task_data()
        if to_delete:
            print("删除任务")
        else:
            print("用户取消了编辑")
            
    sys.exit()