import sys
import os
import json
import time
import datetime as dt
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

CONFIG_PATH = os.path.join(_config_dir(), 'memory_manager_config.json')

# ------------- Memory Controller -------------
class MemoryController(QtCore.QObject):
    log_signal = QtCore.Signal(str)
    state_signal = QtCore.Signal(bool, int)  # running, chunks count

    def __init__(self):
        super().__init__()
        self.target_percent = 80.0
        self.running = False
        self.block_size_mb = 10  # allocation unit
        self._chunks: list[bytearray] = []
        self._thread: QtCore.QThread | None = None
        self._stop = False

    def start(self):
        if self.running:
            return
        self._stop = False
        self._thread = QtCore.QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._control_loop)
        self._thread.start()
        self.running = True
        self.log_signal.emit(f"已启动内存控制，目标 {self.target_percent:.0f}% ，块大小 {self.block_size_mb} MB")
        self.state_signal.emit(True, len(self._chunks))

    def stop(self):
        if not self.running:
            return
        self._stop = True
        # let thread exit
        if self._thread:
            self._thread.quit()
            self._thread.wait(1500)
        self._thread = None
        # free memory
        self._chunks.clear()
        self.running = False
        self.state_signal.emit(False, 0)
        self.log_signal.emit("已停止内存控制并释放占用")

    @QtCore.Slot()
    def _control_loop(self):
        # Hysteresis to avoid thrashing
        lower = 0.5
        upper = 0.5
        touched_index = 0
        while not self._stop:
            vm = psutil.virtual_memory()
            current = vm.percent
            target = self.target_percent
            # Calculate required change in percent
            if current < target - lower:
                # allocate until crossing threshold in small steps
                need_percent = (target - current)
                step_chunks = max(1, int(need_percent // 1))
                for _ in range(step_chunks):
                    try:
                        self._chunks.append(bytearray(self.block_size_mb * 1024 * 1024))
                    except MemoryError:
                        self.log_signal.emit("内存分配失败：已达到系统限制")
                        break
                self.state_signal.emit(True, len(self._chunks))
            elif current > target + upper:
                # release some chunks
                release_count = max(1, int((current - target) // 1))
                if release_count > 0 and self._chunks:
                    del self._chunks[:release_count]
                    self.state_signal.emit(True, len(self._chunks))
            else:
                # Lightly touch one chunk occasionally to keep resident
                if self._chunks:
                    touched_index = (touched_index + 1) % len(self._chunks)
                    ch = self._chunks[touched_index]
                    if ch:
                        ch[0] = (ch[0] + 1) % 256
            # Sleep to keep CPU overhead low
            QtCore.QThread.msleep(500)
        QtCore.QThread.currentThread().quit()

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
            return now >= self.start or now <= self.end

# ------------- GUI -------------
class MemoryManagerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("内存动态占用管理器")
        self.setMinimumSize(780, 540)
        self.controller = MemoryController()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Status
        status_box = QtWidgets.QGroupBox("状态")
        status_layout = QtWidgets.QGridLayout(status_box)
        self.current_label = QtWidgets.QLabel("当前内存：0%")
        self.target_spin = QtWidgets.QSpinBox()
        self.target_spin.setRange(1, 95)
        self.target_spin.setValue(80)
        self.target_spin.setSuffix(" %")
        self.block_spin = QtWidgets.QSpinBox()
        self.block_spin.setRange(1, 1024)
        self.block_spin.setValue(10)
        self.block_spin.setSuffix(" MB/块")
        self.chunks_label = QtWidgets.QLabel("已分配块：0")
        self.toggle_btn = QtWidgets.QPushButton("启动")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)

        status_layout.addWidget(QtWidgets.QLabel("目标内存："), 0, 0)
        status_layout.addWidget(self.target_spin, 0, 1)
        status_layout.addWidget(self.current_label, 0, 2)
        status_layout.addWidget(self.chunks_label, 0, 3)
        status_layout.addWidget(self.toggle_btn, 0, 4)
        status_layout.addWidget(QtWidgets.QLabel("分配粒度："), 1, 0)
        status_layout.addWidget(self.block_spin, 1, 1)
        status_layout.addWidget(self.progress, 1, 2, 1, 3)

        # Schedule
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

        # Log
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
        self.block_spin.valueChanged.connect(self.on_block_changed)
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
        self.schedule_timer.start(10000)

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
                self.block_spin.setValue(int(cfg.get('block_mb', 10)))
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
            'block_mb': self.block_spin.value(),
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
            self.controller.block_size_mb = int(self.block_spin.value())
            self.controller.start()
            self.toggle_btn.setText("停止")
            self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        else:
            self.controller.stop()
            self.toggle_btn.setText("启动")
            self.toggle_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    def on_target_changed(self, val: int):
        self.controller.target_percent = float(val)
        self.append_log(f"目标内存设置为 {val}%")

    def on_block_changed(self, val: int):
        self.controller.block_size_mb = int(val)
        self.append_log(f"分配粒度设置为 {val} MB")

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
        vm = psutil.virtual_memory()
        current = vm.percent
        self.current_label.setText(f"当前内存：{current:.0f}%")
        self.progress.setValue(int(current))

    @QtCore.Slot(bool, int)
    def on_state(self, running: bool, chunks: int):
        self.chunks_label.setText(f"已分配块：{chunks}")

    def append_log(self, text: str):
        ts = dt.datetime.now().strftime('%H:%M:%S')
        self.log_edit.appendPlainText(f"[{ts}] {text}")

# ------------- Entry Point -------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MemoryManagerWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()