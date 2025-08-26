import sys
import os
import json
import time
import datetime as dt
import multiprocessing as mp
from typing import List, Tuple
from collections import deque

import psutil
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtCore import QTimer, QDateTime

# 配置目录改为用户级可写目录
def _config_dir() -> str:
    base = None
    if os.name == 'nt':
        base = os.getenv('APPDATA')
    if not base:
        base = os.path.expanduser('~')
    path = os.path.join(base, 'ResourceManagers')
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path

CONFIG_PATH = os.path.join(_config_dir(), 'cpu_manager_config.json')

# ------------- CPU Load Worker (top-level for Windows spawn) -------------
def cpu_worker_loop(duty_value: mp.Value, stop_event: mp.Event, worker_id: int = 0):
    """单个CPU工作进程，通过调节工作强度来控制CPU占用"""
    try:
        import time
        import math
    except Exception:
        return
    
    base_interval = 0.05
    
    while not stop_event.is_set():
        duty = duty_value.value
        duty = max(0.0, min(1.0, duty))
        
        if duty > 0.01:
            work_time = base_interval * duty
            sleep_time = base_interval * (1.0 - duty)
            
            start_time = time.perf_counter()
            while (time.perf_counter() - start_time) < work_time:
                # 增强的计算密集型操作
                for i in range(10000):
                    math.sin(i) * math.cos(i)
                    math.sqrt(i * 2 + 1)
                # 列表推导式增加计算负载
                [x**2 for x in range(1000)]
                
                if stop_event.is_set():
                    break
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        else:
            time.sleep(base_interval)

# ------------- 实时图表组件 -------------
class RealTimeChart(QChartView):
    def __init__(self, title: str, max_points: int = 100):
        super().__init__()
        
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        
        # 创建图表
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 创建数据系列
        self.series = QLineSeries()
        self.series.setName("CPU使用率")
        self.chart.addSeries(self.series)
        
        # 设置坐标轴
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("hh:mm:ss")
        self.axis_x.setTitleText("时间")
        
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText("CPU使用率 (%)")
        
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)
        
        # 设置图表视图
        self.setChart(self.chart)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 设置样式
        self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#f8f9fa")))
        self.series.setPen(QtGui.QPen(QtGui.QColor("#007bff"), 2))
    
    def add_data_point(self, value: float):
        """添加新的数据点"""
        current_time = QDateTime.currentDateTime()
        self.data_points.append((current_time, value))
        
        # 更新数据系列
        self.series.clear()
        for timestamp, val in self.data_points:
            self.series.append(timestamp.toMSecsSinceEpoch(), val)
        
        # 更新X轴范围
        if len(self.data_points) > 1:
            start_time = self.data_points[0][0]
            end_time = self.data_points[-1][0]
            self.axis_x.setRange(start_time, end_time)

