import sys
import os
import json
import time
import datetime as dt
import multiprocessing as mp
from typing import List, Tuple

import psutil
from PySide6 import QtCore, QtGui, QtWidgets

# 配置目录改为用户级可写目录（Windows: %APPDATA%\ResourceManagers）
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
    
    # 基础工作间隔
    base_interval = 0.05  # 减少工作时间单位
    
    while not stop_event.is_set():
        duty = duty_value.value  # 0.0 ~ 1.0
        duty = max(0.0, min(1.0, duty))
        
        if duty > 0.01:  # 只有当需要占用CPU时才工作
            # 计算工作时间和休息时间
            work_time = base_interval * duty
            sleep_time = base_interval * (1.0 - duty)
            
            # 执行CPU密集型计算
            start_time = time.perf_counter()
            while (time.perf_counter() - start_time) < work_time:
                 # 执行更密集的计算密集型操作
                 _ = sum(i * i * i + math.sin(i) * math.cos(i) for i in range(10000))
                 _ = [x**2 for x in range(1000)]
            
            # 休息时间
            if sleep_time > 0:
                time.sleep(sleep_time)
        else:
            # 如果不需要占用CPU，就休息更长时间
            time.sleep(0.05)

# ------------- Scheduling helpers -------------
class TimeWindow(QtCore.QObject):
    def __init__(self, start_str: str, end_str: str):
        super().__init__()
        self.start_str = start_str
        self.end_str = end_str
        self.start = dt.datetime.strptime(start_str, '%H:%M').time()
        self.end = dt.datetime.strptime(end_str, '%H:%M').time()

    def contains_now(self) -> bool:
        now = dt.datetime.now().time()
        if self.start <= self.end:
            return self.start <= now <= self.end
        else:
            # Cross-midnight window (e.g., 22:00-02:00)
            return now >= self.start or now <= self.end

# ------------- Control Worker -------------
class ControlWorker(QtCore.QObject):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
    
    @QtCore.Slot()
    def run(self):
        # 初始化控制参数
        last_cpu_readings = []
        max_readings = 5  # 保持最近5次读数用于平滑
        error_count = 0  # 错误计数器
        max_errors = 10  # 最大错误次数
        last_health_check = time.time()
        
        try:
            # Periodically measure and adjust duty
            while self.controller.running and self.controller.duty_value and self.controller.stop_event and not self.controller.stop_event.is_set():
                try:
                    current_time = time.time()
                    
                    # 每5秒进行一次进程健康检查
                    if current_time - last_health_check > 5.0:
                        self.controller._check_and_restart_processes()
                        last_health_check = current_time
                    
                    # 获取当前CPU使用率
                    current = psutil.cpu_percent(interval=1.0)  # 增加测量间隔提高准确性
                    
                    # 平滑CPU读数
                    last_cpu_readings.append(current)
                    if len(last_cpu_readings) > max_readings:
                        last_cpu_readings.pop(0)
                    
                    # 使用平均值进行控制
                    avg_cpu = sum(last_cpu_readings) / len(last_cpu_readings)
                    
                    # 计算误差
                    error = self.controller.target_percent - avg_cpu
                    
                    # 改进的控制算法
                    current_duty = self.controller.duty_value.value
                    
                    # 根据误差大小调整控制强度
                    if abs(error) > 10:  # 大误差时快速调整
                        adjustment = self.controller.kp * 2 * (error / 100.0)
                    elif abs(error) > 5:  # 中等误差时正常调整
                        adjustment = self.controller.kp * (error / 100.0)
                    else:  # 小误差时细微调整
                        adjustment = self.controller.kp * 0.5 * (error / 100.0)
                    
                    new_duty = current_duty + adjustment
                    new_duty = max(0.0, min(1.0, new_duty))  # 限制在0-1范围内
                    
                    # 避免过度振荡
                    if abs(new_duty - current_duty) < 0.01 and abs(error) < 2:
                        new_duty = current_duty  # 保持当前值
                    
                    self.controller.duty_value.value = new_duty
                    
                    # 发送状态更新，包含活跃进程数
                    alive_count = len([p for p in self.controller.processes if p.is_alive()])
                    self.controller.state_signal.emit(True, new_duty)
                    self.controller.log_signal.emit(f"CPU: {avg_cpu:.1f}% | 目标: {self.controller.target_percent:.1f}% | 误差: {error:.1f}% | 占空比: {new_duty:.3f} | 活跃进程: {alive_count}/{len(self.controller.processes)}")
                    
                    # 重置错误计数器
                    error_count = 0
                    
                    # 控制循环间隔
                    QtCore.QThread.msleep(500)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Control loop error {error_count}: {e}")
                    if error_count >= max_errors:
                        print("Too many errors, stopping control loop")
                        break
                    # 错误处理
                    QtCore.QThread.msleep(1000)
                    
        except Exception as e:
            print(f"Fatal error in control loop: {e}")
        finally:
            # exit thread when not running
            QtCore.QThread.currentThread().quit()

