import sys
import os
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import psutil
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QTimer, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis, QPieSeries, QPieSlice
from PySide6.QtCore import QDateTime
from theme_manager import get_theme_manager, ThemedStatusCard, ThemedButton

def _config_dir():
    """获取配置目录"""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", ""), "SystemDashboard")
    else:
        return os.path.join(os.path.expanduser("~"), ".system_dashboard")

CONFIG_PATH = os.path.join(_config_dir(), "config.json")

class SystemMonitor(QThread):
    """系统监控线程"""
    data_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.update_interval = 1000  # 1秒更新间隔
        
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        if not self.isRunning():
            self.start()
            
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        
    def run(self):
        """监控主循环"""
        while self.running:
            try:
                # 收集系统信息
                data = self.collect_system_data()
                self.data_updated.emit(data)
                self.msleep(self.update_interval)
            except Exception as e:
                print(f"系统监控错误: {e}")
                self.msleep(5000)
                
    def collect_system_data(self) -> Dict[str, Any]:
        """收集系统数据"""
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存信息
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘信息
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # 网络信息
        network_io = psutil.net_io_counters()
        
        # 进程信息
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按CPU使用率排序，取前10个
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        top_processes = processes[:10]
        
        return {
            'timestamp': datetime.now(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'freq_current': cpu_freq.current if cpu_freq else 0,
                'freq_max': cpu_freq.max if cpu_freq else 0
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            },
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            },
            'network': {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            },
            'processes': top_processes
        }

class RealTimeChart(QtWidgets.QWidget):
    """实时图表组件"""
    
    def __init__(self, theme_manager, title: str, y_label: str, max_points: int = 60, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.title = title
        self.y_label = y_label
        self.max_points = max_points
        self.series_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建图表
        self.chart = QChart()
        self.chart.setTitle(self.title)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 设置坐标轴
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("hh:mm:ss")
        self.axis_x.setTitleText("时间")
        
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText(self.y_label)
        
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        
        # 创建图表视图
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        
        layout.addWidget(self.chart_view)
        self.apply_theme()
        
    def add_series(self, name: str, color: str):
        """添加数据系列"""
        series = QLineSeries()
        series.setName(name)
        
        pen = QtGui.QPen(QtGui.QColor(color), 2)
        series.setPen(pen)
        
        self.chart.addSeries(series)
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)
        
        self.series_data[name] = series
        
    def add_data_point(self, series_name: str, value: float):
        """添加数据点"""
        if series_name not in self.series_data:
            return
            
        series = self.series_data[series_name]
        current_time = QDateTime.currentDateTime()
        timestamp = current_time.toMSecsSinceEpoch()
        
        series.append(timestamp, value)
        
        # 保持数据点数量限制
        if series.count() > self.max_points:
            series.removePoints(0, series.count() - self.max_points)
        
        # 更新X轴范围
        if series.count() > 1:
            min_time = QDateTime.fromMSecsSinceEpoch(int(series.at(0).x()))
            max_time = QDateTime.fromMSecsSinceEpoch(int(series.at(series.count()-1).x()))
            self.axis_x.setRange(min_time, max_time)
            
    def set_y_range(self, min_val: float, max_val: float):
        """设置Y轴范围"""
        self.axis_y.setRange(min_val, max_val)
        
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_current_theme()
        
        # 设置图表背景和文本颜色
        self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["background"])))
        self.chart.setTitleBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_primary"])))
        
        # 设置坐标轴颜色
        axis_pen = QtGui.QPen(QtGui.QColor(theme["colors"]["text_secondary"]))
        self.axis_x.setLinePen(axis_pen)
        self.axis_y.setLinePen(axis_pen)
        self.axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_secondary"])))
        self.axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor(theme["colors"]["text_secondary"])))

