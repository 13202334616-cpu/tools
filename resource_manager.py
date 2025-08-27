#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器资源配置提升工具
CPU和内存资源动态管理工具
支持Windows和Windows Server系统
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time
import json
import os
import multiprocessing
from datetime import datetime
import platform
import sys

# Windows特定导入
if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes
    import subprocess

class ResourceManager:
    def __init__(self):
        self.root = tk.Tk()
        
        # 检测操作系统
        self.is_windows = platform.system() == 'Windows'
        self.is_macos = platform.system() == 'Darwin'
        self.is_linux = platform.system() == 'Linux'
        
        # Windows特定初始化
        if self.is_windows:
            self.init_windows_specific()
        
        self.setup_window()
        
        # 配置变量
        self.cpu_target = tk.DoubleVar(value=50.0)
        self.memory_target = tk.DoubleVar(value=50.0)
        self.is_running = False
        self.monitor_thread = None
        self.cpu_workers = []
        self.memory_workers = []
        
        # 定时任务
        self.schedules = []
        self.schedule_thread = None
        
        # 状态变量
        self.current_cpu = tk.StringVar(value="0.0%")
        self.current_memory = tk.StringVar(value="0.0%")
        self.status_text = tk.StringVar(value="已停止")
        
        self.create_widgets()
        self.load_config()
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("服务器资源配置提升工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # 设置现代化主题
        style = ttk.Style()
        style.theme_use('clam')
        
        # 定义现代化颜色方案
        colors = {
            'primary': '#2196F3',      # 蓝色
            'primary_dark': '#1976D2', # 深蓝色
            'secondary': '#4CAF50',    # 绿色
            'danger': '#F44336',       # 红色
            'warning': '#FF9800',      # 橙色
            'light': '#FAFAFA',        # 浅灰色
            'dark': '#212121',         # 深灰色
            'border': '#E0E0E0'        # 边框色
        }
        
        # 自定义样式
        style.configure('Title.TLabel', 
                       font=('Microsoft YaHei', 18, 'bold'),
                       foreground=colors['dark'],
                       background='#f0f0f0')
        
        style.configure('Heading.TLabel', 
                       font=('Microsoft YaHei', 12, 'bold'),
                       foreground=colors['primary_dark'])
        
        style.configure('Status.TLabel', 
                       font=('Microsoft YaHei', 10),
                       foreground=colors['dark'])
        
        style.configure('Value.TLabel', 
                       font=('Microsoft YaHei', 11, 'bold'),
                       foreground=colors['primary'])
        
        # 按钮样式
        style.configure('Start.TButton',
                       font=('Microsoft YaHei', 10, 'bold'),
                       foreground='white')
        
        style.configure('Stop.TButton',
                       font=('Microsoft YaHei', 10, 'bold'),
                       foreground='white')
        
        style.configure('Action.TButton',
                       font=('Microsoft YaHei', 9))
        
        # LabelFrame样式
        style.configure('Modern.TLabelframe',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Modern.TLabelframe.Label',
                       font=('Microsoft YaHei', 11, 'bold'),
                       foreground=colors['primary_dark'])
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主滚动框架
        canvas = tk.Canvas(self.root, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 主容器
        main_frame = ttk.Frame(scrollable_frame, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(title_frame, text="服务器资源配置提升工具", style='Title.TLabel')
        title_label.grid(row=0, column=0)
        
        subtitle_label = ttk.Label(title_frame, text="智能CPU和内存资源动态管理", 
                                  font=('Microsoft YaHei', 10), foreground='#666666')
        subtitle_label.grid(row=1, column=0, pady=(5, 0))
        
        # 设置区域容器
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
        # CPU设置区域
        self.create_cpu_section(settings_frame, 0, 0)
        
        # 内存设置区域
        self.create_memory_section(settings_frame, 0, 1)
        
        # 控制按钮区域
        self.create_control_section(main_frame, 2)
        
        # 定时计划区域
        self.create_schedule_section(main_frame, 3)
        
        # 状态显示区域
        self.create_status_section(main_frame, 4)
        
        # 配置滚动
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def create_cpu_section(self, parent, row, column):
        """创建CPU设置区域"""
        cpu_frame = ttk.LabelFrame(parent, text="🖥️ CPU设置", padding="15", style='Modern.TLabelframe')
        cpu_frame.grid(row=row, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=5)
        cpu_frame.columnconfigure(0, weight=1)
        
        # 当前CPU显示
        current_frame = ttk.Frame(cpu_frame)
        current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        current_frame.columnconfigure(1, weight=1)
        
        ttk.Label(current_frame, text="当前占用率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W)
        self.cpu_current_label = ttk.Label(current_frame, textvariable=self.current_cpu, style='Value.TLabel')
        self.cpu_current_label.grid(row=0, column=1, sticky=tk.E)
        
        # 目标设置
        ttk.Label(cpu_frame, text="目标占用率:", font=('Microsoft YaHei', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # 滑块容器
        scale_frame = ttk.Frame(cpu_frame)
        scale_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        scale_frame.columnconfigure(0, weight=1)
        
        cpu_scale = ttk.Scale(scale_frame, from_=1, to=100, variable=self.cpu_target, orient=tk.HORIZONTAL)
        cpu_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 数值显示
        value_frame = ttk.Frame(cpu_frame)
        value_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        value_frame.columnconfigure(1, weight=1)
        
        ttk.Label(value_frame, text="1%", font=('Microsoft YaHei', 8), foreground='#888888').grid(row=0, column=0, sticky=tk.W)
        
        self.cpu_value_label = ttk.Label(value_frame, textvariable=self.cpu_target, style='Value.TLabel')
        self.cpu_value_label.grid(row=0, column=1)
        
        ttk.Label(value_frame, text="100%", font=('Microsoft YaHei', 8), foreground='#888888').grid(row=0, column=2, sticky=tk.E)
        
        # 绑定滑块变化事件
        def update_cpu_value(v):
            value = round(float(v), 1)
            self.cpu_target.set(value)
            self.cpu_value_label.configure(text=f"{value}%")
            self.validate_cpu_setting(value)
        
        cpu_scale.configure(command=update_cpu_value)
        
        # 添加数值输入框
        input_frame = ttk.Frame(cpu_frame)
        input_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="精确设置:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.cpu_entry = ttk.Entry(input_frame, width=8, font=('Microsoft YaHei', 9))
        self.cpu_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.cpu_entry.insert(0, str(self.cpu_target.get()))
        
        ttk.Label(input_frame, text="%", font=('Microsoft YaHei', 9)).grid(row=0, column=2, sticky=tk.W)
        
        ttk.Button(input_frame, text="应用", command=self.apply_cpu_value, width=6).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # 初始化显示
        self.cpu_value_label.configure(text=f"{self.cpu_target.get()}%")
        
        # 添加提示信息
        self.cpu_hint_label = ttk.Label(cpu_frame, text="建议范围: 10-90%", 
                                       font=('Microsoft YaHei', 8), foreground='#666666')
        self.cpu_hint_label.grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        
    def create_memory_section(self, parent, row, column):
        """创建内存设置区域"""
        memory_frame = ttk.LabelFrame(parent, text="💾 内存设置", padding="15", style='Modern.TLabelframe')
        memory_frame.grid(row=row, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=5)
        memory_frame.columnconfigure(0, weight=1)
        
        # 当前内存显示
        current_frame = ttk.Frame(memory_frame)
        current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        current_frame.columnconfigure(1, weight=1)
        
        ttk.Label(current_frame, text="当前占用率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W)
        self.memory_current_label = ttk.Label(current_frame, textvariable=self.current_memory, style='Value.TLabel')
        self.memory_current_label.grid(row=0, column=1, sticky=tk.E)
        
        # 目标设置
        ttk.Label(memory_frame, text="目标占用率:", font=('Microsoft YaHei', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # 滑块容器
        scale_frame = ttk.Frame(memory_frame)
        scale_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        scale_frame.columnconfigure(0, weight=1)
        
        memory_scale = ttk.Scale(scale_frame, from_=1, to=100, variable=self.memory_target, orient=tk.HORIZONTAL)
        memory_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 数值显示
        value_frame = ttk.Frame(memory_frame)
        value_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        value_frame.columnconfigure(1, weight=1)
        
        ttk.Label(value_frame, text="1%", font=('Microsoft YaHei', 8), foreground='#888888').grid(row=0, column=0, sticky=tk.W)
        
        self.memory_value_label = ttk.Label(value_frame, textvariable=self.memory_target, style='Value.TLabel')
        self.memory_value_label.grid(row=0, column=1)
        
        ttk.Label(value_frame, text="100%", font=('Microsoft YaHei', 8), foreground='#888888').grid(row=0, column=2, sticky=tk.E)
        
        # 绑定滑块变化事件
        def update_memory_value(v):
            value = round(float(v), 1)
            self.memory_target.set(value)
            self.memory_value_label.configure(text=f"{value}%")
            self.validate_memory_setting(value)
        
        memory_scale.configure(command=update_memory_value)
        
        # 添加数值输入框
        input_frame = ttk.Frame(memory_frame)
        input_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="精确设置:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.memory_entry = ttk.Entry(input_frame, width=8, font=('Microsoft YaHei', 9))
        self.memory_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.memory_entry.insert(0, str(self.memory_target.get()))
        
        ttk.Label(input_frame, text="%", font=('Microsoft YaHei', 9)).grid(row=0, column=2, sticky=tk.W)
        
        ttk.Button(input_frame, text="应用", command=self.apply_memory_value, width=6).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # 初始化显示
        self.memory_value_label.configure(text=f"{self.memory_target.get()}%")
        
        # 添加提示信息
        self.memory_hint_label = ttk.Label(memory_frame, text="建议范围: 10-85%", 
                                          font=('Microsoft YaHei', 8), foreground='#666666')
        self.memory_hint_label.grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        
    def create_control_section(self, parent, row):
        """创建控制按钮区域"""
        control_frame = ttk.LabelFrame(parent, text="🎮 控制面板", padding="20", style='Modern.TLabelframe')
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=20)
        control_frame.columnconfigure(0, weight=1)
        
        # 主要控制按钮
        main_buttons_frame = ttk.Frame(control_frame)
        main_buttons_frame.grid(row=0, column=0, pady=(0, 15))
        
        self.start_button = ttk.Button(main_buttons_frame, text="🚀 启动管理", 
                                      command=self.start_management, 
                                      style='Start.TButton',
                                      width=15)
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(main_buttons_frame, text="⏹️ 停止管理", 
                                     command=self.stop_management, 
                                     style='Stop.TButton',
                                     state=tk.DISABLED,
                                     width=15)
        self.stop_button.pack(side=tk.LEFT)
        
        # 配置管理按钮
        config_frame = ttk.Frame(control_frame)
        config_frame.grid(row=1, column=0)
        
        ttk.Button(config_frame, text="💾 保存配置", 
                  command=self.save_config, 
                  style='Action.TButton',
                  width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(config_frame, text="📂 加载配置", 
                  command=self.load_config, 
                  style='Action.TButton',
                  width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(config_frame, text="🔄 重置设置", 
                  command=self.reset_settings, 
                  style='Action.TButton',
                  width=12).pack(side=tk.LEFT)
        
    def create_schedule_section(self, parent, row):
        """创建定时计划区域"""
        schedule_frame = ttk.LabelFrame(parent, text="⏰ 定时计划", padding="20", style='Modern.TLabelframe')
        schedule_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=20)
        schedule_frame.columnconfigure(0, weight=1)
        
        # 启用定时功能
        self.schedule_enabled = tk.BooleanVar(value=False)
        enable_frame = ttk.Frame(schedule_frame)
        enable_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Checkbutton(enable_frame, text="启用定时计划", variable=self.schedule_enabled,
                       command=self.toggle_schedule, style='Action.TButton').pack(side=tk.LEFT)
        
        # 计划列表框架
        list_frame = ttk.Frame(schedule_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        list_frame.columnconfigure(0, weight=1)
        
        ttk.Label(list_frame, text="计划列表:", font=('Microsoft YaHei', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 创建Treeview显示计划
        list_container = ttk.Frame(list_frame)
        list_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        list_container.columnconfigure(0, weight=1)
        
        columns = ('时间', '动作', '状态')
        self.schedule_tree = ttk.Treeview(list_container, columns=columns, show='headings', height=4)
        
        for col in columns:
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=100)
        
        # 滚动条
        schedule_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scrollbar.set)
        
        self.schedule_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        schedule_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 添加计划框架
        add_frame = ttk.Frame(schedule_frame)
        add_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        add_frame.columnconfigure(1, weight=1)
        
        # 时间输入
        time_frame = ttk.Frame(add_frame)
        time_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(time_frame, text="时间:", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        
        self.hour_var = tk.StringVar(value="09")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=self.hour_var, format="%02.0f")
        hour_spinbox.pack(side=tk.LEFT, padx=(10, 2))
        
        ttk.Label(time_frame, text=":", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=self.minute_var, format="%02.0f")
        minute_spinbox.pack(side=tk.LEFT, padx=(2, 20))
        
        # 动作选择
        ttk.Label(time_frame, text="动作:", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        
        self.action_var = tk.StringVar(value="启动")
        action_combo = ttk.Combobox(time_frame, textvariable=self.action_var, values=["启动", "停止"], 
                                   state="readonly", width=8)
        action_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(add_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="添加计划", command=self.add_schedule, 
                  style="Action.TButton", width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="删除选中", command=self.remove_schedule, 
                  style="Action.TButton", width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="清空全部", command=self.clear_schedules, 
                  style="Action.TButton", width=12).pack(side=tk.LEFT)
        
        # 初始化计划列表
        self.schedules = []
        
    def create_status_section(self, parent, row):
        """创建状态显示区域"""
        status_frame = ttk.LabelFrame(parent, text="📊 系统状态监控", padding="20", style='Modern.TLabelframe')
        status_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        
        # 运行状态
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        status_info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_info_frame, text="运行状态:", font=('Microsoft YaHei', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        self.status_label = ttk.Label(status_info_frame, textvariable=self.status_text, style='Value.TLabel')
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # CPU状态卡片
        cpu_card = ttk.LabelFrame(status_frame, text="🖥️ CPU状态", padding="15")
        cpu_card.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=5)
        cpu_card.columnconfigure(1, weight=1)
        
        ttk.Label(cpu_card, text="当前占用率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(cpu_card, textvariable=self.current_cpu, style='Value.TLabel').grid(row=0, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(cpu_card, text="目标占用率:", font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cpu_target_display = ttk.Label(cpu_card, text=f"{self.cpu_target.get()}%", style='Status.TLabel')
        self.cpu_target_display.grid(row=1, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(cpu_card, text="工作进程:", font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.cpu_workers_label = ttk.Label(cpu_card, text="0", style='Status.TLabel')
        self.cpu_workers_label.grid(row=2, column=1, sticky=tk.E, pady=2)
        
        # 内存状态卡片
        memory_card = ttk.LabelFrame(status_frame, text="💾 内存状态", padding="15")
        memory_card.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=5)
        memory_card.columnconfigure(1, weight=1)
        
        ttk.Label(memory_card, text="当前占用率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(memory_card, textvariable=self.current_memory, style='Value.TLabel').grid(row=0, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(memory_card, text="目标占用率:", font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.memory_target_display = ttk.Label(memory_card, text=f"{self.memory_target.get()}%", style='Status.TLabel')
        self.memory_target_display.grid(row=1, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(memory_card, text="工作进程:", font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.memory_workers_label = ttk.Label(memory_card, text="0", style='Status.TLabel')
        self.memory_workers_label.grid(row=2, column=1, sticky=tk.E, pady=2)
        
        # 系统详细信息卡片
        system_detail_frame = ttk.LabelFrame(status_frame, text="🖥️ 系统详情", padding="15")
        system_detail_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        system_detail_frame.columnconfigure(1, weight=1)
        system_detail_frame.columnconfigure(3, weight=1)
        
        # 第一列：CPU信息
        ttk.Label(system_detail_frame, text="CPU核心数:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        self.cpu_count_label = ttk.Label(system_detail_frame, text=f"{psutil.cpu_count()}", style='Value.TLabel')
        self.cpu_count_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 20))
        
        ttk.Label(system_detail_frame, text="CPU频率:", font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        self.cpu_freq_label = ttk.Label(system_detail_frame, text="--", style='Value.TLabel')
        self.cpu_freq_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(0, 20))
        
        # 第二列：内存信息
        ttk.Label(system_detail_frame, text="总内存:", font=('Microsoft YaHei', 9)).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(0, 5))
        total_memory = psutil.virtual_memory().total / (1024**3)
        self.total_memory_label = ttk.Label(system_detail_frame, text=f"{total_memory:.1f} GB", style='Value.TLabel')
        self.total_memory_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        ttk.Label(system_detail_frame, text="可用内存:", font=('Microsoft YaHei', 9)).grid(row=1, column=2, sticky=tk.W, pady=2, padx=(0, 5))
        self.available_memory_label = ttk.Label(system_detail_frame, text="--", style='Value.TLabel')
        self.available_memory_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # 磁盘使用情况
        disk_frame = ttk.LabelFrame(status_frame, text="💾 磁盘使用", padding="15")
        disk_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        disk_frame.columnconfigure(1, weight=1)
        disk_frame.columnconfigure(3, weight=1)
        
        ttk.Label(disk_frame, text="磁盘使用率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        self.disk_usage_label = ttk.Label(disk_frame, text="--", style='Value.TLabel')
        self.disk_usage_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 20))
        
        ttk.Label(disk_frame, text="可用空间:", font=('Microsoft YaHei', 9)).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(0, 5))
        self.disk_free_label = ttk.Label(disk_frame, text="--", style='Value.TLabel')
        self.disk_free_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # 网络状态
        network_frame = ttk.LabelFrame(status_frame, text="🌐 网络状态", padding="15")
        network_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        network_frame.columnconfigure(1, weight=1)
        network_frame.columnconfigure(3, weight=1)
        
        ttk.Label(network_frame, text="发送速率:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        self.net_sent_label = ttk.Label(network_frame, text="--", style='Value.TLabel')
        self.net_sent_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 20))
        
        ttk.Label(network_frame, text="接收速率:", font=('Microsoft YaHei', 9)).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(0, 5))
        self.net_recv_label = ttk.Label(network_frame, text="--", style='Value.TLabel')
        self.net_recv_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # 最后更新时间
        update_frame = ttk.Frame(status_frame)
        update_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        update_frame.columnconfigure(1, weight=1)
        
        ttk.Label(update_frame, text="最后更新:", font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.last_update_label = ttk.Label(update_frame, text="--", font=('Microsoft YaHei', 9), foreground='#666666')
        self.last_update_label.grid(row=0, column=1, sticky=tk.W)
        
        # 初始化网络统计
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
    
    def init_windows_specific(self):
        """Windows特定初始化"""
        try:
            # 设置进程优先级为高优先级（Windows）
            import psutil
            current_process = psutil.Process()
            current_process.nice(psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, 'HIGH_PRIORITY_CLASS') else -10)
            
            # 启用DPI感知（Windows）
            try:
                if hasattr(ctypes.windll.shcore, 'SetProcessDpiAwareness'):
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                # 如果DPI设置失败，尝试备用方法
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            # Windows版本检查
            self.check_windows_compatibility()
            print("Windows特定优化已启用")
        except Exception as e:
            print(f"Windows特定初始化失败: {e}")
    
    def check_windows_compatibility(self):
        """检查Windows系统兼容性"""
        try:
            import sys
            windows_version = sys.getwindowsversion()
            if windows_version.major < 10:
                messagebox.showwarning(
                    "兼容性警告", 
                    "检测到Windows版本较旧，建议使用Windows 10或更高版本以获得最佳性能。"
                )
            
            # 检查内存大小
            total_memory = psutil.virtual_memory().total / (1024**3)  # GB
            if total_memory < 4:
                messagebox.showwarning(
                    "内存警告", 
                    f"系统内存较小({total_memory:.1f}GB)，建议降低内存目标值以避免系统不稳定。"
                )
        except Exception as e:
            print(f"兼容性检查失败: {e}")
    
    def get_disk_path(self):
        """获取适合当前系统的磁盘路径"""
        if self.is_windows:
            return 'C:\\'
        else:
            return '/'
        
    def start_management(self):
        """启动资源管理"""
        if not self.is_running:
            # 验证设置值
            cpu_target = self.cpu_target.get()
            memory_target = self.memory_target.get()
            
            if cpu_target < 1 or cpu_target > 100:
                messagebox.showerror("错误", "CPU目标值必须在1-100%之间")
                return
                
            if memory_target < 1 or memory_target > 100:
                messagebox.showerror("错误", "内存目标值必须在1-100%之间")
                return
            
            self.is_running = True
            self.status_text.set("正在运行")
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            
            # 初始化工作进程列表
            self.cpu_workers = []
            self.memory_workers = []
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
            self.monitor_thread.start()
            
            # 启动管理线程
            self.management_thread = threading.Thread(target=self.manage_resources, daemon=True)
            self.management_thread.start()
            
            messagebox.showinfo("成功", f"资源管理已启动\nCPU目标: {cpu_target}%\n内存目标: {memory_target}%")
            print(f"资源管理启动 - CPU目标: {cpu_target}%, 内存目标: {memory_target}%")
            
    def stop_management(self):
        """停止资源管理"""
        if self.is_running:
            # 确认停止操作
            result = messagebox.askyesno("确认停止", "确定要停止资源管理吗？\n所有工作进程将被终止。")
            if not result:
                return
                
            self.is_running = False
            self.status_text.set("正在停止...")
            self.start_button.configure(state=tk.DISABLED)  # 暂时禁用，防止重复操作
            self.stop_button.configure(state=tk.DISABLED)
            
            # 清理工作进程
            self.cleanup_workers()
            
            # 更新状态显示
            self.status_text.set("已停止")
            self.start_button.configure(state=tk.NORMAL)
            self.cpu_workers_label.configure(text="0")
            self.memory_workers_label.configure(text="0")
            
            messagebox.showinfo("成功", "资源管理已停止，所有工作进程已清理完成")
            print("资源管理已停止")
            
    def monitor_resources(self):
        """监控系统资源"""
        while self.is_running:
            try:
                # 获取当前系统资源使用情况
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                memory_percent = memory_info.percent
                
                # 更新基本显示
                self.current_cpu.set(f"{cpu_percent:.1f}%")
                self.current_memory.set(f"{memory_percent:.1f}%")
                
                # 更新目标显示
                self.cpu_target_display.configure(text=f"{self.cpu_target.get()}%")
                self.memory_target_display.configure(text=f"{self.memory_target.get()}%")
                
                # 更新工作进程数量显示
                self.cpu_workers_label.configure(text=str(len(self.cpu_workers)))
                self.memory_workers_label.configure(text=str(len(self.memory_workers)))
                
                # 更新详细系统信息
                try:
                    # CPU频率
                    cpu_freq = psutil.cpu_freq()
                    if cpu_freq:
                        self.cpu_freq_label.configure(text=f"{cpu_freq.current:.0f} MHz")
                    
                    # 可用内存
                    available_memory = memory_info.available / (1024**3)
                    self.available_memory_label.configure(text=f"{available_memory:.1f} GB")
                    
                    # 磁盘使用情况（平台兼容）
                    disk_path = self.get_disk_path()
                    disk_usage = psutil.disk_usage(disk_path)
                    disk_percent = (disk_usage.used / disk_usage.total) * 100
                    disk_free = disk_usage.free / (1024**3)
                    self.disk_usage_label.configure(text=f"{disk_percent:.1f}%")
                    self.disk_free_label.configure(text=f"{disk_free:.1f} GB")
                    
                    # 网络速率计算
                    current_net_io = psutil.net_io_counters()
                    current_time = time.time()
                    
                    if hasattr(self, 'last_net_io') and hasattr(self, 'last_net_time'):
                        time_delta = current_time - self.last_net_time
                        if time_delta > 0:
                            sent_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
                            recv_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
                            
                            # 格式化网络速度显示
                            def format_bytes(bytes_val):
                                if bytes_val < 1024:
                                    return f"{bytes_val:.0f} B/s"
                                elif bytes_val < 1024**2:
                                    return f"{bytes_val/1024:.1f} KB/s"
                                elif bytes_val < 1024**3:
                                    return f"{bytes_val/(1024**2):.1f} MB/s"
                                else:
                                    return f"{bytes_val/(1024**3):.1f} GB/s"
                            
                            self.net_sent_label.configure(text=format_bytes(sent_speed))
                            self.net_recv_label.configure(text=format_bytes(recv_speed))
                    
                    # 更新网络统计基准
                    self.last_net_io = current_net_io
                    self.last_net_time = current_time
                    
                except Exception as detail_error:
                    print(f"详细信息更新错误: {detail_error}")
                
                # 更新最后更新时间
                current_time_str = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.configure(text=current_time_str)
                
                # 执行资源管理逻辑
                self.manage_cpu_resources(cpu_percent, self.cpu_target.get(), memory_percent, self.memory_target.get())
                self.manage_memory_resources(memory_percent, self.memory_target.get(), cpu_percent, self.cpu_target.get())
                
                time.sleep(2)  # 每2秒检查一次
                
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(5)
                
    def manage_cpu_resources(self, current_cpu, target_cpu, current_memory, target_memory, conflict_status=None):
        """CPU资源动态管理"""
        tolerance = 2.0  # 容忍度
        
        # 检查是否需要调节CPU
        if abs(current_cpu - target_cpu) <= tolerance:
            return  # 在目标范围内，无需调节
            
        # 冲突避免：如果内存已达到峰值，不再提升CPU
        memory_at_peak = abs(current_memory - target_memory) <= tolerance
        
        # 详细冲突检测和日志记录
        conflict_detected = False
        conflict_reason = ""
        
        if current_cpu < target_cpu - tolerance:
            # CPU占用率低于目标，需要提升
            if not memory_at_peak or current_memory < target_memory:
                # 只有在内存未达峰值或内存也需要提升时才提升CPU
                needed_workers = max(1, int((target_cpu - current_cpu) / 10))
                actual_workers = min(needed_workers, 3 - len(self.cpu_workers))
                if actual_workers > 0:
                    for _ in range(actual_workers):
                        self.start_cpu_worker()
                        time.sleep(0.5)
                    print(f"CPU管理: 提升CPU占用率 {current_cpu:.1f}% -> {target_cpu:.1f}%, 启动 {actual_workers} 个工作进程")
            else:
                conflict_detected = True
                conflict_reason = f"内存已达目标({current_memory:.1f}%/{target_memory:.1f}%)，暂停CPU提升以避免冲突"
                    
        elif current_cpu > target_cpu + tolerance:
            # CPU占用率高于目标，需要释放
            workers_to_stop = max(1, int((current_cpu - target_cpu) / 10))
            actual_stops = min(workers_to_stop, len(self.cpu_workers))
            if actual_stops > 0:
                for _ in range(actual_stops):
                    self.stop_cpu_worker()
                    time.sleep(0.5)
                print(f"CPU管理: 降低CPU占用率 {current_cpu:.1f}% -> {target_cpu:.1f}%, 停止 {actual_stops} 个工作进程")
            
        if conflict_detected:
            print(f"CPU冲突检测: {conflict_reason}")
                
    def manage_memory_resources(self, current_memory, target_memory, current_cpu, target_cpu, conflict_status=None):
        """内存资源动态管理"""
        tolerance = 2.0  # 容忍度
        
        # 检查是否需要调节内存
        if abs(current_memory - target_memory) <= tolerance:
            return  # 在目标范围内，无需调节
            
        # 冲突避免：如果CPU已达到峰值，不再提升内存
        cpu_at_peak = abs(current_cpu - target_cpu) <= tolerance
        
        # 详细冲突检测和日志记录
        conflict_detected = False
        conflict_reason = ""
        
        if current_memory < target_memory - tolerance:
            # 内存占用率低于目标，需要提升
            if not cpu_at_peak or current_cpu < target_cpu:
                # 只有在CPU未达峰值或CPU也需要提升时才提升内存
                needed_workers = max(1, int((target_memory - current_memory) / 15))
                actual_workers = min(needed_workers, 2 - len(self.memory_workers))
                if actual_workers > 0:
                    for _ in range(actual_workers):
                        self.start_memory_worker()
                        time.sleep(1)
                    print(f"内存管理: 提升内存占用率 {current_memory:.1f}% -> {target_memory:.1f}%, 启动 {actual_workers} 个工作进程")
            else:
                conflict_detected = True
                conflict_reason = f"CPU已达目标({current_cpu:.1f}%/{target_cpu:.1f}%)，暂停内存提升以避免冲突"
                    
        elif current_memory > target_memory + tolerance:
            # 内存占用率高于目标，需要释放
            workers_to_stop = max(1, int((current_memory - target_memory) / 15))
            actual_stops = min(workers_to_stop, len(self.memory_workers))
            if actual_stops > 0:
                for _ in range(actual_stops):
                    self.stop_memory_worker()
                    time.sleep(1)
                print(f"内存管理: 降低内存占用率 {current_memory:.1f}% -> {target_memory:.1f}%, 停止 {actual_stops} 个工作进程")
            
        if conflict_detected:
            print(f"内存冲突检测: {conflict_reason}")
                
    def start_cpu_worker(self):
        """启动CPU工作进程"""
        try:
            # 创建CPU密集型工作进程
            def cpu_intensive_task():
                """CPU密集型任务"""
                # Windows特定优化
                if self.is_windows:
                    try:
                        import psutil
                        current_process = psutil.Process()
                        current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else 5)
                    except:
                        pass
                
                while True:
                    # 执行计算密集型操作
                    for i in range(10000):
                        _ = i ** 2
                    time.sleep(0.01)  # 短暂休息避免完全占满
            
            worker = multiprocessing.Process(target=cpu_intensive_task)
            worker.start()
            self.cpu_workers.append(worker)
            print(f"启动CPU工作进程，当前进程数: {len(self.cpu_workers)}")
        except Exception as e:
            print(f"启动CPU工作进程失败: {e}")
        
    def stop_cpu_worker(self):
        """停止CPU工作进程"""
        if self.cpu_workers:
            try:
                worker = self.cpu_workers.pop()
                worker.terminate()
                worker.join(timeout=1)
                if worker.is_alive():
                    worker.kill()
                print(f"停止CPU工作进程，当前进程数: {len(self.cpu_workers)}")
            except Exception as e:
                print(f"停止CPU工作进程失败: {e}")
        
    def start_memory_worker(self):
        """启动内存工作进程"""
        try:
            # 创建内存占用工作进程
            def memory_intensive_task():
                """内存密集型任务"""
                # Windows特定优化
                if self.is_windows:
                    try:
                        import psutil
                        current_process = psutil.Process()
                        current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else 5)
                    except:
                        pass
                
                memory_blocks = []
                # Windows系统使用较小的内存块以提高兼容性
                block_size = 30 * 1024 * 1024 if self.is_windows else 50 * 1024 * 1024  # Windows: 30MB, 其他: 50MB
                
                while True:
                    try:
                        # 分配内存块
                        block = bytearray(block_size)
                        memory_blocks.append(block)
                        time.sleep(1)
                        
                        # 限制最大内存使用量
                        max_blocks = 15 if self.is_windows else 20  # Windows系统更保守
                        if len(memory_blocks) > max_blocks:
                            memory_blocks.pop(0)
                    except MemoryError:
                        # 内存不足时释放一些内存
                        if memory_blocks:
                            memory_blocks.pop(0)
                        time.sleep(2)
            
            worker = multiprocessing.Process(target=memory_intensive_task)
            worker.start()
            self.memory_workers.append(worker)
            print(f"启动内存工作进程，当前进程数: {len(self.memory_workers)}")
        except Exception as e:
            print(f"启动内存工作进程失败: {e}")
        
    def stop_memory_worker(self):
        """停止内存工作进程"""
        if self.memory_workers:
            try:
                worker = self.memory_workers.pop()
                worker.terminate()
                worker.join(timeout=1)
                if worker.is_alive():
                    worker.kill()
                print(f"停止内存工作进程，当前进程数: {len(self.memory_workers)}")
            except Exception as e:
                print(f"停止内存工作进程失败: {e}")
        
    def cleanup_workers(self):
        """清理所有工作进程"""
        try:
            # 清理CPU工作进程
            while self.cpu_workers:
                worker = self.cpu_workers.pop()
                try:
                    worker.terminate()
                    worker.join(timeout=2)
                    if worker.is_alive():
                        worker.kill()
                except Exception as e:
                    print(f"清理CPU工作进程失败: {e}")
            
            # 清理内存工作进程
            while self.memory_workers:
                worker = self.memory_workers.pop()
                try:
                    worker.terminate()
                    worker.join(timeout=2)
                    if worker.is_alive():
                        worker.kill()
                except Exception as e:
                    print(f"清理内存工作进程失败: {e}")
                    
            print("所有工作进程已清理完成")
        except Exception as e:
            print(f"清理工作进程时发生错误: {e}")
        
    def save_config(self):
        """保存配置"""
        config = {
            'cpu_target': self.cpu_target.get(),
            'memory_target': self.memory_target.get(),
            'schedules': self.schedules
        }
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.cpu_target.set(config.get('cpu_target', 50.0))
                self.memory_target.set(config.get('memory_target', 50.0))
                self.schedules = config.get('schedules', [])
                
                # 更新界面显示
                self.cpu_value_label.configure(text=f"{self.cpu_target.get()}%")
                self.memory_value_label.configure(text=f"{self.memory_target.get()}%")
                
                messagebox.showinfo("成功", "配置已加载")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            
    def reset_settings(self):
        """重置设置到默认值"""
        result = messagebox.askyesno("确认重置", "确定要重置所有设置到默认值吗？")
        if result:
            self.cpu_target.set(50.0)
            self.memory_target.set(50.0)
            self.schedules = []
            
            # 更新界面显示
            self.cpu_value_label.configure(text=f"{self.cpu_target.get()}%")
            self.memory_value_label.configure(text=f"{self.memory_target.get()}%")
            self.cpu_entry.delete(0, tk.END)
            self.cpu_entry.insert(0, "50.0")
            self.memory_entry.delete(0, tk.END)
            self.memory_entry.insert(0, "50.0")
            
            messagebox.showinfo("成功", "设置已重置到默认值")
            
    def validate_cpu_setting(self, value):
        """验证CPU设置值"""
        if value < 10:
            self.cpu_hint_label.configure(text="警告: CPU占用率过低可能影响性能", foreground='#FF9800')
        elif value > 90:
            self.cpu_hint_label.configure(text="警告: CPU占用率过高可能导致系统卡顿", foreground='#F44336')
        else:
            self.cpu_hint_label.configure(text="建议范围: 10-90%", foreground='#666666')
            
    def validate_memory_setting(self, value):
        """验证内存设置值"""
        if value < 10:
            self.memory_hint_label.configure(text="警告: 内存占用率过低可能影响性能", foreground='#FF9800')
        elif value > 85:
            self.memory_hint_label.configure(text="警告: 内存占用率过高可能导致系统不稳定", foreground='#F44336')
        else:
            self.memory_hint_label.configure(text="建议范围: 10-85%", foreground='#666666')
            
    def apply_cpu_value(self):
        """应用CPU精确设置值"""
        try:
            value = float(self.cpu_entry.get())
            if 1 <= value <= 100:
                self.cpu_target.set(value)
                self.cpu_value_label.configure(text=f"{value}%")
                self.validate_cpu_setting(value)
                messagebox.showinfo("成功", f"CPU目标占用率已设置为 {value}%")
            else:
                messagebox.showerror("错误", "请输入1-100之间的数值")
                self.cpu_entry.delete(0, tk.END)
                self.cpu_entry.insert(0, str(self.cpu_target.get()))
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            self.cpu_entry.delete(0, tk.END)
            self.cpu_entry.insert(0, str(self.cpu_target.get()))
            
    def apply_memory_value(self):
        """应用内存精确设置值"""
        try:
            value = float(self.memory_entry.get())
            if 1 <= value <= 100:
                self.memory_target.set(value)
                self.memory_value_label.configure(text=f"{value}%")
                self.validate_memory_setting(value)
                messagebox.showinfo("成功", f"内存目标占用率已设置为 {value}%")
            else:
                messagebox.showerror("错误", "请输入1-100之间的数值")
                self.memory_entry.delete(0, tk.END)
                self.memory_entry.insert(0, str(self.memory_target.get()))
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            self.memory_entry.delete(0, tk.END)
            self.memory_entry.insert(0, str(self.memory_target.get()))
            
    def toggle_schedule(self):
        """切换定时计划功能"""
        if self.schedule_enabled.get():
            # 启动定时计划
            self.schedule_thread = threading.Thread(target=self.run_schedule, daemon=True)
            self.schedule_thread.start()
            messagebox.showinfo("成功", "定时计划已启用")
        else:
            # 停止定时计划
            messagebox.showinfo("成功", "定时计划已禁用")
    
    def add_schedule(self):
        """添加定时计划"""
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            action = self.action_var.get()
            
            # 验证时间格式
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                messagebox.showerror("错误", "请输入有效的时间格式")
                return
            
            time_str = f"{hour:02d}:{minute:02d}"
            
            # 检查是否已存在相同时间的计划
            for schedule in self.schedules:
                if schedule['time'] == time_str:
                    messagebox.showerror("错误", "该时间已存在计划")
                    return
            
            # 添加计划
            schedule_item = {
                'time': time_str,
                'action': action,
                'status': '等待中'
            }
            
            self.schedules.append(schedule_item)
            self.update_schedule_tree()
            
            messagebox.showinfo("成功", f"已添加计划: {time_str} {action}")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的时间")
    
    def remove_schedule(self):
        """删除选中的计划"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的计划")
            return
        
        # 获取选中项的索引
        item = selection[0]
        index = self.schedule_tree.index(item)
        
        # 删除计划
        removed_schedule = self.schedules.pop(index)
        self.update_schedule_tree()
        
        messagebox.showinfo("成功", f"已删除计划: {removed_schedule['time']} {removed_schedule['action']}")
    
    def clear_schedules(self):
        """清空所有计划"""
        if not self.schedules:
            messagebox.showinfo("提示", "没有计划需要清空")
            return
        
        result = messagebox.askyesno("确认清空", "确定要清空所有计划吗？")
        if result:
            self.schedules.clear()
            self.update_schedule_tree()
            messagebox.showinfo("成功", "已清空所有计划")
    
    def update_schedule_tree(self):
        """更新计划列表显示"""
        # 清空现有项目
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 添加计划项目
        for schedule in self.schedules:
            self.schedule_tree.insert('', 'end', values=(
                schedule['time'],
                schedule['action'],
                schedule['status']
            ))
    
    def run_schedule(self):
        """运行定时计划检查"""
        while self.schedule_enabled.get():
            try:
                current_time = datetime.now().strftime("%H:%M")
                
                for i, schedule in enumerate(self.schedules):
                    if schedule['time'] == current_time and schedule['status'] == '等待中':
                        # 执行计划
                        if schedule['action'] == '启动':
                            if not self.is_running:
                                self.start_management()
                                schedule['status'] = '已执行'
                                print(f"定时计划执行: {current_time} 启动资源管理")
                        elif schedule['action'] == '停止':
                            if self.is_running:
                                self.stop_management()
                                schedule['status'] = '已执行'
                                print(f"定时计划执行: {current_time} 停止资源管理")
                        
                        # 更新显示
                        self.update_schedule_tree()
                
                # 每分钟检查一次，在新的一分钟重置状态
                if datetime.now().second == 0:
                    for schedule in self.schedules:
                        if schedule['status'] == '已执行':
                            # 检查是否是新的一天，重置状态
                            schedule['status'] = '等待中'
                    self.update_schedule_tree()
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                print(f"定时计划错误: {e}")
                time.sleep(60)
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
            
    def on_closing(self):
        """程序关闭时的清理工作"""
        if self.is_running:
            self.stop_management()
        self.root.destroy()

def main():
    """主函数"""
    app = ResourceManager()
    app.run()

if __name__ == "__main__":
    main()