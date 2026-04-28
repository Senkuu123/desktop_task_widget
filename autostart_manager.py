"""
开机自启动管理模块
用于处理Windows系统下的开机自启动设置
"""

import os
import sys
import winreg
import json


class AutoStartManager:
    """开机自启动管理器"""
    
    def __init__(self, app_name="DesktopTaskWidget"):
        self.app_name = app_name
        self.registry_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        self.config_file = "autostart_config.json"
        
    def get_exe_path(self):
        """获取当前可执行文件的完整路径 - 优化版本"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe文件
            exe_path = sys.executable
        else:
            # 开发环境中的Python脚本
            exe_path = os.path.abspath(sys.argv[0])
        
        # 确保路径使用双引号包围，避免空格问题
        return f'"{exe_path}"'
    
    def is_enabled(self):
        """检查是否已启用开机自启动，并验证路径有效性"""
        try:
            # 首先检查注册表
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    # 验证路径是否有效
                    exe_path = value.strip('"')
                    if os.path.exists(exe_path):
                        return True
                    else:
                        # 路径无效，清理注册表并同步配置文件
                        self._clean_invalid_registry()
                        self._save_config({'enabled': False})
                        return False
                except FileNotFoundError:
                    return False
        except Exception:
            # 如果注册表操作失败，检查配置文件
            return self._load_config().get('enabled', False)
    
    def enable(self):
        """启用开机自启动 - 优化版本"""
        try:
            exe_path = self.get_exe_path()
            
            # 添加到注册表
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
            
            # 保存配置到文件
            self._save_config({'enabled': True, 'exe_path': exe_path})
            
            print(f"✅ 开机自启动已启用: {exe_path}")
            return True
        except Exception as e:
            print(f"❌ 启用开机自启动失败: {e}")
            # 如果注册表失败，尝试只保存到配置文件
            self._save_config({'enabled': True, 'exe_path': self.get_exe_path()})
            return False
    
    def disable(self):
        """禁用开机自启动"""
        try:
            # 从注册表删除
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                except FileNotFoundError:
                    pass  # 如果键不存在，忽略错误
            
            # 保存配置到文件
            self._save_config({'enabled': False})
            
            print("✅ 开机自启动已禁用")
            return True
        except Exception as e:
            print(f"❌ 禁用开机自启动失败: {e}")
            # 如果注册表失败，尝试只保存到配置文件
            self._save_config({'enabled': False})
            return False
    
    def _save_config(self, config):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def _load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
        return {}
    
    def _clean_invalid_registry(self):
        """清理无效的注册表项"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    print(f"✅ 已清理无效的注册表项: {self.app_name}")
                except FileNotFoundError:
                    pass  # 如果键不存在，忽略错误
        except Exception as e:
            print(f"❌ 清理注册表失败: {e}")
    
    def get_status_text(self):
        """获取状态文本"""
        if self.is_enabled():
            return "已启用"
        else:
            return "已禁用"
    
    def toggle(self):
        """切换开机自启动状态"""
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()


def check_startup_permission():
    """检查是否有足够的权限设置开机自启动"""
    try:
        # 尝试写入注册表来测试权限
        test_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key, 0, winreg.KEY_WRITE):
            return True
    except Exception:
        return False


def get_startup_info():
    """获取开机自启动相关信息"""
    manager = AutoStartManager()
    return {
        'enabled': manager.is_enabled(),
        'has_permission': check_startup_permission(),
        'exe_path': manager.get_exe_path(),
        'status_text': manager.get_status_text()
    }


if __name__ == '__main__':
    # 测试代码
    manager = AutoStartManager()
    print(f"当前状态: {manager.get_status_text()}")
    print(f"可执行文件路径: {manager.get_exe_path()}")
    print(f"是否有权限: {check_startup_permission()}")
    
    # 测试切换
    if not manager.is_enabled():
        print("尝试启用开机自启动...")
        if manager.enable():
            print("✅ 启用成功")
        else:
            print("❌ 启用失败")
    else:
        print("尝试禁用开机自启动...")
        if manager.disable():
            print("✅ 禁用成功")
        else:
            print("❌ 禁用失败")