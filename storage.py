"""
桌面任务小组件 - 数据存储模块
实现任务的JSON文件保存与加载功能
"""

import json
import os
import sys
from typing import List, Optional
from task import Task


def get_data_dir():
    """获取数据文件目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe文件，使用exe所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，使用脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))


def get_tasks_file_path():
    """获取任务数据文件路径"""
    data_dir = get_data_dir()
    return os.path.join(data_dir, "tasks.json")


def get_settings_file_path():
    """获取设置数据文件路径"""
    data_dir = get_data_dir()
    return os.path.join(data_dir, "settings.json")


# 任务数据文件路径（使用函数获取，确保路径正确）
TASKS_FILE = get_tasks_file_path()
SETTINGS_FILE = get_settings_file_path()


def save_tasks_to_json(tasks_list: List[Task]) -> bool:
    """
    将任务列表保存到JSON文件（包含所有任务，包括已归档的）
    
    Args:
        tasks_list (List[Task]): 要保存的任务对象列表
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        # 将任务对象转换为字典列表（包含所有任务）
        tasks_data = []
        for task in tasks_list:
            tasks_data.append(task.to_dict())
        
        # 保存到JSON文件
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功保存 {len(tasks_data)} 个任务到 {TASKS_FILE}")
        print(f"数据文件目录: {os.path.dirname(TASKS_FILE)}")
        return True
        
    except Exception as e:
        print(f"保存任务失败: {e}")
        return False


def load_tasks_from_json() -> List[Task]:
    """
    从JSON文件加载任务列表（加载所有任务，包括已归档的）
    
    Returns:
        List[Task]: 加载的任务对象列表，如果失败返回空列表
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(TASKS_FILE):
            print(f"任务文件 {TASKS_FILE} 不存在，返回空列表")
            return []
        
        # 从JSON文件读取数据
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        # 将字典数据转换为任务对象
        tasks_list = []
        for task_data in tasks_data:
            try:
                task = Task.from_dict(task_data)
                tasks_list.append(task)
            except Exception as e:
                print(f"加载单个任务失败: {e}, 数据: {task_data}")
                continue
        
        print(f"成功从 {TASKS_FILE} 加载 {len(tasks_list)} 个任务")
        print(f"数据文件目录: {os.path.dirname(TASKS_FILE)}")
        return tasks_list
        
    except json.JSONDecodeError as e:
        print(f"JSON格式错误，无法加载任务: {e}")
        return []
    except Exception as e:
        print(f"加载任务失败: {e}")
        return []


def backup_tasks() -> bool:
    """
    备份当前任务文件
    
    Returns:
        bool: 备份成功返回True，失败返回False
    """
    try:
        if not os.path.exists(TASKS_FILE):
            print("没有任务文件需要备份")
            return True
        
        # 创建备份文件名（添加时间戳）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"tasks_backup_{timestamp}.json"
        
        # 复制文件
        with open(TASKS_FILE, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        print(f"任务文件已备份到 {backup_file}")
        return True
        
    except Exception as e:
        print(f"备份任务文件失败: {e}")
        return False


def export_tasks_to_txt(tasks_list: List[Task], filename: str = None) -> bool:
    """
    导出任务列表到文本文件
    
    Args:
        tasks_list (List[Task]): 要导出的任务列表
        filename (str): 导出文件名，如果为None则使用默认名称
        
    Returns:
        bool: 导出成功返回True，失败返回False
    """
    try:
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tasks_export_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== 任务列表导出 ===\n\n")
            
            undone_tasks = [task for task in tasks_list if not task.is_done]
            done_tasks = [task for task in tasks_list if task.is_done]
            
            if undone_tasks:
                f.write("【未完成任务】\n")
                f.write("-" * 50 + "\n")
                for i, task in enumerate(undone_tasks, 1):
                    f.write(f"{i}. {task.content}\n")
                    f.write(f"   优先级: {task.get_priority_text()}\n")
                    f.write(f"   截止时间: {task.deadline}\n")
                    f.write(f"   创建时间: {task.created_at}\n")
                    if task.is_overdue():
                        f.write("   ⚠️  已过期!\n")
                    f.write("\n")
            
            if done_tasks:
                f.write("\n【已完成任务】\n")
                f.write("-" * 50 + "\n")
                for i, task in enumerate(done_tasks, 1):
                    f.write(f"{i}. ✓ {task.content}\n")
                    f.write(f"   优先级: {task.get_priority_text()}\n")
                    f.write(f"   截止时间: {task.deadline}\n")
                    f.write(f"   创建时间: {task.created_at}\n")
                    f.write("\n")
        
        print(f"任务列表已导出到 {filename}")
        return True
        
    except Exception as e:
        print(f"导出任务失败: {e}")
        return False


def archive_task(task: Task) -> bool:
    """
    归档任务
    
    Args:
        task (Task): 要归档的任务对象
        
    Returns:
        bool: 归档成功返回True，失败返回False
    """
    try:
        # 标记任务为已归档
        task.archive()
        
        print(f"任务 '{task.content}' 已标记为已归档")
        return True
        
    except Exception as e:
        print(f"归档任务失败: {e}")
        return False





def get_tasks_statistics(tasks_list: List[Task]) -> dict:
    """
    获取任务统计信息
    
    Args:
        tasks_list (List[Task]): 任务列表
        
    Returns:
        dict: 统计信息字典
    """
    total_tasks = len(tasks_list)
    undone_tasks = len([task for task in tasks_list if not task.is_done])
    done_tasks = len([task for task in tasks_list if task.is_done])
    overdue_tasks = len([task for task in tasks_list if task.is_overdue()])
    
    # 按优先级统计
    high_priority = len([task for task in tasks_list if task.priority == 1 and not task.is_done])
    medium_priority = len([task for task in tasks_list if task.priority == 2 and not task.is_done])
    low_priority = len([task for task in tasks_list if task.priority == 3 and not task.is_done])
    
    return {
        'total_tasks': total_tasks,
        'undone_tasks': undone_tasks,
        'done_tasks': done_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'completion_rate': round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    }


def save_settings(settings: dict) -> bool:
    """
    保存窗口设置到JSON文件
    
    Args:
        settings (dict): 设置字典，包含窗口透明度、文字大小、文字透明度、窗口位置等
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"成功保存设置到 {SETTINGS_FILE}")
        return True
    except Exception as e:
        print(f"保存设置失败: {e}")
        return False


