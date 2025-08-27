#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压力测试工具启动器
可以选择启动CPU压力测试工具、内存压力测试工具，或者同时启动两个工具
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import platform
import threading
import time

class ToolLauncher:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        
        # 存储子进程
        self.cpu_process = None
        self.memory_process = None
    
    def setup_window(self):
        """设置窗口"""
        self.root.title("压力测试工具启动器")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # 居中显示
        self.root.eval('tk::PlaceWindow . center')
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="压力测试工具启动器", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 说明文字
        desc_label = ttk.Label(main_frame, text="选择要启动的压力测试工具：", font=('Arial', 10))
        desc_label.pack(pady=(0, 15))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # CPU压力测试按钮
        self.cpu_button = ttk.Button(
            button_frame, 
            text="🖥️ CPU压力测试工具", 
            command=self.launch_cpu_tool,
            width=25
        )
        self.cpu_button.pack(pady=5)
        
        # 内存压力测试按钮
        self.memory_button = ttk.Button(
            button_frame, 
            text="🧠 内存压力测试工具", 
            command=self.launch_memory_tool,
            width=25
        )
        self.memory_button.pack(pady=5)
        
        # 同时启动按钮
        self.both_button = ttk.Button(
            button_frame, 
            text="🚀 同时启动两个工具", 
            command=self.launch_both_tools,
            width=25
        )
        self.both_button.pack(pady=5)
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)
        
        # 状态框架
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(pady=5)
        
        # 状态标签
        ttk.Label(status_frame, text="运行状态:", font=('Arial', 10, 'bold')).pack()
        
        self.status_text = tk.Text(status_frame, height=6, width=45, wrap=tk.WORD)
        self.status_text.pack(pady=5)
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        # 停止所有按钮
        self.stop_button = ttk.Button(
            control_frame, 
            text="🛑 停止所有工具", 
            command=self.stop_all_tools,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 退出按钮
        ttk.Button(
            control_frame, 
            text="❌ 退出", 
            command=self.on_closing
        ).pack(side=tk.LEFT, padx=5)
        
        # 初始状态
        self.update_status("就绪")
    
    def update_status(self, message):
        """更新状态显示"""
        timestamp = time.strftime("%H:%M:%S")
        status_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, status_message)
        self.status_text.see(tk.END)
    
    def launch_cpu_tool(self):
        """启动CPU压力测试工具"""
        try:
            if self.cpu_process and self.cpu_process.poll() is None:
                messagebox.showwarning("警告", "CPU压力测试工具已在运行中")
                return
            
            script_path = os.path.join(os.path.dirname(__file__), "cpu_stress_tool.py")
            
            if not os.path.exists(script_path):
                messagebox.showerror("错误", f"找不到CPU压力测试工具: {script_path}")
                return
            
            self.cpu_process = subprocess.Popen([sys.executable, script_path])
            self.update_status("✅ CPU压力测试工具已启动")
            self.stop_button.config(state=tk.NORMAL)
            
            # 启动监控线程
            threading.Thread(target=self.monitor_cpu_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动CPU压力测试工具失败: {str(e)}")
            self.update_status(f"❌ CPU压力测试工具启动失败: {str(e)}")
    
    def launch_memory_tool(self):
        """启动内存压力测试工具"""
        try:
            if self.memory_process and self.memory_process.poll() is None:
                messagebox.showwarning("警告", "内存压力测试工具已在运行中")
                return
            
            script_path = os.path.join(os.path.dirname(__file__), "memory_stress_tool.py")
            
            if not os.path.exists(script_path):
                messagebox.showerror("错误", f"找不到内存压力测试工具: {script_path}")
                return
            
            self.memory_process = subprocess.Popen([sys.executable, script_path])
            self.update_status("✅ 内存压力测试工具已启动")
            self.stop_button.config(state=tk.NORMAL)
            
            # 启动监控线程
            threading.Thread(target=self.monitor_memory_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动内存压力测试工具失败: {str(e)}")
            self.update_status(f"❌ 内存压力测试工具启动失败: {str(e)}")
    
    def launch_both_tools(self):
        """同时启动两个工具"""
        self.update_status("🚀 正在启动两个压力测试工具...")
        
        # 先启动CPU工具
        self.launch_cpu_tool()
        time.sleep(1)  # 稍等一下
        
        # 再启动内存工具
        self.launch_memory_tool()
        
        self.update_status("✅ 两个压力测试工具都已启动")
    
    def monitor_cpu_process(self):
        """监控CPU进程"""
        if self.cpu_process:
            self.cpu_process.wait()
            self.update_status("🔴 CPU压力测试工具已退出")
            self.cpu_process = None
            self.check_stop_button_state()
    
    def monitor_memory_process(self):
        """监控内存进程"""
        if self.memory_process:
            self.memory_process.wait()
            self.update_status("🔴 内存压力测试工具已退出")
            self.memory_process = None
            self.check_stop_button_state()
    
    def check_stop_button_state(self):
        """检查停止按钮状态"""
        cpu_running = self.cpu_process and self.cpu_process.poll() is None
        memory_running = self.memory_process and self.memory_process.poll() is None
        
        if not cpu_running and not memory_running:
            self.stop_button.config(state=tk.DISABLED)
    
    def stop_all_tools(self):
        """停止所有工具"""
        try:
            stopped_any = False
            
            if self.cpu_process and self.cpu_process.poll() is None:
                self.cpu_process.terminate()
                self.update_status("🛑 正在停止CPU压力测试工具...")
                stopped_any = True
            
            if self.memory_process and self.memory_process.poll() is None:
                self.memory_process.terminate()
                self.update_status("🛑 正在停止内存压力测试工具...")
                stopped_any = True
            
            if stopped_any:
                self.update_status("✅ 所有工具已停止")
                self.stop_button.config(state=tk.DISABLED)
            else:
                self.update_status("ℹ️ 没有运行中的工具需要停止")
                
        except Exception as e:
            messagebox.showerror("错误", f"停止工具失败: {str(e)}")
            self.update_status(f"❌ 停止工具失败: {str(e)}")
    
    def on_closing(self):
        """窗口关闭事件"""
        # 检查是否有运行中的进程
        cpu_running = self.cpu_process and self.cpu_process.poll() is None
        memory_running = self.memory_process and self.memory_process.poll() is None
        
        if cpu_running or memory_running:
            if messagebox.askokcancel("退出", "有压力测试工具正在运行，确定要退出吗？\n退出将停止所有运行中的工具。"):
                self.stop_all_tools()
                time.sleep(1)  # 等待进程停止
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    try:
        root = tk.Tk()
        app = ToolLauncher(root)
        
        # 绑定窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        print(f"启动器启动失败: {e}")
        messagebox.showerror("错误", f"启动器启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()