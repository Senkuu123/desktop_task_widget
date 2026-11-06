import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from quick_notes.hotkey import NoteHotkey
from quick_notes.actions import NoteActions
from storage import save_settings, load_settings, load_habits_from_json, load_water_reminder
from autostart_manager import AutoStartManager
from .layout import WindowLayoutMixin
from .tasks import WindowTasksMixin
from .interaction import WindowInteractionMixin
from .notes import WindowNotesMixin
from .habits import WindowHabitsMixin
from .notifications import WindowNotificationsMixin
from .edge_hide import WindowEdgeHideMixin


class TransparentTaskWindow(
    WindowLayoutMixin,
    WindowTasksMixin,
    WindowInteractionMixin,
    WindowNotesMixin,
    WindowHabitsMixin,
    WindowNotificationsMixin,
    WindowEdgeHideMixin,
    QWidget,
):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.habits = []
        self.notes = []
        self.note_cards = {}
        self.note_actions = NoteActions(self)
        self.note_drafts = {}
        self.note_store = None
        self.note_load_error = False
        self.note_dialog = None
        self.note_toast = None
        self.task_widgets = {}
        self.current_font_size = 11
        self.current_font_opacity = 100
        self.window_background_opacity = 0.8
        self.current_page = 'tasks'
        self.last_content_page = 'tasks'
        self.last_water_page = 'water'
        self.notified_task_ids = set()  # 已弹窗提醒的任务ID集合
        self.water_reminder = load_water_reminder()
        self.water_widget = None
        self.folder_paths = []
        self.folders_collapsed = False
        self.task_area_height = None
        self.folder_sort_key = None
        self.folder_sort_desc = False

        # 贴边隐藏状态
        self.edge_hidden = False
        self.edge_hide_pos = None
        self.edge_restore_timer = None
        self._hide_anim = None
        self._show_anim = None
        self._rehide_timer = None
        self._should_rehide = False
        self._current_edge = None
        self._original_pos = None
        self._temp_shown = False
        self._restoring = False
        self._edge_show_pos = None
        self._pending_hide = False
        self._pending_hide_edge = None
        self._pending_hide_geometry = None
        self._pending_hide_timer = None

        # 加载保存的设置
        self.load_window_settings()
        
        # 开机自启动管理器
        self.autostart_manager = AutoStartManager()
        
        # 窗口交互状态
        self.dragging = False
        self.drag_position = None
        self.resizing = False
        self.resize_direction = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        
        # 窗口边框设置
        self.border_width = 3  # 边框宽度，用于调整大小检测（从5减小到3，提高检测精度）
        
        # 新增：光标状态同步定时器
        self.cursor_sync_timer = QTimer()
        self.cursor_sync_timer.timeout.connect(self.sync_cursor_state)
        self.cursor_sync_timer.start(50)  # 每50ms同步一次光标状态
        
        # 新增：记录上一次的光标位置和状态，用于检测变化
        self.last_cursor_pos = None
        self.last_cursor_shape = Qt.ArrowCursor
        
        self.setMinimumSize(300, 280)
        self.setMaximumSize(800, 1200)
        
        # 先设置基本窗口属性，再初始化UI
        self.setup_basic_window_properties()
        self.initUI()
        self.note_hotkey = NoteHotkey(QApplication.instance(), self.show_quick_note)
        if not self.note_hotkey.registered:
            QTimer.singleShot(300, self.show_note_hotkey_warning)
        
        # 延迟加载任务，确保窗口完全初始化后再加载数据
        QTimer.singleShot(100, self.delayed_task_load)
        
        # 检查是否是通过开机自启动启动的
        self.check_autostart_launch()
        
        # 监听窗口关闭事件以保存设置
        self.setAttribute(Qt.WA_DeleteOnClose, False)

    def setup_basic_window_properties(self):
        """设置基本窗口属性 - 优化版本"""
        # 先设置窗口标题和基本属性
        self.setWindowTitle("桌面任务小组件")
        
        # 设置窗口标志，但避免影响任务栏图标
        # 先使用基本窗口标志，后续再添加置顶等属性
        basic_flags = Qt.FramelessWindowHint | Qt.Window
        self.setWindowFlags(basic_flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口几何属性（初始值，后续会被加载的设置覆盖）
        self.setGeometry(100, 100, 350, 450)
        
        print("✅ 基本窗口属性设置完成")

    def setDpiSettings(self):
        """设置窗口DPI相关属性"""
        try:
            # 启用高DPI图标（如果属性存在）
            if hasattr(Qt, 'WA_UseHighDpiPixmaps'):
                self.setAttribute(Qt.WA_UseHighDpiPixmaps, True)
            print(f"✅ 窗口DPI设置完成，缩放因子: {self.devicePixelRatio()}")
        except Exception as e:
            print(f"⚠️ 窗口DPI设置失败: {e}")

    def setup_windows_specific(self):
        """Windows特定设置，优化任务栏图标显示 - 延迟执行"""
        if sys.platform == 'win32':
            # 延迟设置窗口置顶等属性，确保任务栏图标已正确显示
            QTimer.singleShot(500, self.enable_window_topmost)

    def enable_window_topmost(self):
        """启用窗口置顶属性（延迟执行）"""
        try:
            current_flags = self.windowFlags()
            new_flags = current_flags | Qt.WindowStaysOnTopHint
            self.setWindowFlags(new_flags)
            self.show()  # 重新显示窗口以应用新标志
            print("✅ 窗口置顶属性已启用")
        except Exception as e:
            print(f"⚠️ 启用窗口置顶属性失败: {e}")

    def check_autostart_launch(self):
        """检查是否是通过开机自启动启动的"""
        try:
            if self.autostart_manager.is_enabled():
                print("✓ 开机自启动已启用")
            else:
                print("✗✗ 开机自启动未启用")
        except Exception as e:
            print(f"检查开机自启动状态失败: {e}")

    def toggle_window_topmost(self):
        """切换窗口置顶状态"""
        is_topmost = self.pin_button.isChecked()

        try:
            current_flags = self.windowFlags()

            if is_topmost:
                new_flags = current_flags | Qt.WindowStaysOnTopHint
                self.pin_button.setText("📍")
                self.pin_button.setToolTip("取消置顶")
            else:
                new_flags = current_flags & ~Qt.WindowStaysOnTopHint
                self.pin_button.setText("📌")
                self.pin_button.setToolTip("窗口置顶")

            current_geometry = self.geometry()
            self.setWindowFlags(new_flags)
            self.setGeometry(current_geometry)
            self.show()

        except Exception as e:
            print(f"⚠️ 切换窗口置顶状态失败: {e}")
            self.pin_button.setChecked(not is_topmost)

    def delayed_task_load(self):
        """延迟加载任务，确保窗口完全初始化后再加载数据"""
        print("🕐 开始延迟加载任务...")

        # 加载任务数据
        self.load_tasks()
        self.habits = load_habits_from_json()
        self.water_reminder = load_water_reminder()
        self.water_widget.water = self.water_reminder
        self.water_widget._update_all()

        # 刷新任务显示
        self.refresh_task_display()

        print("✅ 任务加载完成，任务栏图标应正常显示")
        
        # 应用加载的窗口位置和大小
        self.apply_loaded_settings()

    def load_window_settings(self):
        """加载窗口设置"""
        try:
            settings = load_settings()
            self.folder_paths = settings.get('folder_shortcuts', [])
            self.folder_sort_key = settings.get('folder_sort_key')
            self.folder_sort_desc = settings.get('folder_sort_desc', False)
            self.folders_collapsed = settings.get('folders_collapsed', False)
            height = settings.get('task_area_height')
            self.task_area_height = height if isinstance(height, int) and height >= 40 else None
            
            # 加载窗口透明度
            if 'window_background_opacity' in settings:
                self.window_background_opacity = settings['window_background_opacity']
                print(f"✅ 加载窗口透明度: {self.window_background_opacity}")
            
            # 加载文字大小
            if 'current_font_size' in settings:
                self.current_font_size = settings['current_font_size']
                print(f"✅ 加载文字大小: {self.current_font_size}")
            
            # 加载文字透明度
            if 'current_font_opacity' in settings:
                self.current_font_opacity = settings['current_font_opacity']
                print(f"✅ 加载文字透明度: {self.current_font_opacity}")
            
            # 保存窗口几何信息用于后续应用
            self._loaded_geometry = settings.get('window_geometry', None)
            self._loaded_edge = settings.get('window_edge')
            self._loaded_screen = settings.get('window_screen')
            
        except Exception as e:
            print(f"⚠️ 加载窗口设置失败: {e}")
            self._loaded_geometry = None

    def apply_loaded_settings(self):
        """应用加载的设置（在窗口显示后调用）"""
        try:
            # 应用窗口位置和大小
            if hasattr(self, '_loaded_geometry') and self._loaded_geometry:
                parts = self._loaded_geometry.split(',')
                if len(parts) == 4:
                    x, y, width, height = map(int, parts)
                    screens = QApplication.screens()
                    screen = next((item for item in screens
                                   if item.name() == getattr(self, '_loaded_screen', None)), None)
                    screen = screen or QApplication.screenAt(QPoint(x, y)) or QApplication.primaryScreen()
                    bounds = screen.geometry()
                    available = screen.availableGeometry()
                    edge = getattr(self, '_loaded_edge', None)
                    # 兼容旧设置中保存的右侧隐藏坐标。
                    if edge is None and x + width > bounds.right() + 1:
                        edge = 'right'
                    self.resize(width, height)
                    width, height = self.width(), self.height()
                    x = max(available.left(), min(x, available.right() + 1 - width))
                    y = max(available.top(), min(y, available.bottom() + 1 - height))
                    if edge == 'right':
                        x = bounds.right() + 1 - width
                    elif edge == 'left':
                        x = bounds.left()
                    elif edge == 'top':
                        y = bounds.top()
                    self.move(x, y)
                    QTimer.singleShot(0, self._schedule_edge_hide)
                    print(f"✅ 应用窗口位置: ({x}, {y}), 大小: {width}x{height}")
            
            # 更新窗口样式
            self.update_window_style()
            
        except Exception as e:
            print(f"⚠️ 应用设置失败: {e}")

    def save_window_settings(self):
        """保存窗口设置"""
        try:
            position = self.pos()
            edge = self._check_near_edge()
            if (self.edge_hidden or self._restoring) and self._original_pos is not None:
                position = self._original_pos
                edge = self._current_edge
            screen = QApplication.screenAt(position) or QApplication.primaryScreen()
            settings = {
                'window_edge': edge,
                'window_screen': screen.name(),
                'window_background_opacity': self.window_background_opacity,
                'current_font_size': self.current_font_size,
                'current_font_opacity': self.current_font_opacity,
                'window_geometry': f"{position.x()},{position.y()},{self.width()},{self.height()}",
                'folder_shortcuts': self.folder_shortcuts.paths(),
                'folders_collapsed': self.folder_shortcuts.collapsed,
                'task_area_height': self.task_folder_splitter.preferred_task_height,
                'folder_sort_key': self.folder_shortcuts.sort_key,
                'folder_sort_desc': self.folder_shortcuts.sort_desc,
            }

            save_settings(settings)
            print(f"✅ 窗口设置已保存: 位置({self.x()}, {self.y()}), 大小({self.width()}x{self.height()})")

        except Exception as e:
            print(f"⚠️ 保存窗口设置失败: {e}")
