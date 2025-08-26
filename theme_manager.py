from PySide6 import QtCore, QtGui, QtWidgets
from typing import Dict, Any

class ThemeManager(QtCore.QObject):
    """主题管理器，提供深色和浅色主题"""
    
    # 定义主题变化信号
    theme_changed = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes = {
            "light": self._light_theme(),
            "dark": self._dark_theme()
        }
    
    def _light_theme(self) -> Dict[str, Any]:
        """浅色主题配置"""
        return {
            "name": "浅色主题",
            "colors": {
                "primary": "#007bff",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40",
                "background": "#ffffff",
                "surface": "#f8f9fa",
                "text_primary": "#212529",
                "text_secondary": "#6c757d",
                "border": "#e9ecef",
                "hover": "#e9ecef"
            },
            "styles": {
                "main_window": """
                    QMainWindow {
                        background-color: #f8f9fa;
                        color: #212529;
                    }
                """,
                "group_box": """
                    QGroupBox {
                        font-weight: bold;
                        border: 2px solid #e9ecef;
                        border-radius: 8px;
                        margin-top: 10px;
                        padding-top: 10px;
                        background-color: #ffffff;
                        color: #212529;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px 0 5px;
                        color: #495057;
                    }
                """,
                "status_card": """
                    QFrame {
                        background-color: #ffffff;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 16px;
                    }
                    QFrame:hover {
                        border-color: #007bff;
                        box-shadow: 0 2px 4px rgba(0,123,255,0.1);
                    }
                """,
                "button_primary": """
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #0056b3;
                    }
                    QPushButton:pressed {
                        background-color: #004085;
                    }
                    QPushButton:disabled {
                        background-color: #6c757d;
                    }
                """,
                "button_success": """
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                    QPushButton:checked {
                        background-color: #dc3545;
                    }
                    QPushButton:checked:hover {
                        background-color: #c82333;
                    }
                """,
                "input_field": """
                    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                        background-color: #ffffff;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        padding: 8px 12px;
                        font-size: 14px;
                        color: #495057;
                    }
                    QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                        border-color: #007bff;
                        outline: none;
                    }
                """,
                "log_area": """
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 12px;
                        color: #495057;
                        padding: 8px;
                    }
                """,
                "chart_background": "#ffffff",
                "chart_grid": "#e9ecef",
                "chart_text": "#495057"
            }
        }
    
    def _dark_theme(self) -> Dict[str, Any]:
        """深色主题配置"""
        return {
            "name": "深色主题",
            "colors": {
                "primary": "#0d6efd",
                "secondary": "#6c757d",
                "success": "#198754",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#0dcaf0",
                "light": "#f8f9fa",
                "dark": "#212529",
                "background": "#1a1a1a",
                "surface": "#2d2d2d",
                "text_primary": "#ffffff",
                "text_secondary": "#adb5bd",
                "border": "#495057",
                "hover": "#3d3d3d"
            },
            "styles": {
                "main_window": """
                    QMainWindow {
                        background-color: #1a1a1a;
                        color: #ffffff;
                    }
                """,
                "group_box": """
                    QGroupBox {
                        font-weight: bold;
                        border: 2px solid #495057;
                        border-radius: 8px;
                        margin-top: 10px;
                        padding-top: 10px;
                        background-color: #2d2d2d;
                        color: #ffffff;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px 0 5px;
                        color: #adb5bd;
                    }
                """,
                "status_card": """
                    QFrame {
                        background-color: #2d2d2d;
                        border: 1px solid #495057;
                        border-radius: 8px;
                        padding: 16px;
                    }
                    QFrame:hover {
                        border-color: #0d6efd;
                        box-shadow: 0 2px 4px rgba(13,110,253,0.2);
                    }
                """,
                "button_primary": """
                    QPushButton {
                        background-color: #0d6efd;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #0b5ed7;
                    }
                    QPushButton:pressed {
                        background-color: #0a58ca;
                    }
                    QPushButton:disabled {
                        background-color: #6c757d;
                    }
                """,
                "button_success": """
                    QPushButton {
                        background-color: #198754;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #157347;
                    }
                    QPushButton:checked {
                        background-color: #dc3545;
                    }
                    QPushButton:checked:hover {
                        background-color: #bb2d3b;
                    }
                """,
                "input_field": """
                    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                        background-color: #2d2d2d;
                        border: 1px solid #495057;
                        border-radius: 4px;
                        padding: 8px 12px;
                        font-size: 14px;
                        color: #ffffff;
                    }
                    QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                        border-color: #0d6efd;
                        outline: none;
                    }
                """,
                "log_area": """
                    QTextEdit {
                        background-color: #1a1a1a;
                        border: 1px solid #495057;
                        border-radius: 4px;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 12px;
                        color: #adb5bd;
                        padding: 8px;
                    }
                """,
                "chart_background": "#2d2d2d",
                "chart_grid": "#495057",
                "chart_text": "#adb5bd"
            }
        }
    
    def get_current_theme(self) -> Dict[str, Any]:
        """获取当前主题"""
        return self.themes[self.current_theme]
    
    def set_theme(self, theme_name: str):
        """设置主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme_changed.emit()
    
    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.theme_changed.emit()
    
    def apply_theme_to_widget(self, widget: QtWidgets.QWidget, style_key: str = None):
        """将主题应用到指定组件"""
        theme = self.get_current_theme()
        
        if style_key and style_key in theme["styles"]:
            widget.setStyleSheet(theme["styles"][style_key])
        else:
            # 应用默认样式
            if isinstance(widget, QtWidgets.QMainWindow):
                widget.setStyleSheet(theme["styles"]["main_window"])
            elif isinstance(widget, QtWidgets.QGroupBox):
                widget.setStyleSheet(theme["styles"]["group_box"])
    
    def get_color(self, color_name: str) -> str:
        """获取主题颜色"""
        theme = self.get_current_theme()
        return theme["colors"].get(color_name, "#000000")
    
    def get_style(self, style_name: str) -> str:
        """获取样式字符串"""
        theme = self.get_current_theme()
        return theme["styles"].get(style_name, "")

class ThemeAwareWidget(QtWidgets.QWidget):
    """支持主题的基础组件"""
    
    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.apply_theme()
    
    def apply_theme(self):
        """应用主题，子类应重写此方法"""
        pass
    
    def update_theme(self):
        """更新主题"""
        self.apply_theme()
        self.update()

class ThemedStatusCard(QtWidgets.QFrame):
    """支持主题的状态卡片"""
    
    def __init__(self, theme_manager: ThemeManager, title: str, value: str = "0", unit: str = "", color_key: str = "primary", parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.title = title
        self.unit = unit
        self.color_key = color_key
        self.setup_ui(value)
        self.apply_theme()
        
        # 连接主题变化信号
        self.theme_manager.theme_changed.connect(self.apply_theme)
    
    def setup_ui(self, value: str):
        self.setFrameStyle(QtWidgets.QFrame.Box)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        self.title_label = QtWidgets.QLabel(self.title)
        layout.addWidget(self.title_label)
        
        # 数值
        value_layout = QtWidgets.QHBoxLayout()
        self.value_label = QtWidgets.QLabel(value)
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            self.unit_label = QtWidgets.QLabel(self.unit)
            value_layout.addWidget(self.unit_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        layout.addStretch()
    
    def apply_theme(self):
        theme = self.theme_manager.get_current_theme()
        
        # 应用卡片样式
        self.setStyleSheet(theme["styles"]["status_card"])
        
        # 应用文本颜色
        title_color = theme["colors"]["text_secondary"]
        value_color = theme["colors"][self.color_key]
        unit_color = theme["colors"]["text_secondary"]
        
        self.title_label.setStyleSheet(f"color: {title_color}; font-size: 12px; font-weight: bold;")
        self.value_label.setStyleSheet(f"color: {value_color}; font-size: 24px; font-weight: bold;")
        
        if hasattr(self, 'unit_label'):
            self.unit_label.setStyleSheet(f"color: {unit_color}; font-size: 14px;")
    
    def update_value(self, value: str):
        """更新显示值"""
        self.value_label.setText(value)

class ThemedButton(QtWidgets.QPushButton):
    """支持主题的按钮组件"""
    
    def __init__(self, theme_manager: ThemeManager, text: str = "", style: str = "primary", parent=None):
        super().__init__(text, parent)
        self.theme_manager = theme_manager
        self.style_key = f"button_{style}"
        self.apply_theme()
        
        # 连接主题变化信号
        self.theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        """应用主题样式"""
        theme = self.theme_manager.get_current_theme()
        if self.style_key in theme["styles"]:
            self.setStyleSheet(theme["styles"][self.style_key])

# 全局主题管理器实例
_global_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """获取全局主题管理器"""
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = ThemeManager()
    return _global_theme_manager

def set_global_theme(theme_name: str):
    """设置全局主题"""
    theme_manager = get_theme_manager()
    theme_manager.set_theme(theme_name)

def toggle_global_theme():
    """切换全局主题"""
    theme_manager = get_theme_manager()
    theme_manager.toggle_theme()