class ProcessTable(QtWidgets.QTableWidget):
    """进程表格"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["PID", "进程名", "CPU %", "内存 %"])
        self.setRowCount(10)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # 设置列宽
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        
        self.apply_theme()
        
    def update_processes(self, processes: List[Dict[str, Any]]):
        """更新进程列表"""
        for i, proc in enumerate(processes[:10]):
            if i >= self.rowCount():
                break
                
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(str(proc.get('pid', 'N/A'))))
            self.setItem(i, 1, QtWidgets.QTableWidgetItem(proc.get('name', 'N/A')))
            self.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}"))
            self.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}"))
            
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_current_theme()
        
        style = f"""
            QTableWidget {{
                background-color: {theme["colors"]["background"]};
                color: {theme["colors"]["text_primary"]};
                border: 1px solid {theme["colors"]["border"]};
                gridline-color: {theme["colors"]["border"]};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme["colors"]["border"]};
            }}
            QTableWidget::item:selected {{
                background-color: {theme["colors"]["primary"]};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {theme["colors"]["surface"]};
                color: {theme["colors"]["text_primary"]};
                padding: 8px;
                border: 1px solid {theme["colors"]["border"]};
                font-weight: bold;
            }}
        """
        self.setStyleSheet(style)

class SystemDashboard(QMainWindow):
    """系统监控仪表盘"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = get_theme_manager()
        self.monitor = SystemMonitor()
        self.monitor.data_updated.connect(self.update_dashboard)
        
        # 网络统计
        self.last_network_data = None
        
        self.setup_ui()
        self.load_config()
        self.apply_theme()
        
        # 启动监控
        self.monitor.start_monitoring()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("系统监控仪表盘 v1.0")
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部工具栏
        self.create_toolbar(main_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 概览标签页
        self.create_overview_tab()
        
        # CPU标签页
        self.create_cpu_tab()
        
        # 内存标签页
        self.create_memory_tab()
        
        # 磁盘标签页
        self.create_disk_tab()
        
        # 网络标签页
        self.create_network_tab()
        
        # 进程标签页
        self.create_process_tab()
        
        main_layout.addWidget(self.tab_widget)
        
    def create_toolbar(self, parent_layout):
        """创建工具栏"""
        toolbar_layout = QHBoxLayout()
        
        # 主题切换按钮
        self.theme_button = ThemedButton(self.theme_manager, "🌙 深色主题", "primary")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)
        
        # 刷新按钮
        refresh_button = ThemedButton(self.theme_manager, "🔄 刷新", "secondary")
        refresh_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_button)
        
        toolbar_layout.addStretch()
        
        # 系统时间
        self.time_label = QtWidgets.QLabel()
        self.update_time()
        toolbar_layout.addWidget(self.time_label)
        
        # 定时更新时间
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        
        parent_layout.addLayout(toolbar_layout)
        
    def create_overview_tab(self):
        """创建概览标签页"""
        overview_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(overview_widget)
        
        # 状态卡片
        cards_layout = QGridLayout()
        
        self.cpu_card = ThemedStatusCard(self.theme_manager, "CPU使用率", "0", "%", "primary")
        self.memory_card = ThemedStatusCard(self.theme_manager, "内存使用率", "0", "%", "info")
        self.disk_card = ThemedStatusCard(self.theme_manager, "磁盘使用率", "0", "%", "warning")
        self.network_card = ThemedStatusCard(self.theme_manager, "网络活动", "0", "MB/s", "success")
        
        cards_layout.addWidget(self.cpu_card, 0, 0)
        cards_layout.addWidget(self.memory_card, 0, 1)
        cards_layout.addWidget(self.disk_card, 0, 2)
        cards_layout.addWidget(self.network_card, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # 综合图表
        charts_layout = QHBoxLayout()
        
        # 系统资源使用率图表
        self.overview_chart = RealTimeChart(self.theme_manager, "系统资源使用率", "使用率 (%)")
        self.overview_chart.add_series("CPU", self.theme_manager.get_color("primary"))
        self.overview_chart.add_series("内存", self.theme_manager.get_color("info"))
        self.overview_chart.add_series("磁盘", self.theme_manager.get_color("warning"))
        
        charts_layout.addWidget(self.overview_chart)
        
        layout.addLayout(charts_layout)
        
        self.tab_widget.addTab(overview_widget, "概览")
        
    def create_cpu_tab(self):
        """创建CPU标签页"""
        cpu_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(cpu_widget)
        
        # CPU信息卡片
        info_layout = QHBoxLayout()
        
        self.cpu_usage_card = ThemedStatusCard(self.theme_manager, "当前使用率", "0", "%", "primary")
        self.cpu_cores_card = ThemedStatusCard(self.theme_manager, "核心数", "0", "个", "secondary")
        self.cpu_freq_card = ThemedStatusCard(self.theme_manager, "当前频率", "0", "MHz", "info")
        
        info_layout.addWidget(self.cpu_usage_card)
        info_layout.addWidget(self.cpu_cores_card)
        info_layout.addWidget(self.cpu_freq_card)
        
        layout.addLayout(info_layout)
        
        # CPU使用率图表
        self.cpu_chart = RealTimeChart(self.theme_manager, "CPU使用率趋势", "使用率 (%)")
        self.cpu_chart.add_series("CPU使用率", self.theme_manager.get_color("primary"))
        
        layout.addWidget(self.cpu_chart)
        
        self.tab_widget.addTab(cpu_widget, "CPU")
        
    def create_memory_tab(self):
        """创建内存标签页"""
        memory_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(memory_widget)
        
        # 内存信息卡片
        info_layout = QHBoxLayout()
        
        self.memory_usage_card = ThemedStatusCard(self.theme_manager, "内存使用率", "0", "%", "info")
        self.memory_total_card = ThemedStatusCard(self.theme_manager, "总内存", "0", "GB", "secondary")
        self.memory_available_card = ThemedStatusCard(self.theme_manager, "可用内存", "0", "GB", "success")
        self.swap_usage_card = ThemedStatusCard(self.theme_manager, "交换分区", "0", "%", "warning")
        
        info_layout.addWidget(self.memory_usage_card)
        info_layout.addWidget(self.memory_total_card)
        info_layout.addWidget(self.memory_available_card)
        info_layout.addWidget(self.swap_usage_card)
        
        layout.addLayout(info_layout)
        
        # 内存使用图表
        self.memory_chart = RealTimeChart(self.theme_manager, "内存使用趋势", "使用率 (%)")
        self.memory_chart.add_series("内存使用率", self.theme_manager.get_color("info"))
        self.memory_chart.add_series("交换分区", self.theme_manager.get_color("warning"))
        
        layout.addWidget(self.memory_chart)
        
        self.tab_widget.addTab(memory_widget, "内存")
        
    def create_disk_tab(self):
        """创建磁盘标签页"""
        disk_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(disk_widget)
        
        # 磁盘信息卡片
        info_layout = QHBoxLayout()
        
        self.disk_usage_card = ThemedStatusCard(self.theme_manager, "磁盘使用率", "0", "%", "warning")
        self.disk_total_card = ThemedStatusCard(self.theme_manager, "总容量", "0", "GB", "secondary")
        self.disk_free_card = ThemedStatusCard(self.theme_manager, "可用空间", "0", "GB", "success")
        self.disk_io_card = ThemedStatusCard(self.theme_manager, "磁盘IO", "0", "MB/s", "info")
        
        info_layout.addWidget(self.disk_usage_card)
        info_layout.addWidget(self.disk_total_card)
        info_layout.addWidget(self.disk_free_card)
        info_layout.addWidget(self.disk_io_card)
        
        layout.addLayout(info_layout)
        
        # 磁盘使用图表
        self.disk_chart = RealTimeChart(self.theme_manager, "磁盘使用趋势", "使用率 (%)")
        self.disk_chart.add_series("磁盘使用率", self.theme_manager.get_color("warning"))
        
        layout.addWidget(self.disk_chart)
        
        self.tab_widget.addTab(disk_widget, "磁盘")
        
    def create_network_tab(self):
        """创建网络标签页"""
        network_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(network_widget)
        
        # 网络信息卡片
        info_layout = QHBoxLayout()
        
        self.network_upload_card = ThemedStatusCard(self.theme_manager, "上传速度", "0", "MB/s", "success")
        self.network_download_card = ThemedStatusCard(self.theme_manager, "下载速度", "0", "MB/s", "info")
        self.network_total_sent_card = ThemedStatusCard(self.theme_manager, "总发送", "0", "GB", "secondary")
        self.network_total_recv_card = ThemedStatusCard(self.theme_manager, "总接收", "0", "GB", "secondary")
        
        info_layout.addWidget(self.network_upload_card)
        info_layout.addWidget(self.network_download_card)
        info_layout.addWidget(self.network_total_sent_card)
        info_layout.addWidget(self.network_total_recv_card)
        
        layout.addLayout(info_layout)
        
        # 网络速度图表
        self.network_chart = RealTimeChart(self.theme_manager, "网络速度趋势", "速度 (MB/s)")
        self.network_chart.add_series("上传", self.theme_manager.get_color("success"))
        self.network_chart.add_series("下载", self.theme_manager.get_color("info"))
        self.network_chart.set_y_range(0, 10)  # 初始范围0-10 MB/s
        
        layout.addWidget(self.network_chart)
        
        self.tab_widget.addTab(network_widget, "网络")
        
    def create_process_tab(self):
        """创建进程标签页"""
        process_widget = QtWidgets.QWidget()
        layout = QVBoxLayout(process_widget)
        
        # 进程表格
        self.process_table = ProcessTable(self.theme_manager)
        layout.addWidget(self.process_table)
        
        self.tab_widget.addTab(process_widget, "进程")
        
    def update_dashboard(self, data: Dict[str, Any]):
        """更新仪表盘数据"""
        # 更新概览卡片
        self.cpu_card.update_value(f"{data['cpu']['percent']:.1f}")
        self.memory_card.update_value(f"{data['memory']['percent']:.1f}")
        self.disk_card.update_value(f"{data['disk']['percent']:.1f}")
        
        # 计算网络速度
        if self.last_network_data:
            time_diff = (data['timestamp'] - self.last_network_data['timestamp']).total_seconds()
            if time_diff > 0:
                upload_speed = (data['network']['bytes_sent'] - self.last_network_data['network']['bytes_sent']) / time_diff / (1024*1024)
                download_speed = (data['network']['bytes_recv'] - self.last_network_data['network']['bytes_recv']) / time_diff / (1024*1024)
                
                self.network_card.update_value(f"{max(upload_speed, download_speed):.1f}")
                
                # 更新网络图表
                self.network_chart.add_data_point("上传", upload_speed)
                self.network_chart.add_data_point("下载", download_speed)
                
                # 更新网络卡片
                self.network_upload_card.update_value(f"{upload_speed:.1f}")
                self.network_download_card.update_value(f"{download_speed:.1f}")
        
        self.last_network_data = data
        
        # 更新概览图表
        self.overview_chart.add_data_point("CPU", data['cpu']['percent'])
        self.overview_chart.add_data_point("内存", data['memory']['percent'])
        self.overview_chart.add_data_point("磁盘", data['disk']['percent'])
        
        # 更新CPU标签页
        self.cpu_usage_card.update_value(f"{data['cpu']['percent']:.1f}")
        self.cpu_cores_card.update_value(str(data['cpu']['count']))
        self.cpu_freq_card.update_value(f"{data['cpu']['freq_current']:.0f}")
        self.cpu_chart.add_data_point("CPU使用率", data['cpu']['percent'])
        
        # 更新内存标签页
        self.memory_usage_card.update_value(f"{data['memory']['percent']:.1f}")
        self.memory_total_card.update_value(f"{data['memory']['total'] / (1024**3):.1f}")
        self.memory_available_card.update_value(f"{data['memory']['available'] / (1024**3):.1f}")
        self.swap_usage_card.update_value(f"{data['memory']['swap_percent']:.1f}")
        self.memory_chart.add_data_point("内存使用率", data['memory']['percent'])
        self.memory_chart.add_data_point("交换分区", data['memory']['swap_percent'])
        
        # 更新磁盘标签页
        self.disk_usage_card.update_value(f"{data['disk']['percent']:.1f}")
        self.disk_total_card.update_value(f"{data['disk']['total'] / (1024**3):.0f}")
        self.disk_free_card.update_value(f"{data['disk']['free'] / (1024**3):.0f}")
        self.disk_chart.add_data_point("磁盘使用率", data['disk']['percent'])
        
        # 更新网络总量
        self.network_total_sent_card.update_value(f"{data['network']['bytes_sent'] / (1024**3):.1f}")
        self.network_total_recv_card.update_value(f"{data['network']['bytes_recv'] / (1024**3):.1f}")
        
        # 更新进程表格
        self.process_table.update_processes(data['processes'])
        
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def toggle_theme(self):
        """切换主题"""
        self.theme_manager.toggle_theme()
        self.apply_theme()
        
    def refresh_data(self):
        """刷新数据"""
        # 重启监控线程
        self.monitor.stop_monitoring()
        self.monitor.wait(1000)
        self.monitor.start_monitoring()
        
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_current_theme()
        
        # 应用主窗口样式
        self.setStyleSheet(theme["styles"]["main_window"])
        
        # 更新主题按钮文本
        if self.theme_manager.current_theme == "dark":
            self.theme_button.setText("☀️ 浅色主题")
        else:
            self.theme_button.setText("🌙 深色主题")
        
        # 更新所有状态卡片
        for card in self.findChildren(ThemedStatusCard):
            card.apply_theme()
        
        # 更新所有图表
        for chart in self.findChildren(RealTimeChart):
            chart.apply_theme()
        
        # 更新进程表格
        self.process_table.apply_theme()
        
        # 更新标签页样式
        tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {theme["colors"]["border"]};
                background-color: {theme["colors"]["background"]};
            }}
            QTabBar::tab {{
                background-color: {theme["colors"]["surface"]};
                color: {theme["colors"]["text_primary"]};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {theme["colors"]["border"]};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {theme["colors"]["primary"]};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {theme["colors"]["hover"]};
            }}
        """
        self.tab_widget.setStyleSheet(tab_style)
        
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get('theme', 'light')
                    self.theme_manager.set_theme(theme_name)
                    self.apply_theme()
        except Exception as e:
            print(f"加载配置失败: {e}")
            
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            config = {
                'theme': self.theme_manager.current_theme
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.monitor.stop_monitoring()
        self.monitor.wait(3000)
        self.save_config()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("系统监控仪表盘")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("系统工具")
    
    # 创建主窗口
    window = SystemDashboard()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()