# ------------- 状态卡片组件 -------------
class StatusCard(QtWidgets.QFrame):
    def __init__(self, title: str, value: str = "0", unit: str = "", color: str = "#007bff"):
        super().__init__()
        self.setFrameStyle(QtWidgets.QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("color: #6c757d; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 数值
        value_layout = QtWidgets.QHBoxLayout()
        self.value_label = QtWidgets.QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        value_layout.addWidget(self.value_label)
        
        if unit:
            unit_label = QtWidgets.QLabel(unit)
            unit_label.setStyleSheet("color: #6c757d; font-size: 14px;")
            value_layout.addWidget(unit_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        layout.addStretch()
    
    def update_value(self, value: str):
        """更新显示值"""
        self.value_label.setText(value)

# ------------- 控制器类 (保持原有逻辑) -------------
class ControlWorker(QtCore.QObject):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @QtCore.Slot()
    def run(self):
        error_count = 0
        max_errors = 10
        last_health_check = time.time()
        
        try:
            while self.controller.running and self.controller.duty_value and self.controller.stop_event and not self.controller.stop_event.is_set():
                try:
                    current_time = time.time()
                    
                    if current_time - last_health_check > 5.0:
                        self.controller._check_and_restart_processes()
                        last_health_check = current_time
                    
                    current_cpu = psutil.cpu_percent(interval=0.5)
                    error = self.controller.target_cpu - current_cpu
                    
                    self.controller.integral += error * 0.5
                    derivative = (error - self.controller.previous_error) / 0.5
                    
                    self.controller.integral = max(-50, min(50, self.controller.integral))
                    
                    output = (self.controller.kp * error + 
                             self.controller.ki * self.controller.integral + 
                             self.controller.kd * derivative)
                    
                    new_duty = max(0.0, min(1.0, self.controller.duty_value.value + output * 0.01))
                    self.controller.duty_value.value = new_duty
                    
                    self.controller.previous_error = error
                    
                    alive_count = len([p for p in self.controller.processes if p.is_alive()])
                    self.controller.state_signal.emit(True, current_cpu)
                    self.controller.log_signal.emit(f"CPU: {current_cpu:.1f}% | 目标: {self.controller.target_cpu:.1f}% | 误差: {error:.1f}% | 占空比: {new_duty:.3f} | 活跃进程: {alive_count}/{len(self.controller.processes)}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Control loop error ({error_count}/{max_errors}): {e}")
                    if error_count >= max_errors:
                        print("Too many errors, stopping controller")
                        self.controller.running = False
                        break
                    time.sleep(1)
        except Exception as e:
            print(f"Control thread fatal error: {e}")
            self.controller.running = False

class CpuController(QtCore.QObject):
    log_signal = QtCore.Signal(str)
    state_signal = QtCore.Signal(bool, float)  # running, cpu_percent

    def __init__(self):
        super().__init__()
        self.running = False
        self.target_cpu = 50.0
        self.processes = []
        self.duty_value = None
        self.stop_event = None
        self.control_thread = None
        self.core_count = mp.cpu_count()
        
        # PID控制器参数
        self.kp = 0.1
        self.ki = 0.01
        self.kd = 0.05
        self.integral = 0.0
        self.previous_error = 0.0

    def start(self, target_percent: float):
        if self.running:
            return
        
        self.target_cpu = target_percent
        self.running = True
        self.integral = 0.0
        self.previous_error = 0.0
        
        # 创建共享变量
        self.duty_value = mp.Value('d', 0.1)
        self.stop_event = mp.Event()
        
        # 创建工作进程
        self.processes = []
        worker_count = min(self.core_count, max(4, self.core_count * 3 // 4))
        for i in range(worker_count):
            try:
                p = mp.Process(target=cpu_worker_loop, args=(self.duty_value, self.stop_event, i), daemon=True)
                p.start()
                self.processes.append(p)
            except Exception as e:
                print(f"Error starting worker process {i}: {e}")
        
        self._start_control_loop()
        self.log_signal.emit(f"已启动 CPU 控制，目标: {target_percent:.1f}%，工作进程: {len(self.processes)}")

    def stop(self):
        if not self.running:
            return
        print("Stopping CPU controller...")
        self.running = False
        if self.stop_event:
            self.stop_event.set()
        if self.control_thread:
            self.control_thread.quit()
            self.control_thread.wait(timeout=3000)
        
        for p in self.processes:
            if p.is_alive():
                try:
                    p.terminate()
                    p.join(timeout=2)
                    if p.is_alive():
                        p.kill()
                        p.join()
                except Exception as e:
                    print(f"Error stopping process: {e}")
        
        self.processes.clear()
        print("CPU controller stopped")
        self.state_signal.emit(False, 0.0)
        self.log_signal.emit("已停止 CPU 控制")
    
    def _check_and_restart_processes(self):
        """检查进程健康状态并重启死亡的进程"""
        dead_processes = []
        for i, p in enumerate(self.processes):
            if not p.is_alive():
                dead_processes.append(i)
        
        if dead_processes:
            print(f"Found {len(dead_processes)} dead processes, restarting...")
            
            for i in reversed(dead_processes):
                try:
                    self.processes[i].join(timeout=0.1)
                except:
                    pass
                del self.processes[i]
            
            target_count = min(self.core_count, max(4, self.core_count * 3 // 4))
            current_count = len(self.processes)
            
            for i in range(current_count, target_count):
                try:
                    p = mp.Process(target=cpu_worker_loop, args=(self.duty_value, self.stop_event, i), daemon=True)
                    p.start()
                    self.processes.append(p)
                    print(f"Restarted worker process {i}")
                except Exception as e:
                    print(f"Error restarting worker process {i}: {e}")

    def _start_control_loop(self):
        self.control_thread = QtCore.QThread()
        self.worker = ControlWorker(self)
        self.worker.moveToThread(self.control_thread)
        self.control_thread.started.connect(self.worker.run)
        self.control_thread.start()

# ------------- 增强的主窗口 -------------
class EnhancedCpuManagerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = CpuController()
        self.setup_ui()
        self.setup_connections()
        self.load_config()
        
        # 定时器用于更新统计信息
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)  # 每秒更新

    def setup_ui(self):
        self.setWindowTitle("CPU资源管理器 - 增强版")
        self.setMinimumSize(1000, 700)
        
        # 中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 状态卡片区域
        cards_layout = QtWidgets.QHBoxLayout()
        self.cpu_card = StatusCard("当前CPU使用率", "0", "%", "#28a745")
        self.target_card = StatusCard("目标CPU使用率", "50", "%", "#007bff")
        self.processes_card = StatusCard("活跃进程数", "0", "个", "#ffc107")
        self.duty_card = StatusCard("占空比", "0.000", "", "#6f42c1")
        
        cards_layout.addWidget(self.cpu_card)
        cards_layout.addWidget(self.target_card)
        cards_layout.addWidget(self.processes_card)
        cards_layout.addWidget(self.duty_card)
        main_layout.addLayout(cards_layout)
        
        # 图表区域
        self.chart = RealTimeChart("CPU使用率实时监控")
        main_layout.addWidget(self.chart)
        
        # 控制面板
        control_group = QtWidgets.QGroupBox("控制面板")
        control_layout = QtWidgets.QGridLayout(control_group)
        
        # 开关按钮
        self.toggle_btn = QtWidgets.QPushButton("启动")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:checked:hover {
                background-color: #c82333;
            }
        """)
        control_layout.addWidget(self.toggle_btn, 0, 0, 1, 2)
        
        # 目标CPU使用率
        control_layout.addWidget(QtWidgets.QLabel("目标CPU使用率:"), 1, 0)
        self.target_spin = QtWidgets.QSpinBox()
        self.target_spin.setRange(1, 100)
        self.target_spin.setValue(50)
        self.target_spin.setSuffix("%")
        control_layout.addWidget(self.target_spin, 1, 1)
        
        main_layout.addWidget(control_group)
        
        # 日志区域
        log_group = QtWidgets.QGroupBox("运行日志")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # 应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def setup_connections(self):
        self.toggle_btn.clicked.connect(self.on_toggle)
        self.target_spin.valueChanged.connect(self.on_target_changed)
        self.controller.log_signal.connect(self.append_log)
        self.controller.state_signal.connect(self.on_state)

    def on_toggle(self, checked: bool):
        if checked:
            target = self.target_spin.value()
            self.controller.start(target)
            self.toggle_btn.setText("停止")
        else:
            self.controller.stop()
            self.toggle_btn.setText("启动")

    def on_target_changed(self, val: int):
        self.target_card.update_value(str(val))
        if self.controller.running:
            self.controller.target_cpu = val

    def update_stats(self):
        """更新统计信息"""
        cpu_percent = psutil.cpu_percent()
        self.cpu_card.update_value(f"{cpu_percent:.1f}")
        
        # 添加数据点到图表
        self.chart.add_data_point(cpu_percent)
        
        if self.controller.running:
            alive_count = len([p for p in self.controller.processes if p.is_alive()])
            self.processes_card.update_value(str(alive_count))
            
            if self.controller.duty_value:
                self.duty_card.update_value(f"{self.controller.duty_value.value:.3f}")

    @QtCore.Slot(bool, float)
    def on_state(self, running: bool, cpu_percent: float):
        if not running:
            self.toggle_btn.setChecked(False)
            self.toggle_btn.setText("启动")
            self.processes_card.update_value("0")
            self.duty_card.update_value("0.000")

    def append_log(self, text: str):
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {text}")
        
        # 限制日志行数
        if self.log_text.document().blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QtGui.QTextCursor.Start)
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.target_spin.setValue(config.get('target_percent', 50))
        except Exception as e:
            print(f"Failed to load config: {e}")

    def save_config(self):
        config = {
            'target_percent': self.target_spin.value(),
        }
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.controller.stop()
        self.save_config()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("CPU资源管理器增强版")
    app.setOrganizationName("ResourceManagers")
    
    window = EnhancedCpuManagerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()