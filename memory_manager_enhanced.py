import sys
import os
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
import psutil
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QTimer, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtCore import QDateTime
from theme_manager import get_theme_manager, ThemedStatusCard, ThemedButton

def _config_dir():
    """获取配置目录"""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", ""), "MemoryManager")
    else:
        return os.path.join(os.path.expanduser("~"), ".memory_manager")

CONFIG_PATH = os.path.join(_config_dir(), "config.json")

class MemoryWorker(QThread):
    """内存工作线程"""
    status_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.target_percent = 50.0
        self.allocated_memory = []
        self.chunk_size = 1024 * 1024  # 1MB chunks
        self.max_chunks = 1000
        
    def set_target(self, percent: float):
        """设置目标内存使用率"""
        self.target_percent = max(0.0, min(95.0, percent))
        
    def start_work(self):
        """开始工作"""
        self.running = True
        if not self.isRunning():
            self.start()
            
    def stop_work(self):
        """停止工作"""
        self.running = False
        self._release_memory()
        
    def _release_memory(self):
        """释放已分配的内存"""
        self.allocated_memory.clear()
        
    def run(self):
        """主工作循环"""
        while self.running:
            try:
                # 获取当前内存使用情况
                memory = psutil.virtual_memory()
                current_percent = memory.percent
                
                # 计算需要调整的内存量
                if current_percent < self.target_percent:
                    # 需要增加内存使用
                    if len(self.allocated_memory) < self.max_chunks:
                        try:
                            chunk = bytearray(self.chunk_size)
                            # 写入一些数据防止被优化
                            for i in range(0, len(chunk), 4096):
                                chunk[i] = i % 256
                            self.allocated_memory.append(chunk)
                        except MemoryError:
                            pass
                elif current_percent > self.target_percent + 2:
                    # 需要减少内存使用
                    if self.allocated_memory:
                        self.allocated_memory.pop()
                
                # 发送状态更新
                status = {
                    'current_percent': current_percent,
                    'target_percent': self.target_percent,
                    'allocated_chunks': len(self.allocated_memory),
                    'allocated_mb': len(self.allocated_memory) * self.chunk_size / (1024 * 1024),
                    'total_memory_gb': memory.total / (1024**3),
                    'available_memory_gb': memory.available / (1024**3),
                    'used_memory_gb': memory.used / (1024**3)
                }
                
                self.status_updated.emit(status)
                
                # 短暂休眠
                self.msleep(500)
                
            except Exception as e:
                print(f"内存工作线程错误: {e}")
                self.msleep(1000)

