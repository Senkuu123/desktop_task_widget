"""
任务数据模型定义
用于桌面任务小组件应用
"""

import json
from datetime import datetime
from typing import Dict, Any


class Task:
    """任务类，表示一个待办任务"""
    
    def __init__(self, content: str, deadline: str, priority: int = 2, task_id: int = None):
        """
        初始化任务对象
        
        Args:
            content (str): 任务内容
            deadline (str): 截止时间，格式为 "YYYY-MM-DD HH:MM" 或 "YYYY-MM-DD"
            priority (int): 优先级，1-3数字，1为最高，3为最低
            task_id (int): 任务ID，如果不提供则自动生成
        """
        self.id = task_id or self._generate_id()
        self.content = content.strip()
        self.deadline = deadline
        self.original_priority = max(0, min(4, priority))  # 保存原始优先级
        self.priority = self.original_priority  # 当前优先级
        self.is_done = False
        self.is_archived = False  # 是否已归档
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.completed_at = None  # 完成时间，初次勾选时记录
        self.archived_at = None   # 归档时间
        
    def _generate_id(self) -> int:
        """生成任务ID（基于时间戳）"""
        return int(datetime.now().timestamp() * 1000)  # 毫秒时间戳作为ID
    
    def mark_done(self):
        """标记任务为已完成"""
        self.is_done = True
        # 如果是初次完成，记录完成时间
        if self.completed_at is None:
            self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def mark_undone(self):
        """标记任务为未完成"""
        self.is_done = False
        # 取消完成状态时不清除完成时间，保留历史记录
        
    def toggle_done(self):
        """切换任务完成状态"""
        was_done = self.is_done
        self.is_done = not self.is_done
        
        # 如果从未完成变为完成，记录完成时间
        if not was_done and self.is_done and self.completed_at is None:
            self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def archive(self):
        """归档任务"""
        self.is_archived = True
        self.archived_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def unarchive(self):
        """取消归档任务"""
        self.is_archived = False
        self.archived_at = None
        
    def is_overdue(self) -> bool:
        """检查任务是否过期"""
        if self.is_done:
            return False
        try:
            deadline_datetime = self.get_deadline_datetime()
            now = datetime.now()
            return deadline_datetime < now
        except (ValueError, TypeError):
            return False
            
    def get_deadline_datetime(self) -> datetime:
        """获取截止时间的datetime对象"""
        # 尝试不同的时间格式
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S", 
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(self.deadline, fmt)
            except ValueError:
                continue
        
        # 如果所有格式都失败，抛出异常
        raise ValueError(f"无法解析时间格式: {self.deadline}")
        
    def get_priority_text(self) -> str:
        """获取优先级文本描述"""
        priority_map = {
            0: "P0",
            1: "P1", 
            2: "P2",
            3: "P3",
            4: "P4"
        }
        return priority_map.get(self.priority, "P2")
        
    def to_dict(self) -> Dict[str, Any]:
        """将任务对象转换为字典（用于JSON序列化）"""
        return {
            'id': self.id,
            'content': self.content,
            'deadline': self.deadline,
            'priority': self.priority,
            'original_priority': self.original_priority,
            'is_done': self.is_done,
            'is_archived': self.is_archived,
            'created_at': self.created_at,
            'completed_at': self.completed_at,  # 新增完成时间字段
            'archived_at': self.archived_at     # 归档时间
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务对象（用于JSON反序列化）"""
        task = cls(
            content=data['content'],
            deadline=data['deadline'],
            priority=data.get('original_priority', data['priority']),  # 优先使用原始优先级
            task_id=data['id']
        )
        task.priority = data['priority']  # 设置当前优先级
        task.original_priority = data.get('original_priority', data['priority'])  # 设置原始优先级
        task.is_done = data.get('is_done', False)
        task.is_archived = data.get('is_archived', False)
        task.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        task.completed_at = data.get('completed_at', None)  # 加载完成时间
        task.archived_at = data.get('archived_at', None)    # 加载归档时间
        return task
        
    def to_json(self) -> str:
        """将任务对象转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        """从JSON字符串创建任务对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def __str__(self) -> str:
        """字符串表示"""
        status = "✓" if self.is_done else "○"
        priority = self.get_priority_text()
        return f"[{status}] {self.content} (优先级:{priority} 截止:{self.deadline})"
        
    def __repr__(self) -> str:
        """调试用的字符串表示"""
        return f"Task(id={self.id}, content='{self.content}', priority={self.priority}, done={self.is_done})"


# 示例用法和测试代码
if __name__ == '__main__':
    # 创建几个测试任务
    task1 = Task("完成项目报告", "2024-08-25 18:00", 1)
    task2 = Task("学习Python", "2024-08-24 20:00", 2) 
    task3 = Task("锻炼身体", "2024-08-23 07:00", 3)
    
    print("=== 创建的任务 ===")
    print(task1)
    print(task2)
    print(task3)
    
    # 测试完成状态切换
    print("\n=== 测试完成状态 ===")
    task1.mark_done()
    print(f"任务1完成状态: {task1.is_done}")
    print(task1)
    
    # 测试JSON序列化
    print("\n=== 测试JSON序列化 ===")
    json_str = task2.to_json()
    print("JSON字符串:")
    print(json_str)
    
    # 测试JSON反序列化
    task_from_json = Task.from_json(json_str)
    print("\n从JSON恢复的任务:")
    print(task_from_json)
    
    # 测试过期检查
    print("\n=== 测试过期检查 ===")
    overdue_task = Task("测试过期任务", "2023-01-01", 1)
    print(f"过期任务是否过期: {overdue_task.is_overdue()}")
    print(f"正常任务是否过期: {task1.is_overdue()}")