# ------------- Controller (non-Qt threads/processes) -------------
class CpuController(QtCore.QObject):
    log_signal = QtCore.Signal(str)
    state_signal = QtCore.Signal(bool, float)  # running, duty

    def __init__(self):
        super().__init__()
        self.target_percent = 80.0
        self.running = False
        self.processes: List[mp.Process] = []
        self.stop_event: mp.Event | None = None
        self.duty_value: mp.Value | None = None
        self.control_thread: QtCore.QThread | None = None
        self.core_count = max(1, os.cpu_count() or 1)
        self.kp = 0.15  # 提高比例增益，加快响应速度

    def start(self):
        if self.running:
            return
        # Set running first to avoid race with control thread start
        self.running = True
        self.stop_event = mp.Event()
        self.duty_value = mp.Value('d', min(1.0, max(0.0, self.target_percent/100.0)))
        self.processes = []
        # 创建更多工作进程以达到更高CPU使用率
        worker_count = min(self.core_count, max(4, self.core_count * 3 // 4))
        for i in range(worker_count):
            try:
                p = mp.Process(target=cpu_worker_loop, args=(self.duty_value, self.stop_event, i), daemon=True)
                p.start()
                self.processes.append(p)
            except Exception as e:
                print(f"Error starting worker process {i}: {e}")
        # Control thread adjusts duty based on measured CPU
        self._start_control_loop()
        worker_count = len(self.processes)
        self.log_signal.emit(f"已启动 CPU 控制，目标 {self.target_percent:.0f}% ，工作进程数 {worker_count}")
        self.state_signal.emit(True, self.duty_value.value if self.duty_value else 0.0)

    def stop(self):
        if not self.running:
            return
        print("Stopping CPU controller...")
        self.running = False
        if self.stop_event:
            self.stop_event.set()
        # Stop control thread first
        if self.control_thread is not None:
            self.control_thread.quit()
            self.control_thread.wait(3000)  # 等待最多3秒
            self.control_thread = None
        
        # 安全地终止所有进程
        for p in self.processes:
            if p.is_alive():
                try:
                    p.terminate()
                    p.join(timeout=2)  # 等待2秒
                    if p.is_alive():
                        p.kill()  # 强制终止
                        p.join()
                except Exception as e:
                    print(f"Error stopping process: {e}")
        
        self.processes = []
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
            
            # 移除死亡进程
            for i in reversed(dead_processes):
                try:
                    self.processes[i].join(timeout=0.1)
                except:
                    pass
                del self.processes[i]
            
            # 重启进程以保持目标数量
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
        # Use a Qt thread to run the loop safely with signals
        self.control_thread = QtCore.QThread()
        # Create a worker object for the thread instead of moving self
        self.control_worker = ControlWorker(self)
        self.control_worker.moveToThread(self.control_thread)
        self.control_thread.started.connect(self.control_worker.run)
        self.control_thread.start()



# ------------- GUI -------------
class CpuManagerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU 动态占用管理器")
        self.setMinimumSize(780, 540)
        self.controller = CpuController()

        # Main Layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Top status
        status_box = QtWidgets.QGroupBox("状态")
        status_layout = QtWidgets.QGridLayout(status_box)
        self.current_label = QtWidgets.QLabel("当前 CPU：0%")
        self.target_spin = QtWidgets.QSpinBox()
        self.target_spin.setRange(1, 100)
        self.target_spin.setValue(80)
        self.target_spin.setSuffix(" %")
        self.duty_label = QtWidgets.QLabel("当前占空比：0.00")
        self.toggle_btn = QtWidgets.QPushButton("启动")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        status_layout.addWidget(QtWidgets.QLabel("目标 CPU："), 0, 0)
        status_layout.addWidget(self.target_spin, 0, 1)
        status_layout.addWidget(self.current_label, 0, 2)
        status_layout.addWidget(self.duty_label, 0, 3)
        status_layout.addWidget(self.toggle_btn, 0, 4)
        status_layout.addWidget(self.progress, 1, 0, 1, 5)

        # Schedule box
        sched_box = QtWidgets.QGroupBox("定时策略（每日时段）")
        sched_layout = QtWidgets.QVBoxLayout(sched_box)
        self.enable_sched = QtWidgets.QCheckBox("启用定时控制（仅在以下时段内运行）")
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["开始", "结束"]) 
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        form = QtWidgets.QHBoxLayout()
        self.start_time = QtWidgets.QTimeEdit(QtCore.QTime(9, 0))
        self.end_time = QtWidgets.QTimeEdit(QtCore.QTime(18, 0))
        self.add_btn = QtWidgets.QPushButton("添加时段")
        self.del_btn = QtWidgets.QPushButton("删除选中")
        form.addWidget(QtWidgets.QLabel("开始:"))
        form.addWidget(self.start_time)
        form.addWidget(QtWidgets.QLabel("结束:"))
        form.addWidget(self.end_time)
        form.addWidget(self.add_btn)
        form.addWidget(self.del_btn)
        sched_layout.addWidget(self.enable_sched)
        sched_layout.addWidget(self.table)
        sched_layout.addLayout(form)

        # Log box
        log_box = QtWidgets.QGroupBox("日志")
        log_layout = QtWidgets.QVBoxLayout(log_box)
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)

        layout.addWidget(status_box)
        layout.addWidget(sched_box)
        layout.addWidget(log_box)

        # Connections
        self.toggle_btn.toggled.connect(self.on_toggle)
        self.target_spin.valueChanged.connect(self.on_target_changed)
        self.add_btn.clicked.connect(self.on_add_period)
        self.del_btn.clicked.connect(self.on_delete_period)
        self.controller.log_signal.connect(self.append_log)
        self.controller.state_signal.connect(self.on_state)

        # Timers
        self.stats_timer = QtCore.QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)

        self.schedule_timer = QtCore.QTimer(self)
        self.schedule_timer.timeout.connect(self.apply_schedule)
        self.schedule_timer.start(10000)  # every 10s check

        self.load_config()
        self.apply_theme()

    # ---------- Theme ----------
    def apply_theme(self):
        self.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(245, 245, 245))
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(240, 240, 240))
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        self.setPalette(palette)
        self.setStyleSheet("QGroupBox{font-weight:bold;border:1px solid #ccc;border-radius:6px;margin-top:8px;} QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px;} QPushButton{padding:6px 12px;} QTableWidget{gridline-color:#ddd;}")

    # ---------- Config ----------
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.target_spin.setValue(int(cfg.get('target', 80)))
                self.enable_sched.setChecked(bool(cfg.get('schedule_enabled', False)))
                self.table.setRowCount(0)
                for start, end in cfg.get('periods', []):
                    self._add_row(start, end)
                self.append_log("配置已加载")
            except Exception as e:
                self.append_log(f"加载配置失败: {e}")

    def save_config(self):
        cfg = {
            'target': self.target_spin.value(),
            'schedule_enabled': self.enable_sched.isChecked(),
            'periods': self._collect_periods(),
        }
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.append_log("配置已保存")
        except Exception as e:
            self.append_log(f"保存配置失败: {e}")

    # ---------- UI events ----------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.save_config()
        self.controller.stop()
        return super().closeEvent(event)

    def on_toggle(self, checked: bool):
        if checked:
            self.controller.target_percent = float(self.target_spin.value())
            self.controller.start()
            self.toggle_btn.setText("停止")
            self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        else:
            self.controller.stop()
            self.toggle_btn.setText("启动")
            self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    def on_target_changed(self, val: int):
        self.controller.target_percent = float(val)
        self.append_log(f"目标 CPU 设置为 {val}%")

    def on_add_period(self):
        start = self.start_time.time().toString('HH:mm')
        end = self.end_time.time().toString('HH:mm')
        self._add_row(start, end)

    def on_delete_period(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def _add_row(self, start: str, end: str):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(start))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(end))

    def _collect_periods(self) -> List[Tuple[str, str]]:
        out = []
        for r in range(self.table.rowCount()):
            s = self.table.item(r, 0).text()
            e = self.table.item(r, 1).text()
            out.append((s, e))
        return out

    def apply_schedule(self):
        if not self.enable_sched.isChecked():
            return
        periods = [TimeWindow(s, e) for s, e in self._collect_periods()]
        active = any(p.contains_now() for p in periods)
        if active and not self.controller.running:
            self.toggle_btn.setChecked(True)
        elif (not active) and self.controller.running:
            self.toggle_btn.setChecked(False)

    def update_stats(self):
        current = psutil.cpu_percent(interval=None)
        self.current_label.setText(f"当前 CPU：{current:.0f}%")
        self.progress.setValue(int(current))

    @QtCore.Slot(bool, float)
    def on_state(self, running: bool, duty: float):
        self.duty_label.setText(f"当前占空比：{duty:.2f}")

    def append_log(self, text: str):
        ts = dt.datetime.now().strftime('%H:%M:%S')
        self.log_edit.appendPlainText(f"[{ts}] {text}")

# ------------- Entry Point -------------
def main():
    # Windows needs spawn and freeze support for PyInstaller
    try:
        mp.freeze_support()
    except Exception:
        pass
    try:
        mp.set_start_method('spawn')
    except RuntimeError:
        pass
    app = QtWidgets.QApplication(sys.argv)
    w = CpuManagerWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()