class RealTimeMemoryChart(QtWidgets.QWidget):
    """实时内存使用率图表"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.data_points = []
        self.max_points = 60  # 显示最近60个数据点
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建图表
        self.chart = QChart()
        self.chart.setTitle("内存使用率趋势")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 创建数据系列
        self.current_series = QLineSeries()
        self.current_series.setName("当前使用率")
        
        self.target_series = QLineSeries()
        self.target_series.setName("目标使用率")
        
        self.chart.addSeries(self.current_series)
        self.chart.addSeries(self.target_series)
        
        # 设置坐标轴
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("hh:mm:ss")
        self.axis_x.setTitleText("时间")
        
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText("内存使用率 (%)")
        
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        
        self.current_series.attachAxis(self.axis_x)
        self.current_series.attachAxis(self.axis_y)
        self.target_series.attachAxis(self.axis_x)
        self.target_series.attachAxis(self.axis_y)
        
        # 创建图表视图
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        
        layout.addWidget(self.chart_view)
        
        self.apply_theme()
        
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_current_theme()
        
        # 设置图表背景和文本颜色
        self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["background"])))
        self.chart.setTitleBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_primary"])))
        
        # 设置系列颜色
        pen_current = QtGui.QPen(QtGui.QColor(theme["colors"]["primary"]), 2)
        pen_target = QtGui.QPen(QtGui.QColor(theme["colors"]["success"]), 2, QtCore.Qt.DashLine)
        
        self.current_series.setPen(pen_current)
        self.target_series.setPen(pen_target)
        
        # 设置坐标轴颜色
        axis_pen = QtGui.QPen(QtGui.QColor(theme["colors"]["text_secondary"]))
        self.axis_x.setLinePen(axis_pen)
        self.axis_y.setLinePen(axis_pen)
        self.axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_secondary"])))
        self.axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_secondary"])))
        
    def add_data_point(self, current_percent: float, target_percent: float):
        """添加数据点"""
        current_time = QDateTime.currentDateTime()
        timestamp = current_time.toMSecsSinceEpoch()
        
        # 添加到当前使用率系列
        self.current_series.append(timestamp, current_percent)
        self.target_series.append(timestamp, target_percent)
        
        # 保持数据点数量限制
        if self.current_series.count() > self.max_points:
            self.current_series.removePoints(0, self.current_series.count() - self.max_points)
            self.target_series.removePoints(0, self.target_series.count() - self.max_points)
        
        # 更新X轴范围
        if self.current_series.count() > 1:
            min_time = QDateTime.fromMSecsSinceEpoch(int(self.current_series.at(0).x()))
            max_time = QDateTime.fromMSecsSinceEpoch(int(self.current_series.at(self.current_series.count()-1).x()))
            self.axis_x.setRange(min_time, max_time)

class EnhancedMemoryManagerWindow(QMainWindow):
    """增强版内存管理器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = get_theme_manager()
        self.worker = MemoryWorker()
        self.worker.status_updated.connect(self.update_status)
        
        self.setup_ui()
        self.load_config()
        self.apply_theme()
        
        # 设置定时器用于UI更新
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)  # 每秒更新一次
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("增强版内存管理器 v2.0")
        self.setMinimumSize(1000, 700)
        
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部工具栏
        self.create_toolbar(main_layout)
        
        # 状态卡片区域
        self.create_status_cards(main_layout)
        
        # 图表和控制区域
        content_layout = QHBoxLayout()
        
        # 左侧：实时图表
        chart_group = QtWidgets.QGroupBox("实时监控")
        chart_layout = QVBoxLayout(chart_group)
        
        self.memory_chart = RealTimeMemoryChart(self.theme_manager)
        chart_layout.addWidget(self.memory_chart)
        
        content_layout.addWidget(chart_group, 2)
        
        # 右侧：控制面板
        control_group = QtWidgets.QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_group)
        
        self.create_control_panel(control_layout)
        
        content_layout.addWidget(control_group, 1)
        
        main_layout.addLayout(content_layout)
        
        # 底部日志区域
        self.create_log_area(main_layout)
        
    def create_toolbar(self, parent_layout):
        """创建工具栏"""
        toolbar_layout = QHBoxLayout()
        
        # 主题切换按钮
        self.theme_button = ThemedButton(self.theme_manager, "🌙 深色主题", "primary")
        self.theme_button.clicked().connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)
        
        toolbar_layout.addStretch()
        
        # 状态指示器
        self.status_indicator = QtWidgets.QLabel("● 已停止")
        toolbar_layout.addWidget(self.status_indicator)
        
        parent_layout.addLayout(toolbar_layout)
        
    def create_status_cards(self, parent_layout):
        """创建状态卡片"""
        cards_layout = QGridLayout()
        
        # 创建状态卡片
        self.current_usage_card = ThemedStatusCard(self.theme_manager, "当前使用率", "0", "%", "primary")
        self.target_usage_card = ThemedStatusCard(self.theme_manager, "目标使用率", "0", "%", "success")
        self.allocated_memory_card = ThemedStatusCard(self.theme_manager, "已分配内存", "0", "MB", "info")
        self.total_memory_card = ThemedStatusCard(self.theme_manager, "总内存", "0", "GB", "secondary")
        
        cards_layout.addWidget(self.current_usage_card, 0, 0)
        cards_layout.addWidget(self.target_usage_card, 0, 1)
        cards_layout.addWidget(self.allocated_memory_card, 0, 2)
        cards_layout.addWidget(self.total_memory_card, 0, 3)
        
        parent_layout.addLayout(cards_layout)
        
    def create_control_panel(self, parent_layout):
        """创建控制面板"""
        # 目标设置
        target_layout = QHBoxLayout()
        target_layout.addWidget(QtWidgets.QLabel("目标使用率:"))
        
        self.target_spinbox = QtWidgets.QDoubleSpinBox()
        self.target_spinbox.setRange(10.0, 95.0)
        self.target_spinbox.setValue(50.0)
        self.target_spinbox.setSuffix("%")
        self.target_spinbox.valueChanged.connect(self.on_target_changed)
        target_layout.addWidget(self.target_spinbox)
        
        parent_layout.addLayout(target_layout)
        
        # 控制按钮
        self.start_button = ThemedButton(self.theme_manager, "开始", "success")
        self.start_button.setCheckable(True)
        self.start_button.clicked().connect(self.toggle_worker)
        parent_layout.addWidget(self.start_button)
        
        # 预设模式
        parent_layout.addWidget(QtWidgets.QLabel("快速设置:"))
        
        preset_layout = QVBoxLayout()
        
        presets = [
            ("轻度测试", 30),
            ("中度测试", 50),
            ("重度测试", 70),
            ("极限测试", 85)
        ]
        
        for name, value in presets:
            btn = QtWidgets.QPushButton(f"{name} ({value}%)")
            btn.clicked.connect(lambda checked, v=value: self.set_preset(v))
            preset_layout.addWidget(btn)
        
        parent_layout.addLayout(preset_layout)
        
        parent_layout.addStretch()
        
        # 系统信息
        info_group = QtWidgets.QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)
        
        memory = psutil.virtual_memory()
        info_layout.addWidget(QtWidgets.QLabel(f"总内存: {memory.total / (1024**3):.1f} GB"))
        info_layout.addWidget(QtWidgets.QLabel(f"可用内存: {memory.available / (1024**3):.1f} GB"))
        
        parent_layout.addWidget(info_group)
        
    def create_log_area(self, parent_layout):
        """创建日志区域"""
        log_group = QtWidgets.QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        parent_layout.addWidget(log_group)
        
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_current_theme()
        
        # 应用主窗口样式
        self.setStyleSheet(theme["styles"]["main_window"])
        
        # 应用组件样式
        for group_box in self.findChildren(QtWidgets.QGroupBox):
            group_box.setStyleSheet(theme["styles"]["group_box"])
        
        for spinbox in self.findChildren(QtWidgets.QDoubleSpinBox):
            spinbox.setStyleSheet(theme["styles"]["input_field"])
        
        self.log_text.setStyleSheet(theme["styles"]["log_area"])
        
        # 更新状态卡片主题
        for card in [self.current_usage_card, self.target_usage_card, 
                    self.allocated_memory_card, self.total_memory_card]:
            card.apply_theme()
        
        # 更新图表主题
        self.memory_chart.apply_theme()
        
        # 更新主题按钮文本
        if self.theme_manager.current_theme == "dark":
            self.theme_button.setText("☀️ 浅色主题")
        else:
            self.theme_button.setText("🌙 深色主题")
        
    def toggle_theme(self):
        """切换主题"""
        self.theme_manager.toggle_theme()
        self.apply_theme()
        self.log_message(f"已切换到{self.theme_manager.get_current_theme()['name']}")
        
    def set_preset(self, value: int):
        """设置预设值"""
        self.target_spinbox.setValue(value)
        self.log_message(f"设置目标使用率为 {value}%")
        
    def on_target_changed(self, value: float):
        """目标值改变"""
        if self.worker.isRunning():
            self.worker.set_target(value)
            self.log_message(f"目标使用率已更新为 {value:.1f}%")
        
    def toggle_worker(self):
        """切换工作状态"""
        if self.start_button.isChecked():
            self.worker.set_target(self.target_spinbox.value())
            self.worker.start_work()
            self.start_button.setText("停止")
            self.status_indicator.setText("● 运行中")
            self.status_indicator.setStyleSheet(f"color: {self.theme_manager.get_color('success')};")
            self.log_message("内存管理器已启动")
        else:
            self.worker.stop_work()
            self.start_button.setText("开始")
            self.status_indicator.setText("● 已停止")
            self.status_indicator.setStyleSheet(f"color: {self.theme_manager.get_color('danger')};")
            self.log_message("内存管理器已停止")
        
    def update_status(self, status: Dict[str, Any]):
        """更新状态显示"""
        # 更新状态卡片
        self.current_usage_card.update_value(f"{status['current_percent']:.1f}")
        self.target_usage_card.update_value(f"{status['target_percent']:.1f}")
        self.allocated_memory_card.update_value(f"{status['allocated_mb']:.0f}")
        self.total_memory_card.update_value(f"{status['total_memory_gb']:.1f}")
        
        # 更新图表
        self.memory_chart.add_data_point(
            status['current_percent'], 
            status['target_percent']
        )
        
    def update_ui(self):
        """定期更新UI"""
        if not self.worker.isRunning():
            # 显示当前系统内存使用情况
            memory = psutil.virtual_memory()
            self.current_usage_card.update_value(f"{memory.percent:.1f}")
            self.total_memory_card.update_value(f"{memory.total / (1024**3):.1f}")
        
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.target_spinbox.setValue(config.get('target_percent', 50.0))
                    theme_name = config.get('theme', 'light')
                    self.theme_manager.set_theme(theme_name)
                    self.apply_theme()
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
            
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            config = {
                'target_percent': self.target_spinbox.value(),
                'theme': self.theme_manager.current_theme
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"保存配置失败: {e}")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.worker.stop_work()
        self.worker.wait(3000)  # 等待最多3秒
        self.save_config()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("增强版内存管理器")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("系统工具")
    
    # 创建主窗口
    window = EnhancedMemoryManagerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()