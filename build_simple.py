"""
桌面任务小组件 - 简单打包脚本
"""

import os
import sys
import subprocess

def check_required_files():
    """检查必需的文件是否存在"""
    required_files = [
        'main.py',
        'task_window.py',
        'task.py',
        'storage.py',
        'add_task_dialog.py',
        'edit_task_dialog.py',
        'autostart_manager.py',
        'images_rc.py',  # 新增资源文件
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
    """运行PyInstaller"""
    print("🚀🚀🚀🚀 开始打包，这可能需要几分钟...")
    
    # 检查图标文件
    icon_file = 'app_icon.ico'
    if not os.path.exists(icon_file):
        print("❌❌❌❌ 图标文件不存在，尝试创建...")
        if not create_default_icon():
            print("⚠️  使用默认图标")
            icon_param = []
        else:
            print(f"✅ 使用图标文件: {icon_file}")
            icon_param = ['--icon=' + icon_file]
    else:
        print(f"✅ 使用图标文件: {icon_file}")
        icon_param = ['--icon=' + icon_file]
    
    # 创建DPI manifest文件
    create_dpi_manifest()

    # 构建PyInstaller命令（优化DPI支持）
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--noconsole',
        '--name=DesktopTaskWidget',
        '--clean',
        '--distpath=dist',
        '--workpath=build',
        # 隐藏导入
        '--hidden-import=PyQt5.sip',
        '--hidden-import=ctypes',
        '--hidden-import=winreg',
        '--hidden-import=platform',
        '--hidden-import=sys',
        '--hidden-import=os',
        '--hidden-import=datetime',
        '--hidden-import=json',
        '--hidden-import=re',
        '--hidden-import=images_rc',
        # 添加数据文件
        '--add-data=app_icon.ico;.',
        '--add-data=version_info.txt;.',
        '--add-data=dpi.manifest;.',
        '--add-data=images_rc.py;.',
        # 使用manifest文件
        '--version-file=version_info.txt',
        # 启用UPX压缩（可选）
        '--upx-dir=upx' if os.path.exists('upx') else '',
    ] + icon_param + [
        'main.py'
    ]
    
    # 移除空参数
    cmd = [arg for arg in cmd if arg]
    
    try:
        # 执行打包命令
        print("执行命令: " + " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 打包成功！")
            print(f"📁📁📁📁 EXE文件位置: {os.path.join('dist', 'DesktopTaskWidget.exe')}")
            
            # 显示文件大小
            exe_path = os.path.join('dist', 'DesktopTaskWidget.exe')
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path) / (1024 * 1024)  # 转换为MB
                print(f"📏📏📏📏 文件大小: {size:.2f} MB")
                
                # 验证DPI设置
                print("\n🔍🔍🔍🔍 验证DPI设置:")
                print("1. 检查exe属性中是否有DPI感知标记")
                print("2. 在高DPI显示器上测试窗口缩放")
                print("3. 查看程序启动日志中的DPI设置信息")
                
            # Windows 11优化提示
            print("\n💡💡💡💡 Windows 11优化提示:")
            print("1. 首次运行可能需要右键选择'以管理员身份运行'")
            print("2. 如果任务栏图标显示异常，可以清理图标缓存:")
            print("   - 删除 %localappdata%\\IconCache.db")
            print("   - 重启资源管理器或重启电脑")
            print("3. DPI设置需要Windows 10 1703+或Windows 11支持")
                
        else:
            print("❌❌❌❌ 打包失败")
            print("错误信息:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌❌❌❌ 未找到PyInstaller，请先安装: pip install pyinstaller")
    except Exception as e:
        print(f"❌❌❌❌ 打包过程出错: {e}")

def clean_old_builds():
    """清理旧构建文件"""
    print("\n🧹🧹🧹🧹 清理旧构建文件...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                print(f"  已删除: {folder}")
            except Exception as e:
                print(f"  删除失败 {folder}: {e}")

def main():
    print("=" * 50)
    print("    桌面任务小组件 - EXE打包工具 (Windows 11优化版)")
    print("=" * 50)
    print()
    
    # 检查文件
    if not check_required_files():
        print("\n请确保以上文件都在当前目录中")
        input("按Enter键退出...")
        return
    
    # 清理旧构建文件
    clean_old_builds()
    
    # 执行打包
    run_pyinstaller()
    
    print("\n" + "=" * 50)
    input("按Enter键退出...")

if __name__ == '__main__':
    main()