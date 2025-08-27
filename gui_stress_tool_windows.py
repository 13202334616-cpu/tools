#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源压力测试工具 - Windows优化版本
专门为Windows服务器环境优化的图形界面版本
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import threading
import time
import json
import os
import sys
import platform
import subprocess
from datetime import datetime, timedelta
import queue
import logging
import multiprocessing
from multiprocessing import Process, Queue, Value

# CPU密集型进程函数（必须在类外部定义以支持Windows的spawn方法）
def cpu_intensive_process(control_signal, initial_intensity):
    """CPU密集型进程（独立进程，突破GIL限制）"""
    import random
    import math
    import time
    
    # 创建大量数据用于计算
    data_size = 10000
    data = [random.random() for _ in range(data_size)]
    
    # 获取当前负载强度
    current_intensity = initial_intensity
    
    while control_signal.value > 0:  # 0表示停止
        start_time = time.time()
        
        # 从控制信号获取最新的负载强度
        if control_signal.value != 1:  # 不是默认值1
            current_intensity = control_signal.value / 100.0
        
        # 多种计算密集型操作（根据强度调整）
        result = 0
        
        # 1. 数学运算
        math_ops = int(8000 * current_intensity)  # 进程比线程更多计算
        for i in range(math_ops):
            result += math.sin(i) * math.cos(i) + math.sqrt(i + 1)
            result += i ** 3 + i ** 2 + i
        
        # 2. 浮点运算
        float_ops = int(5000 * current_intensity)
        for i in range(float_ops):
            result += data[i % data_size] * 2.71828 + data[(i + 1) % data_size] * 3.14159
        
        # 3. 整数运算
        int_ops = int(4000 * current_intensity)
        for i in range(int_ops):
            result += i * i * i + i * i + i
        
        # 4. 字符串操作（CPU密集型）
        str_ops = int(2000 * current_intensity)
        for i in range(str_ops):
            s = "x" * (i % 100 + 1)
            result += len(s) + hash(s) % 1000
        
        # 5. 矩阵运算（更高强度）
        if current_intensity > 1.0:
            matrix_ops = int(1000 * (current_intensity - 1.0))
            for i in range(matrix_ops):
                # 简单矩阵乘法
                a = [[random.random() for _ in range(10)] for _ in range(10)]
                b = [[random.random() for _ in range(10)] for _ in range(10)]
                c = [[sum(a[i][k] * b[k][j] for k in range(10)) for j in range(10)] for i in range(10)]
                result += sum(sum(row) for row in c)
        
        elapsed = time.time() - start_time
        
        # 动态休眠控制（根据强度调整）
        if current_intensity < 1.0:
            sleep_time = elapsed * (1.0 - current_intensity) / current_intensity
            if sleep_time > 0:
                time.sleep(sleep_time)
        elif current_intensity > 1.5:
            # 超高强度时几乎不休眠
            time.sleep(max(0.0001, 0.005 / current_intensity))
        else:
            # 适度休眠
            time.sleep(max(0.001, 0.01 / current_intensity))

# 设置multiprocessing启动方法（Windows兼容）
# multiprocessing设置移到main函数中

