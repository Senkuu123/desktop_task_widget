"""
桌面任务小组件 - 主程序入口
启动桌面任务管理悬浮窗
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from task_window import TransparentTaskWindow
import images_rc


def setup_dpi_scaling():
    """设置DPI缩放兼容性"""
    if sys.platform == 'win32':
        try:
            # 方法1: 使用Windows API设置DPI感知
            import ctypes
            # 尝试设置进程DPI感知
            awareness = 2  # Per Monitor DPI Aware V2 (推荐)
            ctypes.windll.shcore.SetProcessDpiAwareness(awareness)
            print(f"✅ 已设置Windows DPI感知级别: {awareness}")
        except Exception as e:
            print(f"⚠️ Windows DPI API设置失败: {e}")
            try:
                # 方法2: 旧版Windows兼容性设置
                ctypes.windll.user32.SetProcessDPIAware()
                print("✅ 已设置旧版DPI感知")
            except Exception as e2:
                print(f"⚠️ 旧版DPI设置也失败: {e2}")
    
    # 方法3: 设置Qt高DPI缩放环境变量
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    
    # 方法4: 设置Qt应用属性（必须在QApplication之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    print("✅ 已设置Qt高DPI缩放属性")


def resource_path(relative_path):
    """获取资源的绝对路径。适用于开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，将资源存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def create_default_icon():
    """创建默认图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    # 绘制一个简单的任务图标
    from PyQt5.QtGui import QPainter, QBrush, QPen, QColor
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制背景
    painter.setBrush(QBrush(QColor(74, 175, 80)))  # 绿色
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(8, 8, 48, 48)
    
    # 绘制勾号
    painter.setPen(QPen(Qt.white, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(24, 32, 32, 40)
    painter.drawLine(32, 40, 44, 24)
    
    painter.end()
    return QIcon(pixmap)


def load_application_icon():
    """加载应用程序图标 - 优化版本"""
    icon_paths = [
        'app_icon.ico',  # 当前工作目录
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.ico'),  # 脚本目录
        resource_path('app_icon.ico'),  # PyInstaller资源路径
    ]
    
    # 如果是打包的exe，添加exe同目录的图标路径
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        icon_paths.insert(0, os.path.join(exe_dir, 'app_icon.ico'))
        # 添加exe所在目录的上级目录（针对某些打包场景）
        icon_paths.insert(0, os.path.join(os.path.dirname(exe_dir), 'app_icon.ico'))
    
    # 添加更多可能的路径
    icon_paths.extend([
        os.path.join(os.getcwd(), 'app_icon.ico'),  # 当前工作目录
        os.path.join(os.path.expanduser('~'), 'app_icon.ico'),  # 用户主目录
    ])
    
    print("🔍 搜索图标文件路径:")
    for path in icon_paths:
        if os.path.exists(path):
            try:
                icon = QIcon(path)
                if not icon.isNull():
                    print(f"✅ 成功加载应用程序图标: {path}")
                    return icon
                else:
                    print(f"⚠️ 图标文件存在但加载失败: {path}")
            except Exception as e:
                print(f"⚠️ 加载图标文件出错 {path}: {e}")
        else:
            print(f"❌ 图标文件不存在: {path}")
    
    print("⚠️ 未找到图标文件，使用默认图标")
    return create_default_icon()


def setup_windows_app_id(app):
    """设置Windows应用ID - 优化版本"""
    if sys.platform != 'win32':
        return
        
    app_id = 'DesktopTaskWidget.1.0.0'
    
    # 方法1: 使用SetCurrentProcessExplicitAppUserModelID（推荐）
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        print(f"✅ 已设置Windows应用ID: {app_id}")
        return True
    except Exception as e:
        print(f"⚠️ 方法1设置应用ID失败: {e}")
    
    # 方法2: 设置环境变量
    try:
        os.environ['APP_ID'] = app_id
        print(f"✅ 已设置环境变量APP_ID: {app_id}")
        return True
    except Exception as e:
        print(f"⚠️ 方法2设置应用ID也失败: {e}")
    
    print("⚠️ 所有应用ID设置方法均失败，但程序将继续运行")
    return False


def pre_initialize_application():
    """预初始化应用设置"""
    # 设置DPI缩放（必须在QApplication创建之前）
    setup_dpi_scaling()
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("DesktopTaskWidget")
    app.setApplicationDisplayName("桌面任务小组件")
    app.setApplicationVersion("1.0.0")
    
    # 设置Windows应用ID
    setup_windows_app_id(app)
    
    # 提前加载并设置应用图标
    icon = load_application_icon()
    if icon and not icon.isNull():
        app.setWindowIcon(icon)
        print("✅ 应用程序图标设置完成")
    else:
        print("❌ 应用程序图标设置失败")
    
    return app, icon


def main():
    """主函数：启动应用程序 - 优化版本"""
    
    # 预初始化应用
    app, app_icon = pre_initialize_application()
    
    # 创建任务窗口实例
    window = TransparentTaskWindow()
    
    # 确保窗口使用相同的图标（再次设置以确保）
    if app_icon and not app_icon.isNull():
        window.setWindowIcon(app_icon)
        print("✅ 窗口图标设置完成")
    
    # 设置窗口DPI相关属性
    if hasattr(window, 'setDpiSettings'):
        window.setDpiSettings()
    else:
        print("⚠️ TransparentTaskWindow没有setDpiSettings方法，跳过窗口级DPI设置")
    
    # 延迟显示窗口，确保图标和窗口属性已完全设置
    from PyQt5.QtCore import QTimer
    def initialize_window():
        # 显示窗口（任务加载已在TransparentTaskWindow中延迟执行）
        window.show()
        
        print("✅ 应用程序启动完成")
        print(f"✅ DPI设置: 缩放因子={window.devicePixelRatio()}")
    
    # 使用单次定时器延迟初始化，确保图标和窗口属性已完全设置
    QTimer.singleShot(100, initialize_window)
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()