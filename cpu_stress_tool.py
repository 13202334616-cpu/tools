#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU压力测试工具 - 独立版本
专门用于CPU动态管理和压力测试
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

def cpu_intensive_process(control_signal, initial_intensity):
    """CPU密集型进程（多进程版本）"""
    try:
        intensity = initial_intensity
        while True:
            # 检查控制信号
            if not control_signal.empty():
                try:
                    signal = control_signal.get_nowait()
                    if signal == 'stop':
                        break
                    elif isinstance(signal, (int, float)):
                        intensity = max(0.1, min(1.0, signal))
                except:
                    pass
            
            # CPU密集型计算
            start_time = time.time()
            while time.time() - start_time < intensity * 0.01:  # 工作时间
                # 执行一些CPU密集型操作
                for i in range(1000):
                    _ = i ** 2
            
            # 休息时间
            if intensity < 1.0:
                time.sleep((1.0 - intensity) * 0.01)
                
    except Exception as e:
        print(f"CPU进程错误: {e}")

class CPUStressTestGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window_basic()
        
        # 初始化变量
        self.is_running = False
        self.cpu_manager_running = False
        self.cpu_processes = []
        self.cpu_threads = []
        self.cpu_load_intensity = 0.5
        
        # 异步初始化
        self.root.after(100, self.async_initialize)
    
    def setup_window_basic(self):
        """设置窗口基本属性"""
        self.root.title("CPU压力测试工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap(default="icon.ico")
        except:
            pass
    
    def async_initialize(self):
        """异步初始化第一步"""
        try:
            self.setup_variables()
            self.root.after(50, self.async_initialize_step2)
        except Exception as e:
            self.show_error_and_exit(f"初始化变量失败: {str(e)}")
    
    def async_initialize_step2(self):
        """异步初始化第二步"""
        try:
            self.create_widgets()
            self.root.after(50, self.async_initialize_step3)
        except Exception as e:
            self.show_error_and_exit(f"创建界面失败: {str(e)}")
    
    def async_initialize_step3(self):
        """异步初始化第三步"""
        try:
            self.setup_logging()
            self.root.after(50, self.async_initialize_final)
        except Exception as e:
            self.show_error_and_exit(f"设置日志失败: {str(e)}")
    
    def async_initialize_final(self):
        """异步初始化最后一步"""
        try:
            self.add_log("🚀 CPU压力测试工具启动成功")
            self.add_log(f"💻 系统信息: {platform.system()} {platform.release()}")
            self.add_log(f"🔧 CPU核心数: {psutil.cpu_count(logical=False)}物理核心, {psutil.cpu_count()}逻辑核心")
        except Exception as e:
            self.show_error_and_exit(f"最终初始化失败: {str(e)}")
    
    def show_error_and_exit(self, error_msg):
        """显示错误并退出"""
        messagebox.showerror("启动失败", f"程序启动失败:\n{error_msg}")
        self.root.quit()
        sys.exit(1)
    
    def setup_variables(self):
        """设置变量"""
        # CPU相关变量
        self.cpu_target = tk.DoubleVar(value=30.0)  # CPU目标使用率
        self.cpu_max = tk.DoubleVar(value=50.0)     # CPU峰值限制
        self.cpu_threads_count = tk.IntVar(value=4)  # CPU线程数
        
        # 状态变量
        self.status_var = tk.StringVar(value="就绪")
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # CPU控制区域
        cpu_frame = ttk.LabelFrame(main_frame, text="CPU压力测试", padding="10")
        cpu_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        cpu_frame.columnconfigure(1, weight=1)
        
        # CPU目标使用率
        ttk.Label(cpu_frame, text="目标CPU使用率:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        cpu_target_scale = ttk.Scale(cpu_frame, from_=10, to=90, variable=self.cpu_target, orient=tk.HORIZONTAL)
        cpu_target_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Label(cpu_frame, textvariable=self.cpu_target).grid(row=0, column=2, sticky=tk.W)
        
        # CPU峰值限制
        ttk.Label(cpu_frame, text="CPU峰值限制:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        cpu_max_scale = ttk.Scale(cpu_frame, from_=20, to=100, variable=self.cpu_max, orient=tk.HORIZONTAL)
        cpu_max_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        ttk.Label(cpu_frame, textvariable=self.cpu_max).grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        # CPU线程数
        ttk.Label(cpu_frame, text="线程数:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        threads_spinbox = ttk.Spinbox(cpu_frame, from_=1, to=32, textvariable=self.cpu_threads_count, width=10)
        threads_spinbox.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="🚀 开始压力测试", command=self.start_stress_test)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="🛑 停止测试", command=self.stop_stress_test, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="📊 系统信息", command=self.show_system_info).pack(side=tk.LEFT)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志控制按钮
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(log_button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_button_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT)
    
    def setup_logging(self):
        """设置日志"""
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cpu_stress_test.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 添加到GUI
        self.log_text.insert(tk.END, log_message + "\n")
        self.log_text.see(tk.END)
        
        # 添加到日志文件
        self.logger.info(message)
    
    def start_stress_test(self):
        """开始压力测试"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("运行中")
        
        self.add_log("🚀 开始CPU压力测试")
        
        # 启动CPU压力测试
        self.start_cpu_stress()
    
    def stop_stress_test(self):
        """停止压力测试"""
        if not self.is_running:
            return
        
        self.add_log("🛑 正在停止压力测试...")
        
        self.is_running = False
        self.cpu_manager_running = False
        
        # 停止CPU进程和线程
        self.cleanup_cpu_stress()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        
        self.add_log("✅ 压力测试已停止")
    
    def start_cpu_stress(self):
        """启动CPU压力测试"""
        self.cpu_manager_running = True
        
        # 启动CPU管理器线程
        cpu_manager_thread = threading.Thread(target=self.cpu_manager, daemon=True)
        cpu_manager_thread.start()
    
    def cpu_manager(self):
        """CPU动态管理器"""
        initial_max = self.cpu_max.get()
        initial_target = self.cpu_target.get()
        
        self.add_log(f"🔄 CPU管理器启动: 峰值限制{initial_max:.0f}%, 目标值{initial_target:.0f}%")
        self.add_log(f"📋 规则: 系统CPU低于目标时增加负载，高于峰值时强制减少负载")
        self.add_log(f"💡 使用多进程突破GIL限制，提升CPU利用率")
        
        # 初始启动CPU进程和线程
        initial_processes = max(2, min(4, psutil.cpu_count()))
        self.start_cpu_processes(initial_processes)
        
        initial_threads = max(1, psutil.cpu_count() // 2)
        self.start_cpu_threads(initial_threads)
        
        last_max = initial_max
        last_target = initial_target
        
        while self.cpu_manager_running and self.is_running:
            try:
                # 动态获取当前峰值和目标值
                max_percent = self.cpu_max.get()
                target_percent = self.cpu_target.get()
                
                # 如果设置发生变化，记录日志
                if abs(max_percent - last_max) > 0.5 or abs(target_percent - last_target) > 0.5:
                    self.add_log(f"🎯 设置已更新: 峰值{last_max:.0f}%→{max_percent:.0f}%, 目标{last_target:.0f}%→{target_percent:.0f}%")
                    last_max = max_percent
                    last_target = target_percent
                
                # 获取当前CPU使用率
                current_cpu = psutil.cpu_percent(interval=0.1)
                
                # 检查CPU使用率并主动调整
                if current_cpu > max_percent:
                    excess = current_cpu - max_percent
                    self.add_log(f"🚨 系统CPU{current_cpu:.1f}%超过峰值限制{max_percent:.0f}%（超出{excess:.1f}%），强制减少负载")
                    
                    reduce_times = 1
                    if excess > 10:
                        reduce_times = 3
                    elif excess > 5:
                        reduce_times = 2
                    
                    for i in range(reduce_times):
                        self.reduce_cpu_load()
                        if i < reduce_times - 1:
                            time.sleep(0.2)
                
                elif current_cpu < target_percent - 3:
                    self.add_log(f"📈 系统CPU{current_cpu:.1f}%低于目标{target_percent:.0f}%，增加负载")
                    self.increase_cpu_load()
                
                elif current_cpu < target_percent - 1:
                    self.add_log(f"📈 系统CPU{current_cpu:.1f}%接近目标{target_percent:.0f}%，小幅增加负载")
                    self.fine_tune_cpu_load(increase=True)
                
                elif current_cpu > max_percent - 1:
                    self.add_log(f"📉 系统CPU{current_cpu:.1f}%接近峰值{max_percent:.0f}%，小幅减少负载")
                    self.fine_tune_cpu_load(increase=False)
                
                # 定期记录状态
                total_workers = len(self.cpu_threads) + len(self.cpu_processes)
                if total_workers > 0:
                    self.add_log(f"📊 当前状态: 系统CPU{current_cpu:.1f}% (目标{target_percent:.0f}%, 峰值{max_percent:.0f}%), 进程{len(self.cpu_processes)}个, 线程{len(self.cpu_threads)}个, 负载强度{self.cpu_load_intensity:.2f}")
                
                time.sleep(0.5)
                
            except Exception as e:
                self.add_log(f"❌ CPU管理错误: {str(e)}")
                time.sleep(1)
    
    def start_cpu_processes(self, process_count):
        """启动CPU进程"""
        try:
            for i in range(process_count):
                if not self.cpu_manager_running or not self.is_running:
                    break
                
                control_queue = Queue()
                process = Process(target=cpu_intensive_process, args=(control_queue, self.cpu_load_intensity))
                process.daemon = True
                process.start()
                
                # 存储进程和控制队列
                self.cpu_processes.append({
                    'process': process,
                    'control_queue': control_queue
                })
            
            self.add_log(f"🚀 启动了{process_count}个CPU进程")
            
        except Exception as e:
            self.add_log(f"❌ 启动CPU进程失败: {str(e)}")
    
    def start_cpu_threads(self, thread_count):
        """启动CPU线程"""
        try:
            for i in range(thread_count):
                if not self.cpu_manager_running or not self.is_running:
                    break
                
                thread = threading.Thread(target=self.cpu_intensive_task_dynamic, daemon=True)
                thread.start()
                self.cpu_threads.append(thread)
            
            self.add_log(f"🚀 启动了{thread_count}个CPU线程")
            
        except Exception as e:
            self.add_log(f"❌ 启动CPU线程失败: {str(e)}")
    
    def cpu_intensive_task_dynamic(self):
        """CPU密集型任务（动态强度）"""
        try:
            while self.cpu_manager_running and self.is_running:
                # 根据当前强度执行CPU密集型操作
                start_time = time.time()
                work_duration = self.cpu_load_intensity * 0.01  # 工作时间
                
                while time.time() - start_time < work_duration:
                    # CPU密集型计算
                    for i in range(1000):
                        _ = i ** 2
                
                # 休息时间
                if self.cpu_load_intensity < 1.0:
                    time.sleep((1.0 - self.cpu_load_intensity) * 0.01)
                    
        except Exception as e:
            self.add_log(f"❌ CPU线程错误: {str(e)}")
    
    def increase_cpu_load(self):
        """增加CPU负载"""
        try:
            # 增加负载强度
            self.cpu_load_intensity = min(1.0, self.cpu_load_intensity + 0.1)
            
            # 更新所有进程的强度
            for cpu_proc in self.cpu_processes:
                try:
                    cpu_proc['control_queue'].put(self.cpu_load_intensity)
                except:
                    pass
            
            # 如果强度已经很高，考虑增加更多工作线程
            if self.cpu_load_intensity >= 0.8 and len(self.cpu_threads) < psutil.cpu_count():
                self.start_cpu_threads(1)
            
            # 如果线程数量不够，考虑增加进程
            if len(self.cpu_processes) < psutil.cpu_count() // 2:
                self.start_cpu_processes(1)
                
        except Exception as e:
            self.add_log(f"❌ 增加CPU负载失败: {str(e)}")
    
    def reduce_cpu_load(self):
        """减少CPU负载"""
        try:
            # 首先尝试减少负载强度
            if self.cpu_load_intensity > 0.2:
                self.cpu_load_intensity = max(0.1, self.cpu_load_intensity - 0.1)
                
                # 更新所有进程的强度
                for cpu_proc in self.cpu_processes:
                    try:
                        cpu_proc['control_queue'].put(self.cpu_load_intensity)
                    except:
                        pass
            
            # 如果强度已经很低，考虑停止一些进程
            elif len(self.cpu_processes) > 1:
                try:
                    cpu_proc = self.cpu_processes.pop()
                    cpu_proc['control_queue'].put('stop')
                    if hasattr(cpu_proc['process'], 'terminate'):
                        cpu_proc['process'].terminate()
                    self.add_log(f"🛑 停止CPU进程，剩余{len(self.cpu_processes)}个")
                except:
                    pass
            
            # 最后考虑停止线程（线程较难强制停止，主要通过标志位控制）
            elif len(self.cpu_threads) > 1:
                # 线程会通过cpu_manager_running标志自然结束
                self.add_log(f"📉 减少CPU线程活动")
                
        except Exception as e:
            self.add_log(f"❌ 减少CPU负载失败: {str(e)}")
    
    def fine_tune_cpu_load(self, increase=True):
        """微调CPU负载"""
        try:
            if increase:
                self.cpu_load_intensity = min(1.0, self.cpu_load_intensity + 0.05)
            else:
                self.cpu_load_intensity = max(0.1, self.cpu_load_intensity - 0.05)
            
            # 更新所有进程的强度
            for cpu_proc in self.cpu_processes:
                try:
                    cpu_proc['control_queue'].put(self.cpu_load_intensity)
                except:
                    pass
                    
        except Exception as e:
            self.add_log(f"❌ 微调CPU负载失败: {str(e)}")
    
    def cleanup_cpu_stress(self):
        """清理CPU压力测试"""
        try:
            # 停止所有CPU进程
            for cpu_proc in self.cpu_processes:
                try:
                    cpu_proc['control_queue'].put('stop')
                    if hasattr(cpu_proc['process'], 'terminate'):
                        cpu_proc['process'].terminate()
                        cpu_proc['process'].join(timeout=1)
                except:
                    pass
            
            self.cpu_processes.clear()
            
            # CPU线程会通过标志位自然结束
            self.cpu_threads.clear()
            
            self.add_log("🧹 CPU压力测试清理完成")
            
        except Exception as e:
            self.add_log(f"❌ 清理CPU压力测试失败: {str(e)}")
    
    def show_system_info(self):
        """显示系统信息"""
        try:
            cpu_info = f"CPU: {psutil.cpu_count(logical=False)}物理核心, {psutil.cpu_count()}逻辑核心\n"
            cpu_info += f"当前CPU使用率: {psutil.cpu_percent(interval=1):.1f}%\n"
            
            memory = psutil.virtual_memory()
            memory_info = f"内存: {memory.total / (1024**3):.1f}GB 总计\n"
            memory_info += f"当前内存使用率: {memory.percent:.1f}%\n"
            
            system_info = f"系统: {platform.system()} {platform.release()}\n"
            system_info += f"Python版本: {platform.python_version()}\n"
            
            info_text = cpu_info + memory_info + system_info
            
            messagebox.showinfo("系统信息", info_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取系统信息失败: {str(e)}")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("📝 日志已清空")
    
    def save_log(self):
        """保存日志"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.add_log(f"💾 日志已保存到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存日志失败: {str(e)}")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            if messagebox.askokcancel("退出", "压力测试正在运行，确定要退出吗？"):
                self.stop_stress_test()
                time.sleep(0.5)  # 等待清理完成
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    try:
        # 设置多进程启动方法
        if platform.system() == "Windows":
            multiprocessing.set_start_method('spawn', force=True)
        
        root = tk.Tk()
        app = CPUStressTestGUI(root)
        
        # 绑定窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()