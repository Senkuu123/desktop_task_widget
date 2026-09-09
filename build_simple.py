"""
桌面任务小组件 - 简单打包脚本
"""

import os
import sys
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def check_required_files():
    """检查必需的文件是否存在"""
    required_files = [
        'main.py',
        'task_window.py',
        'task.py',
        'habit.py',
        'storage.py',
        'add_task_dialog.py',
        'edit_task_dialog.py',
        'add_habit_dialog.py',
        'water_reminder.py',
        'autostart_manager.py',
        'images_rc.py',  # 新增资源文件
        'DesktopTaskWidget.spec',
        'quick_notes/__init__.py',
        'quick_notes/dialog.py',
        'quick_notes/card.py',
        'quick_notes/hotkey.py',
        'quick_notes/store.py',
        'app_icon.ico',
        'version_info.txt'
    ]
    
    print("🔍🔍🔍🔍 检查必需文件...")
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌❌❌❌ 以下文件缺失:")
        for file in missing_files:
            print(f"   - {file}")
        
        # 如果图标文件缺失，创建一个简单的版本
        if 'app_icon.ico' in missing_files:
            print("⚠️  正在创建默认图标文件...")
            if create_default_icon() and os.path.exists('app_icon.ico'):
                missing_files.remove('app_icon.ico')
                print("✅ 已创建默认图标文件")
        
        # 如果版本信息文件缺失，创建一个
        if 'version_info.txt' in missing_files:
            print("⚠️  正在创建版本信息文件...")
            if create_version_info() and os.path.exists('version_info.txt'):
                missing_files.remove('version_info.txt')
                print("✅ 已创建版本信息文件")
        
        # 如果资源文件缺失，提示用户
        if 'images_rc.py' in missing_files:
            print("⚠️  images_rc.py 文件缺失，这是必要的资源文件")
            print("   请确保已生成此文件或从源代码中获取")
        
        if missing_files:
            return False
    
    print("✅ 所有必需文件都存在")
    return True

def create_default_icon():
    """创建默认图标文件"""
    try:
        from PIL import Image, ImageDraw
        # 创建一个64x64的图标
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制圆形背景
        draw.ellipse([8, 8, 56, 56], fill=(74, 175, 80, 255))
        
        # 绘制勾号
        draw.line([(24, 32), (32, 40)], fill=(255, 255, 255, 255), width=4)
        draw.line([(32, 40), (44, 24)], fill=(255, 255, 255, 255), width=4)
        
        # 保存为ICO文件
        img.save('app_icon.ico', format='ICO', sizes=[(64, 64), (48, 48), (32, 32), (16, 16)])
        return True
    except ImportError:
        print("⚠️  未安装PIL库，无法创建默认图标")
        return False
    except Exception as e:
        print(f"❌❌❌❌ 创建图标失败: {e}")
        return False

def create_version_info():
    """创建版本信息文件"""
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'DesktopTaskWidget'),
           StringStruct(u'FileDescription', u'桌面任务小组件'),
           StringStruct(u'FileVersion', u'1.0.0.0'),
           StringStruct(u'InternalName', u'DesktopTaskWidget'),
           StringStruct(u'LegalCopyright', u'Copyright © 2024 DesktopTaskWidget'),
           StringStruct(u'OriginalFilename', u'DesktopTaskWidget.exe'),
           StringStruct(u'ProductName', u'桌面任务小组件'),
           StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x409, 1200])])
  ]
)
'''
    try:
        with open('version_info.txt', 'w', encoding='utf-8') as f:
            f.write(version_info)
        return True
    except Exception as e:
        print(f"❌❌❌❌ 创建版本信息文件失败: {e}")
        return False

def create_dpi_manifest():
    """创建DPI感知的manifest文件"""
    manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="DesktopTaskWidget"
    type="win32"
  />
  <description>桌面任务小组件</description>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>'''
    
    try:
        with open('dpi.manifest', 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        print("✅ 已创建DPI感知manifest文件")
        return True
    except Exception as e:
        print(f"❌❌❌❌ 创建manifest文件失败: {e}")
        return False

def run_pyinstaller():
    """使用当前Python环境和项目spec打包，不清理用户数据目录。"""
    from importlib.util import find_spec
    if find_spec('PyInstaller') is None:
        print('当前Python环境未安装PyInstaller，请运行：')
        print(f'"{sys.executable}" -m pip install pyinstaller')
        return False

    dist_dir = os.path.join(PROJECT_DIR, 'dist', 'quick-notes')
    cmd = [
        sys.executable, '-X', 'utf8', '-m', 'PyInstaller',
        '--noconfirm',
        '--distpath', dist_dir,
        '--workpath', os.path.join(PROJECT_DIR, 'build', 'release'),
        os.path.join(PROJECT_DIR, 'DesktopTaskWidget.spec'),
    ]
    print('开始打包，请先退出同目录正在运行的DesktopTaskWidget.exe。', flush=True)
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR)
    except OSError as error:
        print(f'打包启动失败：{error}')
        return False
    if result.returncode != 0:
        print('打包失败，请检查上方错误；原有数据文件保留。')
        return False

    exe_path = os.path.join(dist_dir, 'DesktopTaskWidget.exe')
    if not os.path.isfile(exe_path):
        print('打包未生成预期的exe文件。')
        return False
    print(f'打包完成：{exe_path}')
    print(f'文件大小：{os.path.getsize(exe_path) / (1024 * 1024):.2f} MB')
    print('任务、便签存档和日志继续保存在exe同目录。')
    return True


def main():
    # 从其他目录启动脚本时，也始终使用本项目的源码和资源。
    os.chdir(PROJECT_DIR)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print('桌面任务小组件打包工具')
    if not check_required_files():
        return 1
    if not os.path.exists('dpi.manifest') and not create_dpi_manifest():
        return 1
    return 0 if run_pyinstaller() else 1


if __name__ == '__main__':
    sys.exit(main())
