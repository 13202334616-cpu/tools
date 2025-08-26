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
def cpu_worker_loop(duty_value: mp.Value, stop_event: mp.Event, interval: float = 0.5):
    try:
        import time
    except Exception:
        return
    # Busy-sleep duty cycle to approximate target utilization per core
    while not stop_event.is_set():
        duty = duty_value.value  # 0.0 ~ 1.0
        duty = 0.0 if duty < 0.0 else (1.0 if duty > 1.0 else duty)
        busy_time = interval * duty
        start = time.perf_counter()
        # Busy phase
        while (time.perf_counter() - start) < busy_time:
            pass
        # Sleep the rest
        remaining = interval - busy_time
        if remaining > 0:
            time.sleep(remaining)

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
        self.kp = 0.02  # proportional gain

    def start(self):
        if self.running:
            return
        # Set running first to avoid race with control thread start
        self.running = True
        self.stop_event = mp.Event()
        self.duty_value = mp.Value('d', min(1.0, max(0.0, self.target_percent/100.0)))
        self.processes = []
        for _ in range(self.core_count):
            p = mp.Process(target=cpu_worker_loop, args=(self.duty_value, self.stop_event, 0.5), daemon=True)
            p.start()
            self.processes.append(p)
        # Control thread adjusts duty based on measured CPU
        self._start_control_loop()
        self.log_signal.emit(f"已启动 CPU 控制，目标 {self.target_percent:.0f}% ，核心数 {self.core_count}")
        self.state_signal.emit(True, self.duty_value.value if self.duty_value else 0.0)

    def stop(self):
        if not self.running:
            return
        if self.stop_event:
            self.stop_event.set()
        for p in self.processes:
            if p.is_alive():
                p.join(timeout=1.0)
                if p.is_alive():
                    p.terminate()
        self.processes = []
        # stop control thread
        self.running = False
        if self.control_thread is not None:
            self.control_thread.quit()
            self.control_thread.wait(1500)
            self.control_thread = None
        self.state_signal.emit(False, 0.0)
        self.log_signal.emit("已停止 CPU 控制")

    def _start_control_loop(self):
        # Use a Qt thread to run the loop safely with signals
        self.control_thread = QtCore.QThread()
        self.moveToThread(self.control_thread)
        self.control_thread.started.connect(self._control_loop)
        self.control_thread.start()

    @QtCore.Slot()
    def _control_loop(self):
        # Periodically measure and adjust duty
        while self.running and self.duty_value and self.stop_event and not self.stop_event.is_set():
            # psutil with small interval smooths readings
            current = psutil.cpu_percent(interval=0.8)
            error = (self.target_percent - current) / 100.0
            # Proportional control
            new_duty = self.duty_value.value + self.kp * error
            new_duty = 0.0 if new_duty < 0.0 else (1.0 if new_duty > 1.0 else new_duty)
            self.duty_value.value = new_duty
            self.state_signal.emit(True, new_duty)
            # Small sleep to yield UI thread
            QtCore.QThread.msleep(200)
        # exit thread when not running
        QtCore.QThread.currentThread().quit()

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
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(40, 44, 52))
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(33, 37, 43))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(40, 44, 52))
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(52, 58, 64))
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(100, 149, 237))
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        self.setPalette(palette)
        self.setStyleSheet("QGroupBox{font-weight:bold;border:1px solid #555;border-radius:6px;margin-top:8px;} QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px;} QPushButton{padding:6px 12px;} QTableWidget{gridline-color:#666;}")

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