def load_settings() -> dict:
    """
    从JSON文件加载窗口设置
    
    Returns:
        dict: 加载的设置字典，如果失败返回默认设置
    """
    default_settings = {
        'window_background_opacity': 0.8,
        'current_font_size': 11,
        'current_font_opacity': 100,
        'window_geometry': None  # 保存窗口位置和大小: 'x,y,width,height'
    }
    
    try:
        if not os.path.exists(SETTINGS_FILE):
            print(f"设置文件 {SETTINGS_FILE} 不存在，使用默认设置")
            return default_settings
        
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        print(f"成功从 {SETTINGS_FILE} 加载设置")
        return settings
    except Exception as e:
        print(f"加载设置失败: {e}, 使用默认设置")
        return default_settings


# 测试代码
if __name__ == '__main__':
    print("=== 测试数据存储功能 ===")
    
    # 创建测试任务
    test_tasks = [
        Task("完成项目报告", "2024-12-27 18:00", 1),
        Task("学习Python", "2024-12-28 20:00", 2),
        Task("锻炼身体", "2024-12-26 07:00", 3)
    ]
    
    # 标记一个任务为完成
    test_tasks[2].mark_done()
    
    print("\n1. 测试保存任务")
    success = save_tasks_to_json(test_tasks)
    print(f"保存结果: {success}")
    
    print("\n2. 测试加载任务")
    loaded_tasks = load_tasks_from_json()
    print(f"加载到 {len(loaded_tasks)} 个任务:")
    for task in loaded_tasks:
        print(f"  - {task}")
    
    print("\n3. 测试任务统计")
    stats = get_tasks_statistics(loaded_tasks)
    print("统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n4. 测试导出功能")
    export_success = export_tasks_to_txt(loaded_tasks)
    print(f"导出结果: {export_success}")
    
    print("\n5. 测试备份功能")
    backup_success = backup_tasks()
    print(f"备份结果: {backup_success}")