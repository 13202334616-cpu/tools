#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存压力测试工具 - 独立版本
专门用于内存动态管理和压力测试
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
import gc
import random

class MemoryStressTestGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window_basic()
        
        # 初始化变量
        self.is_running = False
        self.memory_manager_running = False
        self.memory_blocks = []
        
        # 异步初始化
        self.root.after(100, self.async_initialize)
    
    def setup_window_basic(self):
        """设置窗口基本属性"""
        self.root.title("内存压力测试工具")
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
            self.add_log("🚀 内存压力测试工具启动成功")
            self.add_log(f"💻 系统信息: {platform.system()} {platform.release()}")
            memory = psutil.virtual_memory()
            self.add_log(f"🧠 内存信息: {memory.total / (1024**3):.1f}GB 总计, 当前使用率 {memory.percent:.1f}%")
        except Exception as e:
            self.show_error_and_exit(f"最终初始化失败: {str(e)}")
    
    def show_error_and_exit(self, error_msg):
        """显示错误并退出"""
        messagebox.showerror("启动失败", f"程序启动失败:\n{error_msg}")
        self.root.quit()
        sys.exit(1)
    
    def setup_variables(self):
        """设置变量"""
        # 内存相关变量
        self.memory_target = tk.DoubleVar(value=60.0)  # 内存目标使用率
        self.memory_max = tk.DoubleVar(value=80.0)     # 内存峰值限制
        self.memory_block_size = tk.IntVar(value=10)   # 内存块大小(MB)
        
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
        
        # 内存控制区域
        memory_frame = ttk.LabelFrame(main_frame, text="内存压力测试", padding="10")
        memory_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        memory_frame.columnconfigure(1, weight=1)
        
        # 内存目标使用率
        ttk.Label(memory_frame, text="目标内存使用率:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        memory_target_scale = ttk.Scale(memory_frame, from_=20, to=90, variable=self.memory_target, orient=tk.HORIZONTAL)
        memory_target_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Label(memory_frame, textvariable=self.memory_target).grid(row=0, column=2, sticky=tk.W)
        
        # 内存峰值限制
        ttk.Label(memory_frame, text="内存峰值限制:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        memory_max_scale = ttk.Scale(memory_frame, from_=30, to=95, variable=self.memory_max, orient=tk.HORIZONTAL)
        memory_max_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        ttk.Label(memory_frame, textvariable=self.memory_max).grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        # 内存块大小
        ttk.Label(memory_frame, text="内存块大小(MB):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        block_size_spinbox = ttk.Spinbox(memory_frame, from_=1, to=100, textvariable=self.memory_block_size, width=10)
        block_size_spinbox.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="🚀 开始压力测试", command=self.start_stress_test)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="🛑 停止测试", command=self.stop_stress_test, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="📊 系统信息", command=self.show_system_info).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🧹 释放内存", command=self.force_gc).pack(side=tk.LEFT)
        
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
                logging.FileHandler('memory_stress_test.log', encoding='utf-8'),
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
        
        self.add_log("🚀 开始内存压力测试")
        
        # 启动内存压力测试
        self.start_memory_stress()
    
    def stop_stress_test(self):
        """停止压力测试"""
        if not self.is_running:
            return
        
        self.add_log("🛑 正在停止压力测试...")
        
        self.is_running = False
        self.memory_manager_running = False
        
        # 清理内存
        self.cleanup_memory_stress()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        
        self.add_log("✅ 压力测试已停止")
    
    def start_memory_stress(self):
        """启动内存压力测试"""
        self.memory_manager_running = True
        
        # 启动内存管理器线程
        memory_manager_thread = threading.Thread(target=self.memory_manager, daemon=True)
        memory_manager_thread.start()
    
    def memory_manager(self):
        """内存动态管理器"""
        initial_max = self.memory_max.get()
        initial_target = self.memory_target.get()
        
        self.add_log(f"🔄 内存管理器启动: 峰值限制{initial_max:.0f}%, 目标值{initial_target:.0f}%")
        self.add_log(f"📋 规则: 系统内存低于目标时分配内存，高于峰值时释放内存")
        
        last_max = initial_max
        last_target = initial_target
        last_log_time = time.time()
        
        while self.memory_manager_running and self.is_running:
            try:
                # 动态获取当前峰值和目标值
                max_percent = self.memory_max.get()
                target_percent = self.memory_target.get()
                
                # 如果设置发生变化，记录日志
                if abs(max_percent - last_max) > 0.5 or abs(target_percent - last_target) > 0.5:
                    self.add_log(f"🎯 设置已更新: 峰值{last_max:.0f}%→{max_percent:.0f}%, 目标{last_target:.0f}%→{target_percent:.0f}%")
                    last_max = max_percent
                    last_target = target_percent
                
                # 获取当前内存使用率
                memory = psutil.virtual_memory()
                current_memory = memory.percent
                
                # 计算目标值（设为峰值的90%）
                target_value = max_percent * 0.9
                
                # 检查内存使用率并主动调整
                if current_memory > max_percent:
                    excess = current_memory - max_percent
                    self.add_log(f"🚨 系统内存{current_memory:.1f}%超过峰值限制{max_percent:.0f}%（超出{excess:.1f}%），强制释放内存")
                    
                    # 根据超出程度决定释放量
                    if excess > 10:
                        self.remove_memory_blocks(count=5)
                    elif excess > 5:
                        self.remove_memory_blocks(count=3)
                    else:
                        self.remove_memory_blocks(count=1)
                
                elif current_memory > max_percent - 5:
                    # 接近峰值，紧急保护
                    self.add_log(f"⚠️ 系统内存{current_memory:.1f}%接近峰值{max_percent:.0f}%，预防性释放")
                    self.remove_memory_blocks(count=1)
                
                elif current_memory < target_value:
                    # 低于目标值，增加内存使用
                    shortage = target_value - current_memory
                    self.add_log(f"📈 系统内存{current_memory:.1f}%低于目标{target_value:.1f}%（差距{shortage:.1f}%），分配内存")
                    
                    # 根据差距决定分配量
                    if shortage > 10:
                        self.add_memory_blocks(count=3)
                    elif shortage > 5:
                        self.add_memory_blocks(count=2)
                    else:
                        self.add_memory_blocks(count=1)
                
                elif current_memory > target_value + 2:
                    # 超过目标值较多，微调
                    self.add_log(f"📉 系统内存{current_memory:.1f}%超过目标{target_value:.1f}%，微调释放")
                    self.fine_tune_memory_load(increase=False)
                
                elif current_memory < target_value - 2:
                    # 低于目标值较多，微调
                    self.add_log(f"📈 系统内存{current_memory:.1f}%低于目标{target_value:.1f}%，微调分配")
                    self.fine_tune_memory_load(increase=True)
                
                # 定期记录状态（每30秒）
                current_time = time.time()
                if current_time - last_log_time >= 30:
                    allocated_mb = len(self.memory_blocks) * self.memory_block_size.get()
                    self.add_log(f"📊 当前状态: 系统内存{current_memory:.1f}% (目标{target_value:.1f}%, 峰值{max_percent:.0f}%), 已分配{allocated_mb}MB ({len(self.memory_blocks)}个块)")
                    last_log_time = current_time
                
                time.sleep(1)
                
            except Exception as e:
                self.add_log(f"❌ 内存管理错误: {str(e)}")
                time.sleep(2)
    
    def add_memory_blocks(self, count=1):
        """分配内存块（批量处理以减少CPU影响）"""
        try:
            block_size_mb = self.memory_block_size.get()
            block_size_bytes = block_size_mb * 1024 * 1024
            
            # 批量分配，每批10MB，批次间延迟50ms
            batch_size = max(1, 10 // block_size_mb)  # 每批大约10MB
            batches = (count + batch_size - 1) // batch_size  # 向上取整
            
            for batch in range(batches):
                if not self.memory_manager_running or not self.is_running:
                    break
                
                # 计算当前批次的块数
                current_batch_count = min(batch_size, count - batch * batch_size)
                
                for i in range(current_batch_count):
                    # 创建内存块（随机数据以防止压缩）
                    memory_block = bytearray(random.getrandbits(8) for _ in range(block_size_bytes))
                    self.memory_blocks.append(memory_block)
                
                # 批次间延迟
                if batch < batches - 1:
                    time.sleep(0.05)
            
            allocated_mb = len(self.memory_blocks) * block_size_mb
            self.add_log(f"➕ 分配了{count}个内存块({count * block_size_mb}MB)，总计{allocated_mb}MB")
            
        except Exception as e:
            self.add_log(f"❌ 分配内存失败: {str(e)}")
    
    def remove_memory_blocks(self, count=1):
        """释放内存块（批量处理以减少CPU影响）"""
        try:
            if not self.memory_blocks:
                return
            
            block_size_mb = self.memory_block_size.get()
            
            # 计算实际要释放的块数
            actual_count = min(count, len(self.memory_blocks))
            
            # 为了更激进的释放，可能会释放更多
            if len(self.memory_blocks) > actual_count * 2:
                actual_count = min(actual_count + 1, len(self.memory_blocks))
            
            # 批量释放，每批20MB，批次间延迟30ms
            batch_size = max(1, 20 // block_size_mb)  # 每批大约20MB
            batches = (actual_count + batch_size - 1) // batch_size  # 向上取整
            
            for batch in range(batches):
                if not self.memory_blocks:
                    break
                
                # 计算当前批次的块数
                current_batch_count = min(batch_size, actual_count - batch * batch_size, len(self.memory_blocks))
                
                for i in range(current_batch_count):
                    if self.memory_blocks:
                        self.memory_blocks.pop()
                
                # 批次间延迟
                if batch < batches - 1 and self.memory_blocks:
                    time.sleep(0.03)
            
            # 强制垃圾回收
            gc.collect()
            
            remaining_mb = len(self.memory_blocks) * block_size_mb
            released_mb = actual_count * block_size_mb
            self.add_log(f"➖ 释放了{actual_count}个内存块({released_mb}MB)，剩余{remaining_mb}MB")
            
        except Exception as e:
            self.add_log(f"❌ 释放内存失败: {str(e)}")
    
    def fine_tune_memory_load(self, increase=True):
        """微调内存负载"""
        try:
            if increase:
                if len(self.memory_blocks) < 1000:  # 防止过度分配
                    self.add_memory_blocks(count=1)
            else:
                if self.memory_blocks:
                    self.remove_memory_blocks(count=1)
                    
        except Exception as e:
            self.add_log(f"❌ 微调内存负载失败: {str(e)}")
    
    def cleanup_memory_stress(self):
        """清理内存压力测试"""
        try:
            # 释放所有内存块
            block_count = len(self.memory_blocks)
            if block_count > 0:
                block_size_mb = self.memory_block_size.get()
                total_mb = block_count * block_size_mb
                
                self.memory_blocks.clear()
                gc.collect()  # 强制垃圾回收
                
                self.add_log(f"🧹 释放了所有内存块: {block_count}个块，{total_mb}MB")
            
            self.add_log("🧹 内存压力测试清理完成")
            
        except Exception as e:
            self.add_log(f"❌ 清理内存压力测试失败: {str(e)}")
    
    def force_gc(self):
        """强制垃圾回收"""
        try:
            before_memory = psutil.virtual_memory().percent
            gc.collect()
            after_memory = psutil.virtual_memory().percent
            
            self.add_log(f"🧹 强制垃圾回收: {before_memory:.1f}% → {after_memory:.1f}%")
            
        except Exception as e:
            self.add_log(f"❌ 强制垃圾回收失败: {str(e)}")
    
    def show_system_info(self):
        """显示系统信息"""
        try:
            memory = psutil.virtual_memory()
            memory_info = f"内存: {memory.total / (1024**3):.1f}GB 总计\n"
            memory_info += f"当前内存使用率: {memory.percent:.1f}%\n"
            memory_info += f"可用内存: {memory.available / (1024**3):.1f}GB\n"
            
            cpu_info = f"CPU: {psutil.cpu_count(logical=False)}物理核心, {psutil.cpu_count()}逻辑核心\n"
            cpu_info += f"当前CPU使用率: {psutil.cpu_percent(interval=1):.1f}%\n"
            
            system_info = f"系统: {platform.system()} {platform.release()}\n"
            system_info += f"Python版本: {platform.python_version()}\n"
            
            # 当前分配的内存信息
            if self.memory_blocks:
                allocated_mb = len(self.memory_blocks) * self.memory_block_size.get()
                allocation_info = f"\n当前分配: {len(self.memory_blocks)}个内存块, {allocated_mb}MB\n"
            else:
                allocation_info = "\n当前分配: 无\n"
            
            info_text = memory_info + cpu_info + system_info + allocation_info
            
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
        root = tk.Tk()
        app = MemoryStressTestGUI(root)
        
        # 绑定窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()