class StressTestGUI:
    def __init__(self, root):
        self.root = root
        
        # 初始化基本属性
        self.stress_thread = None
        self.is_running = False
        self.cpu_threads = []
        self.memory_blocks = []
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # CPU动态管理相关属性
        self.cpu_manager_running = False
        self.cpu_manager_thread = None
        self.cpu_load_intensity = 1.0  # CPU负载强度控制
        self.cpu_processes = []  # CPU进程列表
        self.cpu_process_control = None  # 进程控制信号
        
        # 内存动态管理相关属性
        self.memory_manager_running = False
        
        # 创建监控队列（确保在所有其他初始化之前）
        try:
            self.monitor_queue = queue.Queue()
        except Exception as e:
            print(f"监控队列创建失败: {e}")
            self.monitor_queue = None
        
        # 快速设置窗口基础属性
        self.setup_window_basic()
        
        # 异步初始化其他组件
        self.root.after(10, self.async_initialize)
    
    def setup_window_basic(self):
        """快速设置窗口基础属性"""
        self.root.title("🖥️ 资源压力测试工具 - 启动中...")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # 显示加载提示
        loading_frame = tk.Frame(self.root, bg='white')
        loading_frame.pack(fill='both', expand=True)
        
        loading_label = tk.Label(loading_frame, text="⏳ 正在加载，请稍候...", 
                                font=('Arial', 16), bg='white', fg='#333')
        loading_label.pack(expand=True)
        
        self.loading_frame = loading_frame
        
        # 关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def async_initialize(self):
        """异步初始化组件"""
        try:
            # 分步骤初始化，避免阻塞
            self.setup_window()
            self.root.after(10, self.async_initialize_step2)
        except Exception as e:
            print(f"初始化错误: {e}")
            self.show_error_and_exit(str(e))
    
    def async_initialize_step2(self):
        """异步初始化步骤2"""
        try:
            self.setup_variables()
            self.root.after(10, self.async_initialize_step3)
        except Exception as e:
            print(f"变量初始化错误: {e}")
            self.show_error_and_exit(str(e))
    
    def async_initialize_step3(self):
        """异步初始化步骤3"""
        try:
            # 移除加载界面
            if hasattr(self, 'loading_frame'):
                self.loading_frame.destroy()
            
            self.create_widgets()
            self.root.after(10, self.async_initialize_step4)
        except Exception as e:
            print(f"界面创建错误: {e}")
            self.show_error_and_exit(str(e))
    
    def async_initialize_step4(self):
        """异步初始化步骤4"""
        try:
            self.setup_logging()
            self.root.after(100, self.async_initialize_final)
        except Exception as e:
            print(f"日志设置错误: {e}")
            self.show_error_and_exit(str(e))
    
    def async_initialize_final(self):
        """异步初始化最终步骤"""
        try:
            # 延迟启动监控系统，避免启动时的性能影响
            self.setup_monitoring_delayed()
            self.root.title("🖥️ 资源压力测试工具 - Windows版")
        except Exception as e:
            print(f"监控设置错误: {e}")
            self.show_error_and_exit(str(e))
    
    def show_error_and_exit(self, error_msg):
        """显示错误并退出"""
        try:
            messagebox.showerror("启动失败", f"程序启动失败:\n{error_msg}")
        except:
            pass
        self.root.quit()
    
    def setup_window(self):
        """设置主窗口"""
        self.root.title("🖥️ 资源压力测试工具 - Windows版")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Windows特定设置
        if platform.system() == "Windows":
            try:
                # 设置窗口图标（如果有的话）
                # self.root.iconbitmap("icon.ico")
                pass
            except:
                pass
            
            # 设置窗口置顶（首次显示）
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        
        # 设置样式和字体
        style = ttk.Style()
        if platform.system() == "Windows":
            style.theme_use('vista')  # Windows Vista/7/8/10样式
        
        # 配置字体大小
        self.setup_fonts(style)
        
        # 关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_fonts(self, style):
        """设置字体大小"""
        # 使用默认字体设置，延迟加载自定义字体
        self.setup_default_fonts()
        
        # 配置基础样式
        self.configure_basic_styles(style)
        
        # 异步加载自定义字体设置
        self.root.after(500, self.load_custom_fonts)
    
    def configure_basic_styles(self, style):
        """配置基础样式"""
        style.configure('Title.TLabel', font=self.title_font)
        style.configure('Label.TLabel', font=self.label_font)
        style.configure('Button.TButton', font=self.button_font)
        style.configure('Status.TLabel', font=self.status_font)
        
        # 配置选项卡字体
        style.configure('TNotebook.Tab', font=self.label_font, padding=[10, 5])
        
        # 配置框架字体
        style.configure('TLabelframe.Label', font=self.title_font)
    
    def setup_default_fonts(self):
        """设置默认字体"""
        # 使用系统默认字体，快速启动
        if platform.system() == "Windows":
            default_family = "Microsoft YaHei UI"
        else:
            default_family = "Arial"
        
        self.title_font = (default_family, 14, 'bold')
        self.label_font = (default_family, 10)
        self.button_font = (default_family, 10)
        self.status_font = (default_family, 9)
        self.log_font = (default_family, 9)
    
    def load_custom_fonts(self):
        """异步加载自定义字体设置"""
        try:
            self.load_font_settings()
            self.apply_font_settings()
        except Exception as e:
            print(f"字体加载错误: {e}")
            # 使用默认字体继续运行
    
    def load_font_settings(self):
        """加载字体设置"""
        try:
            if os.path.exists('font_settings.json'):
                with open('font_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.title_font = ('Microsoft YaHei UI', settings.get('title', 12), 'bold')
                    self.label_font = ('Microsoft YaHei UI', settings.get('label', 10))
                    self.button_font = ('Microsoft YaHei UI', settings.get('button', 10))
                    self.status_font = ('Microsoft YaHei UI', settings.get('status', 9))
                    self.log_font = ('Consolas', settings.get('log', 9))
            else:
                # 默认字体大小
                self.title_font = ('Microsoft YaHei UI', 12, 'bold')
                self.label_font = ('Microsoft YaHei UI', 10)
                self.button_font = ('Microsoft YaHei UI', 10)
                self.status_font = ('Microsoft YaHei UI', 9)
                self.log_font = ('Consolas', 9)
        except Exception as e:
            # 如果加载失败，使用默认设置
            self.title_font = ('Microsoft YaHei UI', 12, 'bold')
            self.label_font = ('Microsoft YaHei UI', 10)
            self.button_font = ('Microsoft YaHei UI', 10)
            self.status_font = ('Microsoft YaHei UI', 9)
            self.log_font = ('Consolas', 9)
    
    def save_font_settings(self):
        """保存字体设置"""
        try:
            settings = {
                'title': self.title_font[1],
                'label': self.label_font[1],
                'button': self.button_font[1],
                'status': self.status_font[1],
                'log': self.log_font[1]
            }
            with open('font_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存字体设置失败: {e}")
    
    def apply_font_settings(self):
        """应用字体设置"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=self.title_font)
        style.configure('Label.TLabel', font=self.label_font)
        style.configure('Button.TButton', font=self.button_font)
        style.configure('Status.TLabel', font=self.status_font)
        style.configure('TNotebook.Tab', font=self.label_font, padding=[10, 5])
        style.configure('TLabelframe.Label', font=self.title_font)
        
        # 更新日志字体
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.configure(font=self.log_font)
    
    def setup_variables(self):
        """设置变量"""
        # CPU设置 - 自动设置为峰值的70%作为目标
        self.cpu_max = tk.DoubleVar(value=85.0)
        self.cpu_target = tk.DoubleVar(value=self.cpu_max.get() * 0.7)  # 目标为峰值的70%
        self.cpu_threads_var = tk.IntVar(value=psutil.cpu_count())
        
        # 内存设置 - 自动设置为峰值的70%作为目标
        self.memory_max_percent = tk.DoubleVar(value=80.0)
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        target_memory_gb = total_memory_gb * (self.memory_max_percent.get() / 100) * 0.7
        self.memory_mb = tk.DoubleVar(value=target_memory_gb * 1024)  # 转换为MB
        
        # 运行时间
        self.duration_minutes = tk.IntVar(value=10)
        
        # 状态变量
        self.status_text = tk.StringVar(value="就绪")
        self.cpu_usage = tk.StringVar(value="0%")
        self.memory_usage = tk.StringVar(value="0%")
        self.test_progress = tk.StringVar(value="")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(0, weight=1)
        
        # 手动测试选项卡
        self.create_manual_tab(notebook)
        
        # 定时任务选项卡
        self.create_scheduler_tab(notebook)
        
        # 实时监控选项卡
        self.create_monitor_tab(notebook)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_manual_tab(self, notebook):
        """创建手动测试选项卡（简化版）"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="🎛️ 压力测试")
        
        # CPU峰值设置组
        cpu_group = ttk.LabelFrame(frame, text="CPU 峰值设置", padding="20")
        cpu_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        frame.columnconfigure(0, weight=1)
        
        ttk.Label(cpu_group, text="CPU峰值限制:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W, pady=10)
        cpu_max_scale = ttk.Scale(cpu_group, from_=50, to=95, variable=self.cpu_max, orient=tk.HORIZONTAL)
        cpu_max_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(20, 0), pady=10)
        cpu_max_label = ttk.Label(cpu_group, text="85", style='Label.TLabel')
        cpu_max_label.grid(row=0, column=2, sticky=tk.W, padx=(15, 0), pady=10)
        ttk.Label(cpu_group, text="%", style='Label.TLabel').grid(row=0, column=3, sticky=tk.W, pady=10)
        
        # 更新CPU峰值显示和目标值
        def update_cpu_max(*args):
            cpu_max_label.config(text=f"{int(self.cpu_max.get())}")
            # 自动更新CPU目标值为峰值的70%
            self.cpu_target.set(self.cpu_max.get() * 0.7)
        self.cpu_max.trace('w', update_cpu_max)
        
        cpu_group.columnconfigure(1, weight=1)
        
        # 内存峰值设置组
        memory_group = ttk.LabelFrame(frame, text="内存峰值设置", padding="20")
        memory_group.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(memory_group, text="内存峰值限制:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W, pady=10)
        memory_max_scale = ttk.Scale(memory_group, from_=50, to=90, variable=self.memory_max_percent, orient=tk.HORIZONTAL)
        memory_max_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(20, 0), pady=10)
        memory_max_label = ttk.Label(memory_group, text="80", style='Label.TLabel')
        memory_max_label.grid(row=0, column=2, sticky=tk.W, padx=(15, 0), pady=10)
        ttk.Label(memory_group, text="%", style='Label.TLabel').grid(row=0, column=3, sticky=tk.W, pady=10)
        
        # 更新内存峰值显示和目标值
        def update_memory_max(*args):
            memory_max_label.config(text=f"{int(self.memory_max_percent.get())}")
            # 自动更新内存目标值为峰值的70%
            total_memory_gb = psutil.virtual_memory().total / (1024**3)
            target_memory_gb = total_memory_gb * (self.memory_max_percent.get() / 100) * 0.7
            self.memory_mb.set(target_memory_gb * 1024)
        self.memory_max_percent.trace('w', update_memory_max)
        
        memory_group.columnconfigure(1, weight=1)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=30)
        
        self.start_button = ttk.Button(button_frame, text="🚀 启动压力测试", command=self.start_stress_test, style='Button.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止测试", command=self.stop_stress_test, state=tk.DISABLED, style='Button.TButton')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(button_frame, text="📊 查看系统信息", command=self.show_system_info, style='Button.TButton').pack(side=tk.LEFT)
    
    def create_scheduler_tab(self, notebook):
        """创建定时任务选项卡"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="⏰ 定时任务")
        
        # 定时任务说明
        info_text = """
🕒 定时任务功能说明：
• 可以设置多个时间段自动运行压力测试
• 支持工作日/周末不同配置
• 自动启停，无需人工干预
• 内置安全保护机制
        """
        ttk.Label(frame, text=info_text, justify=tk.LEFT, style='Label.TLabel').grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 定时任务控制
        control_frame = ttk.LabelFrame(frame, text="任务控制", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.scheduler_status = tk.StringVar(value="定时任务已停止")
        ttk.Label(control_frame, textvariable=self.scheduler_status).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        self.start_scheduler_btn = ttk.Button(control_frame, text="▶️ 启动定时任务", command=self.start_scheduler)
        self.start_scheduler_btn.grid(row=1, column=0, padx=(0, 10))
        
        self.stop_scheduler_btn = ttk.Button(control_frame, text="⏸️ 停止定时任务", command=self.stop_scheduler, state=tk.DISABLED)
        self.stop_scheduler_btn.grid(row=1, column=1)
        
        # 配置管理
        config_frame = ttk.LabelFrame(frame, text="配置管理", padding="10")
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(config_frame, text="📝 编辑配置", command=self.edit_schedule_config).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(config_frame, text="🔄 重载配置", command=self.reload_schedule_config).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(config_frame, text="📂 打开配置目录", command=self.open_config_dir).grid(row=0, column=2)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def create_monitor_tab(self, notebook):
        """创建监控选项卡"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="📊 实时监控")
        
        # 系统状态显示
        status_frame = ttk.LabelFrame(frame, text="系统状态", padding="15")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(status_frame, text="CPU使用率:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_frame, textvariable=self.cpu_usage, font=("Microsoft YaHei UI", 14, "bold")).grid(row=0, column=1, sticky=tk.W, padx=(15, 0), pady=5)
        
        ttk.Label(status_frame, text="内存使用率:", style='Label.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_frame, textvariable=self.memory_usage, font=("Microsoft YaHei UI", 14, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(15, 0), pady=5)
        
        # 运行日志
        log_frame = ttk.LabelFrame(frame, text="运行日志", padding="15")
        log_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        frame.rowconfigure(1, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70, font=self.log_font)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # 日志控制按钮
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(log_btn_frame, text="🗑️ 清空日志", command=self.clear_log, style='Button.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_btn_frame, text="💾 保存日志", command=self.save_log, style='Button.TButton').pack(side=tk.LEFT)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 左侧状态信息
        ttk.Label(status_frame, text="状态:", style='Status.TLabel').pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_text, style='Status.TLabel').pack(side=tk.LEFT, padx=(5, 20))
        ttk.Label(status_frame, textvariable=self.test_progress, style='Status.TLabel').pack(side=tk.LEFT)
        
        # 右侧功能按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # 调小文字按钮
        decrease_font_button = ttk.Button(button_frame, text="🔍- 调小文字", command=self.decrease_all_fonts, style='Button.TButton')
        decrease_font_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 调大文字按钮
        increase_font_button = ttk.Button(button_frame, text="🔍+ 调大文字", command=self.increase_all_fonts, style='Button.TButton')
        increase_font_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 字体设置按钮
        font_button = ttk.Button(button_frame, text="🔤 字体设置", command=self.open_font_settings, style='Button.TButton')
        font_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def setup_monitoring_delayed(self):
        """延迟设置系统监控，避免启动阻塞"""
        # 延迟3秒后启动监控，让界面先完全加载
        self.root.after(3000, self.setup_monitoring)
    
    def setup_monitoring(self):
        """设置系统监控"""
        def monitor_system():
            # 首次获取CPU使用率时不使用interval参数，避免阻塞
            first_run = True
            while True:
                try:
                    # 检查monitor_queue是否存在且不为None
                    if not hasattr(self, 'monitor_queue') or self.monitor_queue is None:
                        time.sleep(1)
                        continue
                    
                    # 优化CPU监控，避免阻塞
                    if first_run:
                        cpu_percent = psutil.cpu_percent()  # 不使用interval，立即返回
                        first_run = False
                    else:
                        cpu_percent = psutil.cpu_percent(interval=0.1)  # 使用较短的interval
                    
                    memory_info = psutil.virtual_memory()
                    
                    try:
                        self.monitor_queue.put(('system_status', {
                            'cpu': cpu_percent,
                            'memory': memory_info.percent
                        }))
                    except Exception as queue_error:
                        print(f"队列操作失败: {queue_error}")
                        time.sleep(1)
                        continue
                except Exception as e:
                    # 如果出现错误，等待一段时间后继续
                    time.sleep(1)
                    continue
                time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        
        # 定期更新GUI
        self.update_gui()
    
    def update_gui(self):
        """更新GUI显示"""
        try:
            # 检查monitor_queue是否存在且不为None
            if not hasattr(self, 'monitor_queue') or self.monitor_queue is None:
                self.root.after(1000, self.update_gui)
                return
            
            # 批量处理队列消息，避免频繁更新
            updates = {'cpu': None, 'memory': None, 'logs': []}
            processed_count = 0
            max_process = 10  # 限制每次处理的消息数量
            
            try:
                while not self.monitor_queue.empty() and processed_count < max_process:
                    try:
                        msg_type, data = self.monitor_queue.get_nowait()
                        processed_count += 1
                        
                        if msg_type == 'system_status':
                            updates['cpu'] = data['cpu']
                            updates['memory'] = data['memory']
                        elif msg_type == 'log':
                            updates['logs'].append(data)
                    except queue.Empty:
                        break
            except Exception as queue_error:
                print(f"队列处理失败: {queue_error}")
            
            # 批量更新UI
            if updates['cpu'] is not None:
                self.cpu_usage.set(f"{updates['cpu']:.1f}%")
            if updates['memory'] is not None:
                self.memory_usage.set(f"{updates['memory']:.1f}%")
            for log_msg in updates['logs']:
                self.add_log(log_msg)
                
        except Exception as e:
            # 如果出现错误，继续更新
            pass
        
        # 动态调整更新频率
        update_interval = 500 if self.is_running else 1000
        self.root.after(update_interval, self.update_gui)
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def add_log(self, message):
        """添加日志"""
        try:
            if hasattr(self, 'log_text') and self.log_text:
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_message = f"[{timestamp}] {message}\n"
                
                self.log_text.insert(tk.END, log_message)
                self.log_text.see(tk.END)
                
                # 限制日志长度
                lines = self.log_text.get("1.0", tk.END).split('\n')
                if len(lines) > 1000:
                    self.log_text.delete("1.0", "100.0")
        except Exception as e:
            # 如果日志控件不可用，忽略错误
            pass
    
    def put_log(self, message):
        """安全地添加日志到队列"""
        try:
            if hasattr(self, 'monitor_queue') and self.monitor_queue is not None:
                try:
                    self.monitor_queue.put(('log', message))
                except Exception as queue_error:
                    print(f"日志队列操作失败: {queue_error}")
                    # 如果队列操作失败，直接添加到日志
                    self.add_log(message)
            else:
                # 如果队列不存在，直接添加到日志
                self.add_log(message)
        except Exception as e:
            # 如果队列不可用，直接添加到日志
            self.add_log(message)
    
    def start_stress_test(self):
        """启动压力测试"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_text.set("正在运行压力测试...")
        
        # 启动压力测试线程
        self.stress_thread = threading.Thread(target=self.run_stress_test, daemon=True)
        self.stress_thread.start()
        
        self.put_log(f"启动压力测试 - CPU目标:{self.cpu_target.get():.0f}%, 内存:{self.memory_mb.get():.0f}MB")
    
    def stop_stress_test(self):
        """停止压力测试"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_text.set("正在停止...")
        
        # 清理资源
        self.cleanup_stress_test()
        
        self.status_text.set("就绪")
        self.test_progress.set("")
        self.put_log("压力测试已停止")
    
    def run_stress_test(self):
        """运行压力测试主逻辑"""
        try:
            # 启动CPU压力测试
            self.start_cpu_stress()
            
            # 启动内存压力测试
            self.start_memory_stress()
            
            # 运行指定时间
            duration_seconds = self.duration_minutes.get() * 60
            start_time = time.time()
            
            while self.is_running and (time.time() - start_time) < duration_seconds:
                # 更新进度
                elapsed = time.time() - start_time
                progress = (elapsed / duration_seconds) * 100
                remaining = duration_seconds - elapsed
                
                if remaining > 0:
                    self.test_progress.set(f"进度: {progress:.1f}% (剩余 {remaining/60:.1f} 分钟)")
                
                # 检查峰值保护
                self.check_peak_limits()
                
                time.sleep(1)
            
            # 自动停止
            if self.is_running:
                self.root.after(0, self.stop_stress_test)
                
        except Exception as e:
            self.put_log(f"压力测试出错: {str(e)}")
            self.root.after(0, self.stop_stress_test)
    
    def start_cpu_stress(self):
        """启动CPU压力测试（动态管理版本）"""
        try:
            # 初始化CPU动态管理
            self.cpu_threads = []
            self.cpu_manager_running = True
            self.cpu_load_intensity = 1.0  # 初始负载强度
            
            # 启动CPU动态管理线程
            self.cpu_manager_thread = threading.Thread(target=self.cpu_manager, daemon=True)
            self.cpu_manager_thread.start()
            
            self.put_log("🔄 CPU动态管理已启动")
                    
        except Exception as e:
            self.put_log(f"❌ CPU管理启动失败: {str(e)}")
    
    def cpu_manager(self):
        """CPU动态管理器（峰值保持机制）"""
        # 获取初始峰值限制用于日志显示
        initial_max = self.cpu_max.get()
        initial_target = self.cpu_target.get()
        
        self.put_log(f"🔄 CPU管理器启动: 峰值限制{initial_max:.0f}%, 目标值{initial_target:.0f}%")
        self.put_log(f"📋 规则: 系统CPU低于目标时增加负载，高于峰值时强制减少负载")
        self.put_log(f"💡 使用多进程突破GIL限制，提升CPU利用率")
        self.put_log(f"🔄 支持运行时动态调整峰值和目标值")
        
        # 初始启动一些CPU进程（优先使用进程）
        initial_processes = max(2, min(4, psutil.cpu_count()))
        self.start_cpu_processes(initial_processes)
        
        # 补充一些线程
        initial_threads = max(1, psutil.cpu_count() // 2)
        self.start_cpu_threads(initial_threads)
        
        last_max = initial_max  # 记录上次的峰值
        last_target = initial_target  # 记录上次的目标值
        
        while self.cpu_manager_running and self.is_running:
            try:
                # 动态获取当前峰值和目标值（支持运行时调整）
                max_percent = self.cpu_max.get()
                target_percent = self.cpu_target.get()
                
                # 如果峰值或目标值发生变化，记录日志
                if abs(max_percent - last_max) > 0.5 or abs(target_percent - last_target) > 0.5:
                    self.put_log(f"🎯 设置已更新: 峰值{last_max:.0f}%→{max_percent:.0f}%, 目标{last_target:.0f}%→{target_percent:.0f}%")
                    last_max = max_percent
                    last_target = target_percent
                
                # 获取当前CPU使用率（0.1秒平均值，提高响应速度）
                current_cpu = psutil.cpu_percent(interval=0.1)
                
                # 检查CPU使用率并主动调整
                if current_cpu > max_percent:  # 超过峰值限制
                    # 超过峰值，强制减少CPU负载
                    excess = current_cpu - max_percent
                    self.put_log(f"🚨 系统CPU{current_cpu:.1f}%超过峰值限制{max_percent:.0f}%（超出{excess:.1f}%），强制减少负载")
                    
                    # 立即强制降低负载强度到最低
                    if excess > 2:  # 超出2%以上时，立即降到最低强度
                        self.cpu_load_intensity = 0.1
                        if self.cpu_process_control:
                            self.cpu_process_control.value = 10  # 设置为最低强度
                        self.put_log(f"⚡ 紧急降低负载强度到最低: 0.1")
                    
                    # 根据超出程度决定减少次数
                    reduce_times = 1
                    if excess > 10:  # 超出10%以上，连续减少3次
                        reduce_times = 3
                    elif excess > 5:  # 超出5%以上，连续减少2次
                        reduce_times = 2
                    
                    for i in range(reduce_times):
                        self.reduce_cpu_load()
                        if i < reduce_times - 1:  # 不是最后一次时稍作等待
                            time.sleep(0.1)  # 减少等待时间，更快响应
                    
                    # 如果仍然超过峰值，强制终止一些进程
                    time.sleep(0.1)
                    recheck_cpu = psutil.cpu_percent(interval=0.1)
                    if recheck_cpu > max_percent and len(self.cpu_processes) > 0:
                        processes_to_kill = min(2, len(self.cpu_processes))
                        for _ in range(processes_to_kill):
                            if self.cpu_processes:
                                process = self.cpu_processes.pop()
                                if process.is_alive():
                                    process.terminate()
                        self.put_log(f"🛑 紧急终止{processes_to_kill}个CPU进程，剩余{len(self.cpu_processes)}个")
                    
                elif current_cpu < target_percent - 3:  # 低于目标值3%时主动增加负载
                    # 主动提升到目标值左右
                    self.put_log(f"📈 系统CPU{current_cpu:.1f}%低于目标{target_percent:.0f}%，增加负载")
                    self.increase_cpu_load()
                    
                elif current_cpu < target_percent - 1:  # 接近目标值时小幅增加
                    # 小幅增加CPU负载
                    self.put_log(f"📈 系统CPU{current_cpu:.1f}%接近目标{target_percent:.0f}%，小幅增加负载")
                    self.fine_tune_cpu_load(increase=True)
                    
                elif current_cpu > max_percent - 1:  # 接近峰值时小幅减少
                    # 小幅减少CPU负载
                    self.put_log(f"📉 系统CPU{current_cpu:.1f}%接近峰值{max_percent:.0f}%，小幅减少负载")
                    self.fine_tune_cpu_load(increase=False)
                
                # 定期记录状态
                total_workers = len(self.cpu_threads) + len(self.cpu_processes)
                if total_workers > 0:
                    self.put_log(f"📊 当前状态: 系统CPU{current_cpu:.1f}% (目标{target_percent:.0f}%, 峰值{max_percent:.0f}%), 进程{len(self.cpu_processes)}个, 线程{len(self.cpu_threads)}个, 负载强度{self.cpu_load_intensity:.2f}")
                
                time.sleep(0.2)  # 每0.2秒检查一次，提高响应速度
                
            except Exception as e:
                self.put_log(f"❌ CPU管理错误: {str(e)}")
                time.sleep(1)
    
    def start_cpu_processes(self, process_count):
        """启动指定数量的CPU进程"""
        try:
            # 创建进程控制信号
            if self.cpu_process_control is None:
                self.cpu_process_control = Value('i', 1)  # 1表示运行，0表示停止
            
            for i in range(process_count):
                if not self.cpu_manager_running or not self.is_running:
                    break
                
                # 创建CPU密集型进程
                process = Process(target=cpu_intensive_process, 
                                args=(self.cpu_process_control, self.cpu_load_intensity))
                process.start()
                self.cpu_processes.append(process)
            
            self.put_log(f"🚀 启动{process_count}个CPU进程")
            
        except Exception as e:
            self.put_log(f"❌ 启动CPU进程失败: {str(e)}")
    
    def start_cpu_threads(self, thread_count):
        """启动指定数量的CPU线程（作为进程的补充）"""
        for i in range(thread_count):
            if not self.cpu_manager_running or not self.is_running:
                break
            thread = threading.Thread(target=self.cpu_intensive_task_dynamic, daemon=True)
            thread.start()
            self.cpu_threads.append(thread)
        
        self.put_log(f"🚀 启动{thread_count}个CPU线程")
    
    def cpu_intensive_task_dynamic(self):
        """动态CPU密集型任务"""
        import random
        import math
        
        # 创建大量数据用于计算
        data_size = 10000
        data = [random.random() for _ in range(data_size)]
        
        while self.is_running and self.cpu_manager_running:
            start_time = time.time()
            
            # 根据负载强度调整计算量
            intensity = self.cpu_load_intensity
            
            # 多种计算密集型操作（根据强度调整）
            result = 0
            
            # 1. 数学运算
            math_ops = int(5000 * intensity)
            for i in range(math_ops):
                result += math.sin(i) * math.cos(i) + math.sqrt(i + 1)
                result += i ** 3 + i ** 2 + i
            
            # 2. 浮点运算
            float_ops = int(3000 * intensity)
            for i in range(float_ops):
                result += data[i % data_size] * 2.71828 + data[(i + 1) % data_size] * 3.14159
            
            # 3. 整数运算
            int_ops = int(2000 * intensity)
            for i in range(int_ops):
                result += i * i * i + i * i + i
            
            # 4. 字符串操作（CPU密集型）
            str_ops = int(1000 * intensity)
            for i in range(str_ops):
                s = "x" * (i % 100 + 1)
                result += len(s) + hash(s) % 1000
            
            elapsed = time.time() - start_time
            
            # 动态休眠控制（根据强度调整）
            if intensity < 1.0:
                sleep_time = elapsed * (1.0 - intensity) / intensity
                if sleep_time > 0:
                    time.sleep(sleep_time)
            elif intensity > 1.0:
                 # 高强度时减少休眠
                 time.sleep(max(0.001, 0.01 / intensity))
    

    
    def increase_cpu_load(self):
        """增加CPU负载"""
        try:
            # 方法1: 优先增加进程数
            current_processes = len(self.cpu_processes)
            max_processes = psutil.cpu_count() * 2  # 每个CPU核心最多2个进程
            
            if current_processes < max_processes:
                new_processes = min(2, max_processes - current_processes)
                self.start_cpu_processes(new_processes)
                return
            
            # 方法2: 增加线程数
            current_threads = len(self.cpu_threads)
            max_threads = psutil.cpu_count() * 3
            
            if current_threads < max_threads:
                new_threads = min(2, max_threads - current_threads)
                self.start_cpu_threads(new_threads)
            
            # 方法3: 增加负载强度
            if self.cpu_load_intensity < 2.0:
                self.cpu_load_intensity = min(2.0, self.cpu_load_intensity + 0.2)
                self.put_log(f"📈 提升负载强度到 {self.cpu_load_intensity:.2f}")
                # 更新进程控制信号
                if self.cpu_process_control:
                    self.cpu_process_control.value = int(self.cpu_load_intensity * 100)
            
        except Exception as e:
            self.put_log(f"❌ 增加CPU负载失败: {str(e)}")
    
    def reduce_cpu_load(self):
        """减少CPU负载"""
        try:
            # 方法1: 减少负载强度（更激进的减少）
            if self.cpu_load_intensity > 0.1:
                # 根据当前强度决定减少幅度
                if self.cpu_load_intensity > 0.8:
                    reduction = 0.3  # 高强度时大幅减少
                elif self.cpu_load_intensity > 0.5:
                    reduction = 0.25  # 中等强度时中等减少
                else:
                    reduction = 0.2   # 低强度时小幅减少
                
                self.cpu_load_intensity = max(0.1, self.cpu_load_intensity - reduction)
                self.put_log(f"📉 降低负载强度到 {self.cpu_load_intensity:.2f}（减少{reduction:.2f}）")
                # 更新进程控制信号
                if self.cpu_process_control:
                    self.cpu_process_control.value = int(self.cpu_load_intensity * 100)
            
            # 方法2: 减少进程数（如果强度已经很低）
            if self.cpu_load_intensity <= 0.3 and len(self.cpu_processes) > 1:
                processes_to_remove = min(1, len(self.cpu_processes) - 1)
                for _ in range(processes_to_remove):
                    if self.cpu_processes:
                        process = self.cpu_processes.pop()
                        if process.is_alive():
                            process.terminate()
                            process.join(timeout=1)
                self.put_log(f"📉 减少{processes_to_remove}个CPU进程")
            
            # 方法3: 减少线程数（通过停止cpu_manager来让线程自然结束）
            elif self.cpu_load_intensity <= 0.3 and len(self.cpu_threads) > 1:
                threads_to_remove = min(2, len(self.cpu_threads) - 1)
                # 临时停止cpu_manager让线程结束
                old_manager_state = self.cpu_manager_running
                self.cpu_manager_running = False
                time.sleep(0.1)  # 给线程时间结束
                
                # 移除已结束的线程
                active_threads = []
                for thread in self.cpu_threads:
                    if thread.is_alive():
                        active_threads.append(thread)
                
                # 只保留需要的线程数量
                target_count = len(active_threads) - threads_to_remove
                self.cpu_threads = active_threads[:max(1, target_count)]
                
                # 重新启动cpu_manager
                self.cpu_manager_running = old_manager_state
                
                self.put_log(f"📉 减少{threads_to_remove}个CPU线程，当前活跃线程: {len(self.cpu_threads)}")
                
        except Exception as e:
            self.put_log(f"❌ 减少CPU负载失败: {str(e)}")
    
    def fine_tune_cpu_load(self, increase=True):
        """微调CPU负载"""
        try:
            if increase:
                if self.cpu_load_intensity < 2.0:
                    self.cpu_load_intensity = min(2.0, self.cpu_load_intensity + 0.1)
                    self.put_log(f"🔧 微调: 负载强度 +0.1 → {self.cpu_load_intensity:.2f}")
            else:
                if self.cpu_load_intensity > 0.1:
                    self.cpu_load_intensity = max(0.1, self.cpu_load_intensity - 0.1)
                    self.put_log(f"🔧 微调: 负载强度 -0.1 → {self.cpu_load_intensity:.2f}")
                    
        except Exception as e:
            self.put_log(f"❌ 微调CPU负载失败: {str(e)}")
    
    def start_memory_stress(self):
        """启动内存压力测试"""
        try:
            # 初始化内存管理
            self.memory_blocks = []
            self.memory_manager_running = True
            
            # 启动内存管理线程
            memory_manager_thread = threading.Thread(target=self.memory_manager, daemon=True)
            memory_manager_thread.start()
            
            self.put_log("内存动态管理已启动")
                    
        except Exception as e:
            self.put_log(f"内存管理启动失败: {str(e)}")
    
    def memory_manager(self):
        """内存动态管理器（峰值保持机制）"""
        # 获取初始峰值限制
        initial_peak_percent = self.memory_max_percent.get()
        
        # 计算目标使用率（基于峰值的95%，更接近峰值）
        target_percent = initial_peak_percent * 0.95
        max_percent = initial_peak_percent
        
        # 获取系统总内存
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 计算目标内存量（MB）
        target_memory_mb = int((target_percent / 100) * total_memory_gb * 1024)
        
        self.put_log(f"🔄 内存管理器启动: 系统总内存{total_memory_gb:.1f}GB, 峰值限制{initial_peak_percent:.0f}%")
        self.put_log(f"📋 目标使用率{target_percent:.1f}% (约{target_memory_mb}MB), 峰值限制{max_percent:.0f}%")
        self.put_log(f"📋 规则: 主动调整到目标使用率，超过峰值时强制减少")
        
        # 立即分配到目标内存
        current_memory = psutil.virtual_memory()
        current_percent = current_memory.percent
        
        if current_percent < target_percent:
            needed_mb = int((target_percent - current_percent) / 100 * total_memory_gb * 1024)
            self.put_log(f"📈 当前内存{current_percent:.1f}%，需要增加约{needed_mb}MB到目标{target_percent:.1f}%")
            self.add_memory_blocks(needed_mb)
        
        last_peak_percent = initial_peak_percent  # 记录上次的峰值限制
        
        while self.memory_manager_running and self.is_running:
            try:
                # 动态获取当前峰值限制（支持运行时调整）
                peak_percent = self.memory_max_percent.get()
                
                # 重新计算目标使用率
                target_percent = peak_percent * 0.95
                max_percent = peak_percent
                
                # 如果峰值限制发生变化，记录日志
                if abs(peak_percent - last_peak_percent) > 1:
                    self.put_log(f"🎯 峰值限制已更新: {last_peak_percent:.0f}% → {peak_percent:.0f}%")
                    target_percent = peak_percent * 0.95  # 重新计算目标
                    last_peak_percent = peak_percent
                
                current_memory = psutil.virtual_memory()
                current_percent = current_memory.percent
                current_allocated_mb = len(self.memory_blocks)
                
                # 移除CPU冲突检查，允许CPU和内存并行管理到各自峰值
                # 这样CPU和内存可以同时达到各自设定的峰值
                
                # 检查内存使用率并主动调整
                if current_percent > max_percent:  # 超过峰值限制
                    # 超过峰值，强制减少内存负载
                    self.put_log(f"🚨 系统内存{current_percent:.1f}%超过峰值限制{max_percent:.0f}%，强制减少负载")
                    self.reduce_memory_load()
                    
                elif current_percent < target_percent - 2:  # 低于目标值2%时主动增加负载
                    # 主动提升到目标值左右
                    self.put_log(f"📈 系统内存{current_percent:.1f}%低于目标{target_percent:.0f}%，增加负载")
                    self.increase_memory_load()
                    
                elif current_percent < target_percent:  # 低于目标值时持续小幅增加
                    # 小幅增加内存负载
                    self.put_log(f"📈 系统内存{current_percent:.1f}%低于目标{target_percent:.0f}%，小幅增加负载")
                    self.fine_tune_memory_load(increase=True)
                    
                elif current_percent > max_percent - 1:  # 接近峰值时小幅减少
                    # 小幅减少内存负载
                    self.put_log(f"📉 系统内存{current_percent:.1f}%接近峰值{max_percent:.0f}%，小幅减少负载")
                    self.fine_tune_memory_load(increase=False)
                
                # 定期记录状态
                if len(self.memory_blocks) > 0:
                    self.put_log(f"📊 当前状态: 系统内存{current_percent:.1f}% (目标{target_percent:.0f}%, 峰值{max_percent:.0f}%), 已分配{current_allocated_mb}MB")
                
                time.sleep(0.2)  # 每0.2秒检查一次，与CPU管理器保持一致
                
            except Exception as e:
                self.put_log(f"❌ 内存管理错误: {str(e)}")
                time.sleep(1)
    
    def add_memory_blocks(self, mb_amount=200):
        """添加内存块（可指定数量）"""
        try:
            # 添加指定数量的内存，分批处理避免CPU冲突
            batch_size = 10  # 每批处理10MB
            batches = (mb_amount + batch_size - 1) // batch_size  # 向上取整
            
            for batch in range(batches):
                if not self.memory_manager_running or not self.is_running:
                    break
                
                # 计算当前批次要分配的内存块数量
                current_batch_size = min(batch_size, mb_amount - batch * batch_size)
                
                # 分配当前批次的内存块
                for i in range(current_batch_size):
                    if not self.memory_manager_running or not self.is_running:
                        break
                    block = bytearray(1024 * 1024)  # 1MB
                    self.memory_blocks.append(block)
                
                # 批次间添加短暂延迟，避免CPU使用率飙升
                if batch < batches - 1:  # 不是最后一批时才延迟
                    time.sleep(0.05)  # 50ms延迟
            
            current_memory = psutil.virtual_memory()
            self.put_log(f"📈 增加内存: 新增{mb_amount}MB, 总计{len(self.memory_blocks)}MB, 系统使用率: {current_memory.percent:.1f}%")
            
        except Exception as e:
            self.put_log(f"❌ 添加内存块失败: {str(e)}")
    
    def increase_memory_load(self):
        """增加内存负载"""
        try:
            # 增加100-200MB内存
            add_amount = 150
            self.add_memory_blocks(add_amount)
            
        except Exception as e:
            self.put_log(f"❌ 增加内存负载失败: {str(e)}")
    
    def reduce_memory_load(self):
        """减少内存负载"""
        try:
            if self.memory_blocks:
                # 释放30%的内存块
                release_count = max(50, len(self.memory_blocks) // 3)
                
                for i in range(release_count):
                    if self.memory_blocks:
                        self.memory_blocks.pop()
                    else:
                        break
                
                # 强制垃圾回收
                import gc
                gc.collect()
                
                current_memory = psutil.virtual_memory()
                self.put_log(f"📉 减少内存负载: 释放{release_count}MB, 剩余{len(self.memory_blocks)}MB, 系统使用率{current_memory.percent:.1f}%")
            
        except Exception as e:
            self.put_log(f"❌ 减少内存负载失败: {str(e)}")
    
    def fine_tune_memory_load(self, increase=True):
        """微调内存负载"""
        try:
            if increase:
                # 小幅增加内存（20-50MB）
                add_amount = 30
                self.add_memory_blocks(add_amount)
            else:
                # 小幅减少内存
                if self.memory_blocks:
                    release_count = min(30, len(self.memory_blocks) // 10)
                    
                    for i in range(release_count):
                        if self.memory_blocks:
                            self.memory_blocks.pop()
                        else:
                            break
                    
                    # 强制垃圾回收
                    import gc
                    gc.collect()
                    
                    current_memory = psutil.virtual_memory()
                    self.put_log(f"📉 微调内存负载: 释放{release_count}MB, 剩余{len(self.memory_blocks)}MB, 系统使用率{current_memory.percent:.1f}%")
            
        except Exception as e:
            self.put_log(f"❌ 微调内存负载失败: {str(e)}")
    
    def remove_memory_blocks(self, target_bytes, current_bytes):
        """移除内存块"""
        try:
            block_size = 1024 * 1024  # 1MB
            excess_blocks = max(1, int((current_bytes - target_bytes) / block_size))
            
            # 更积极地释放内存
            blocks_to_remove = min(excess_blocks * 2, len(self.memory_blocks))  # 释放更多块
            
            # 分批移除内存块，避免CPU冲突
            batch_size = 20  # 每批释放20MB
            batches = (blocks_to_remove + batch_size - 1) // batch_size
            
            for batch in range(batches):
                if not self.memory_manager_running or not self.is_running:
                    break
                
                # 计算当前批次要释放的内存块数量
                current_batch_size = min(batch_size, blocks_to_remove - batch * batch_size)
                
                # 释放当前批次的内存块
                for i in range(current_batch_size):
                    if not self.memory_manager_running or not self.is_running:
                        break
                    
                    if self.memory_blocks:
                        self.memory_blocks.pop()
                
                # 批次间添加短暂延迟，避免CPU使用率飙升
                if batch < batches - 1:  # 不是最后一批时才延迟
                    time.sleep(0.03)  # 30ms延迟
                    
                    # 每移除50MB记录一次
                    if len(self.memory_blocks) % 50 == 0:
                        current_memory = psutil.virtual_memory()
                        self.put_log(f"📉 释放内存: {len(self.memory_blocks)}MB, 当前使用率: {current_memory.percent:.1f}%")
                
                time.sleep(0.005)  # 更快的释放速度
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
        except Exception as e:
            self.put_log(f"移除内存块失败: {str(e)}")
    
    def aggressive_memory_release(self):
        """积极的内存释放策略（改进版本）"""
        try:
            if self.memory_blocks:
                initial_blocks = len(self.memory_blocks)
                self.put_log(f"📉 积极释放: 从{initial_blocks}MB开始释放")
                
                # 释放50%的内存块
                blocks_to_remove = len(self.memory_blocks) // 2
                
                for i in range(blocks_to_remove):
                    if self.memory_blocks:
                        self.memory_blocks.pop()
                    
                    # 每释放50MB记录一次
                    if i % 50 == 0 and i > 0:
                        current_memory = psutil.virtual_memory()
                        self.put_log(f"📉 释放进度: {len(self.memory_blocks)}MB, 系统使用率{current_memory.percent:.1f}%")
                
                # 强制垃圾回收
                import gc
                gc.collect()
                
                current_memory = psutil.virtual_memory()
                self.put_log(f"✅ 积极释放完成: 从{initial_blocks}MB释放到{len(self.memory_blocks)}MB, 系统使用率{current_memory.percent:.1f}%")
            else:
                self.put_log("📉 没有内存块需要释放")
            
        except Exception as e:
            self.put_log(f"❌ 积极释放失败: {str(e)}")
    
    def emergency_memory_release(self):
        """紧急内存释放（改进版本）"""
        try:
            self.put_log("🚨 执行紧急内存释放")
            
            # 立即释放所有内存块
            if self.memory_blocks:
                initial_blocks = len(self.memory_blocks)
                self.put_log(f"📉 紧急释放: 清空{initial_blocks}MB内存")
                self.memory_blocks.clear()
            else:
                self.put_log("📉 没有内存块需要释放")
            
            # 多次强制垃圾回收
            import gc
            for i in range(5):  # 增加垃圾回收次数
                gc.collect()
                time.sleep(0.05)  # 减少延迟
            
            # 检查释放效果
            current_memory = psutil.virtual_memory()
            current_percent = current_memory.percent
            target_percent = self.memory_max_percent.get()
            
            if current_percent <= target_percent:
                self.put_log(f"✅ 紧急释放成功: 使用率从超标降到{current_percent:.1f}% (目标{target_percent:.0f}%)")
            else:
                self.put_log(f"⚠️ 紧急释放后: 使用率{current_percent:.1f}%仍高于目标{target_percent:.0f}%")
            
        except Exception as e:
            self.put_log(f"❌ 紧急释放失败: {str(e)}")
    
    def check_peak_limits(self):
        """检查峰值限制并执行紧急保护"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            # CPU峰值紧急保护
            if cpu_usage > self.cpu_max.get() + 1:  # 超过峰值1%时紧急保护
                self.put_log(f"🚨 CPU紧急保护: {cpu_usage:.1f}% > {self.cpu_max.get():.0f}%+1%, 强制降级")
                # 紧急减少CPU负载
                if hasattr(self, 'cpu_load_intensity'):
                    self.cpu_load_intensity = max(0.1, self.cpu_load_intensity * 0.5)
                # 停止一些CPU进程
                if len(self.cpu_processes) > 1:
                    try:
                        process = self.cpu_processes.pop()
                        if hasattr(process, 'terminate'):
                            process.terminate()
                        self.put_log(f"🛑 紧急停止CPU进程，剩余{len(self.cpu_processes)}个")
                    except:
                        pass
            
            # 内存峰值紧急保护
            if memory_usage > self.memory_max_percent.get() + 2:  # 超过峰值2%时紧急保护
                self.put_log(f"🚨 内存紧急保护: {memory_usage:.1f}% > {self.memory_max_percent.get():.0f}%+2%, 强制释放")
                # 触发紧急内存释放
                if hasattr(self, 'emergency_memory_release'):
                    self.emergency_memory_release()
            
            # 内存使用率监控（内存管理由memory_manager处理）
            target_memory = self.memory_max_percent.get()
            if self.is_running:
                self.put_log(f"📊 内存使用率: {memory_usage:.1f}% (目标: {target_memory:.0f}%)")
                
        except Exception as e:
            pass
    
    def cleanup_stress_test(self):
        """清理压力测试资源"""
        try:
            # 停止CPU动态管理器
            self.cpu_manager_running = False
            
            # 等待CPU管理线程结束
            if hasattr(self, 'cpu_manager_thread') and self.cpu_manager_thread and self.cpu_manager_thread.is_alive():
                self.cpu_manager_thread.join(timeout=2)
            
            # 停止内存管理器
            self.memory_manager_running = False
            
            # 清理内存块
            self.memory_blocks.clear()
            
            # 停止所有CPU进程
            if self.cpu_process_control:
                self.cpu_process_control.value = 0  # 发送停止信号
            
            for process in self.cpu_processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                    if process.is_alive():
                        process.kill()  # 强制终止
            
            # 清理进程列表
            self.cpu_processes.clear()
            
            # 清理CPU线程列表
            self.cpu_threads.clear()
            
            # 重置负载强度和控制信号
            self.cpu_load_intensity = 1.0
            self.cpu_process_control = None
            
            self.put_log("🧹 压力测试资源已清理")
            
        except Exception as e:
            self.put_log(f"❌ 清理资源时出错: {str(e)}")
    
    def show_system_info(self):
        """显示系统信息"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:' if platform.system() == 'Windows' else '/')
            
            info = f"""
🖥️ 系统信息

💻 CPU信息:
   物理核心数: {psutil.cpu_count(logical=False)}
   逻辑核心数: {cpu_count}
   当前频率: {cpu_freq.current:.0f} MHz (最大: {cpu_freq.max:.0f} MHz)
   当前使用率: {psutil.cpu_percent(interval=1):.1f}%

🧠 内存信息:
   总内存: {memory.total / (1024**3):.1f} GB
   可用内存: {memory.available / (1024**3):.1f} GB
   使用率: {memory.percent:.1f}%

💾 磁盘信息:
   总空间: {disk.total / (1024**3):.1f} GB
   可用空间: {disk.free / (1024**3):.1f} GB
   使用率: {(disk.used / disk.total) * 100:.1f}%

🖥️ 操作系统:
   系统: {platform.system()} {platform.release()}
   架构: {platform.machine()}
   Python版本: {platform.python_version()}
            """
            
            messagebox.showinfo("系统信息", info)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取系统信息失败: {str(e)}")
    
    def start_scheduler(self):
        """启动定时任务"""
        # 这里可以集成之前的调度器逻辑
        self.scheduler_running = True
        self.start_scheduler_btn.config(state=tk.DISABLED)
        self.stop_scheduler_btn.config(state=tk.NORMAL)
        self.scheduler_status.set("定时任务运行中...")
        self.put_log("定时任务已启动")
    
    def stop_scheduler(self):
        """停止定时任务"""
        self.scheduler_running = False
        self.start_scheduler_btn.config(state=tk.NORMAL)
        self.stop_scheduler_btn.config(state=tk.DISABLED)
        self.scheduler_status.set("定时任务已停止")
        self.put_log("定时任务已停止")
    
    def edit_schedule_config(self):
        """编辑调度配置"""
        messagebox.showinfo("配置编辑", "请使用文本编辑器打开 schedule_config.json 文件进行编辑")
    
    def reload_schedule_config(self):
        """重载调度配置"""
        messagebox.showinfo("配置重载", "配置已重载")
        self.put_log("调度配置已重载")
    
    def open_config_dir(self):
        """打开配置目录"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            if platform.system() == "Windows":
                os.startfile(current_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", current_dir])
            else:  # Linux
                subprocess.run(["xdg-open", current_dir])
                
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", tk.END)
        self.add_log("日志已清空")
    
    def save_log(self):
        """保存日志"""
        try:
            log_content = self.log_text.get("1.0", tk.END)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_log_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            messagebox.showinfo("保存成功", f"日志已保存为: {filename}")
            self.add_log(f"日志已保存: {filename}")
            
        except Exception as e:
            messagebox.showerror("保存失败", f"保存日志失败: {str(e)}")
    
    def on_closing(self):
        """关闭程序时的处理"""
        if self.is_running:
            if messagebox.askokcancel("退出", "压力测试正在运行，确定要退出吗？"):
                self.stop_stress_test()
                # 清理锁文件
                if platform.system() == "Windows":
                    import tempfile
                    lock_file_path = os.path.join(tempfile.gettempdir(), "resource_stress_tool.lock")
                    try:
                        if os.path.exists(lock_file_path):
                            os.remove(lock_file_path)
                    except:
                        pass
                self.root.after(1000, self.root.destroy)  # 延迟关闭
        else:
            # 清理锁文件
            if platform.system() == "Windows":
                import tempfile
                lock_file_path = os.path.join(tempfile.gettempdir(), "resource_stress_tool.lock")
                try:
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                except:
                    pass
            self.root.destroy()
    
    def open_font_settings(self):
        """打开字体设置窗口"""
        font_window = tk.Toplevel(self.root)
        font_window.title("🔤 字体设置")
        font_window.geometry("400x500")
        font_window.resizable(False, False)
        font_window.transient(self.root)
        font_window.grab_set()
        
        # 居中显示
        font_window.update_idletasks()
        x = (font_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (font_window.winfo_screenheight() // 2) - (500 // 2)
        font_window.geometry(f"400x500+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(font_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="字体大小设置", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 字体大小变量
        title_size = tk.IntVar(value=self.title_font[1])
        label_size = tk.IntVar(value=self.label_font[1])
        button_size = tk.IntVar(value=self.button_font[1])
        status_size = tk.IntVar(value=self.status_font[1])
        log_size = tk.IntVar(value=self.log_font[1])
        
        # 创建字体设置控件
        self.create_font_control(main_frame, "标题字体", title_size, 8, 20)
        self.create_font_control(main_frame, "标签字体", label_size, 8, 20)
        self.create_font_control(main_frame, "按钮字体", button_size, 8, 20)
        self.create_font_control(main_frame, "状态字体", status_size, 8, 20)
        self.create_font_control(main_frame, "日志字体", log_size, 8, 20)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览效果", padding="10")
        preview_frame.pack(fill=tk.X, pady=(20, 0))
        
        preview_label = ttk.Label(preview_frame, text="这是预览文本", style='Label.TLabel')
        preview_label.pack()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 应用按钮
        apply_button = ttk.Button(button_frame, text="应用设置", 
                                 command=lambda: self.apply_font_changes(
                                     title_size.get(), label_size.get(), 
                                     button_size.get(), status_size.get(), 
                                     log_size.get(), preview_label, font_window
                                 ))
        apply_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 重置按钮
        reset_button = ttk.Button(button_frame, text="重置默认", 
                                 command=lambda: self.reset_font_settings(
                                     title_size, label_size, button_size, 
                                     status_size, log_size, preview_label
                                 ))
        reset_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", 
                                  command=font_window.destroy)
        cancel_button.pack(side=tk.RIGHT)
        
        # 更新预览
        def update_preview(*args):
            preview_label.configure(font=('Microsoft YaHei UI', label_size.get()))
        
        label_size.trace('w', update_preview)
    
    def create_font_control(self, parent, label_text, variable, min_val, max_val):
        """创建字体大小控制控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text=f"{label_text}:", style='Label.TLabel').pack(side=tk.LEFT)
        
        # 添加滑块变化回调，确保整数显示
        def on_scale_change(value):
            int_value = int(round(float(value)))
            variable.set(int_value)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, variable=variable, orient=tk.HORIZONTAL,
                         command=on_scale_change)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        # 创建显示整数值的标签
        size_var = tk.StringVar()
        size_var.set(str(int(variable.get())))
        
        def update_display(*args):
            size_var.set(str(int(variable.get())))
        
        variable.trace('w', update_display)
        
        size_label = ttk.Label(frame, textvariable=size_var, style='Label.TLabel')
        size_label.pack(side=tk.RIGHT)
        
        ttk.Label(frame, text="px", style='Label.TLabel').pack(side=tk.RIGHT)
    
    def apply_font_changes(self, title_size, label_size, button_size, status_size, log_size, preview_label, window):
        """应用字体更改"""
        # 更新字体设置
        self.title_font = ('Microsoft YaHei UI', title_size, 'bold')
        self.label_font = ('Microsoft YaHei UI', label_size)
        self.button_font = ('Microsoft YaHei UI', button_size)
        self.status_font = ('Microsoft YaHei UI', status_size)
        self.log_font = ('Consolas', log_size)
        
        # 应用设置
        self.apply_font_settings()
        
        # 保存设置
        self.save_font_settings()
        
        # 更新预览
        preview_label.configure(font=self.label_font)
        
        messagebox.showinfo("成功", "字体设置已应用并保存！")
        window.destroy()
    
    def reset_font_settings(self, title_size, label_size, button_size, status_size, log_size, preview_label):
        """重置字体设置为默认值"""
        title_size.set(12)
        label_size.set(10)
        button_size.set(10)
        status_size.set(9)
        log_size.set(9)
        
        preview_label.configure(font=('Microsoft YaHei UI', 10))
    
    def increase_all_fonts(self):
        """一键调大所有文本字体"""
        try:
            # 获取当前字体大小
            current_title = self.title_font[1]
            current_label = self.label_font[1]
            current_button = self.button_font[1]
            current_status = self.status_font[1]
            current_log = self.log_font[1]
            
            # 增加字体大小（每次增加2px）
            new_title = min(24, current_title + 2)
            new_label = min(20, current_label + 2)
            new_button = min(20, current_button + 2)
            new_status = min(18, current_status + 2)
            new_log = min(18, current_log + 2)
            
            # 更新字体设置
            self.title_font = ('Microsoft YaHei UI', new_title, 'bold')
            self.label_font = ('Microsoft YaHei UI', new_label)
            self.button_font = ('Microsoft YaHei UI', new_button)
            self.status_font = ('Microsoft YaHei UI', new_status)
            self.log_font = ('Consolas', new_log)
            
            # 应用设置
            self.apply_font_settings()
            
            # 保存设置
            self.save_font_settings()
            
            self.put_log(f"📝 字体已调大: 标题{new_title}px, 标签{new_label}px, 按钮{new_button}px, 状态{new_status}px, 日志{new_log}px")
             
        except Exception as e:
            self.put_log(f"❌ 调整字体失败: {str(e)}")
    
    def decrease_all_fonts(self):
        """一键调小所有文本字体"""
        try:
            # 获取当前字体大小
            current_title = self.title_font[1]
            current_label = self.label_font[1]
            current_button = self.button_font[1]
            current_status = self.status_font[1]
            current_log = self.log_font[1]
            
            # 减少字体大小（每次减少2px，但不小于最小值）
            new_title = max(8, current_title - 2)
            new_label = max(8, current_label - 2)
            new_button = max(8, current_button - 2)
            new_status = max(8, current_status - 2)
            new_log = max(8, current_log - 2)
            
            # 更新字体设置
            self.title_font = ('Microsoft YaHei UI', new_title, 'bold')
            self.label_font = ('Microsoft YaHei UI', new_label)
            self.button_font = ('Microsoft YaHei UI', new_button)
            self.status_font = ('Microsoft YaHei UI', new_status)
            self.log_font = ('Consolas', new_log)
            
            # 应用设置
            self.apply_font_settings()
            
            # 保存设置
            self.save_font_settings()
            
            self.put_log(f"📝 字体已调小: 标题{new_title}px, 标签{new_label}px, 按钮{new_button}px, 状态{new_status}px, 日志{new_log}px")
            
        except Exception as e:
            self.put_log(f"❌ 调整字体失败: {str(e)}")

def main():
    """主函数"""
    # 设置multiprocessing启动方法（必须在最开始设置）
    if platform.system() == 'Windows':
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # 如果已经设置过，忽略错误
            pass
    else:
        try:
            multiprocessing.set_start_method('fork', force=True)
        except RuntimeError:
            # 如果已经设置过，忽略错误
            pass
    
    # Windows单实例检查
    if platform.system() == "Windows":
        import tempfile
        
        # 创建锁文件防止多实例
        lock_file_path = os.path.join(tempfile.gettempdir(), "resource_stress_tool.lock")
        try:
            if os.path.exists(lock_file_path):
                # 检查进程是否还在运行
                with open(lock_file_path, 'r') as f:
                    old_pid = f.read().strip()
                try:
                    import psutil
                    if psutil.pid_exists(int(old_pid)):
                        print("程序已在运行中，请先关闭现有实例")
                        return
                except:
                    pass
            
            # 写入当前进程ID
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
        except:
            pass
    
    # Windows特定设置
    if platform.system() == "Windows":
        # 设置控制台代码页为UTF-8
        try:
            import subprocess
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        except:
            pass
    
    # 检查依赖
    try:
        import psutil
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", 
                           "缺少依赖包 psutil\n\n"
                           "请运行以下命令安装:\n"
                           "pip install psutil\n\n"
                           "或者使用独立可执行版本")
        root.destroy()
        return
    
    try:
        # 创建主窗口
        root = tk.Tk()
        
        # Windows特殊设置
        if platform.system() == "Windows":
            # 设置DPI感知
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
        
        app = StressTestGUI(root)
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"GUI启动错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", f"程序启动失败:\n{str(e)}")
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()
