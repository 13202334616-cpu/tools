#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU管理程序 - 命令行版本
用于测试CPU动态控制逻辑，不依赖GUI库
"""

import os
import sys
import time
import math
import psutil
import signal
import threading
import multiprocessing as mp
from typing import List

def cpu_worker_loop(worker_id: int, duty_value: mp.Value, stop_event: mp.Event):
    """
    CPU工作进程函数
    通过调节工作强度来控制CPU占用
    """
    print(f"Worker {worker_id} started")
    
    while not stop_event.is_set():
        try:
            if duty_value.value > 0:
                # 工作阶段 - 执行计算密集型任务
                work_time = duty_value.value * 0.05  # 减少工作时间单位
                rest_time = (1.0 - duty_value.value) * 0.05  # 减少休息时间单位
                
                # 执行更密集的计算任务
                start_time = time.time()
                while time.time() - start_time < work_time:
                    # 增加计算强度和复杂度
                    _ = sum(i * i * i + math.sin(i) * math.cos(i) for i in range(10000))
                    _ = [x**2 for x in range(1000)]
                
                # 休息
                if rest_time > 0:
                    time.sleep(rest_time)
            else:
                # 如果duty_value为0，则休息
                time.sleep(0.05)
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            time.sleep(0.1)
    
    print(f"Worker {worker_id} stopped")

class CpuController:
    def __init__(self, target_percent=80.0):
        self.target_percent = target_percent
        self.running = False
        self.processes: List[mp.Process] = []
        self.stop_event: mp.Event = None
        self.duty_value: mp.Value = None
        self.control_thread: threading.Thread = None
        self.core_count = max(1, os.cpu_count() or 1)
        self.kp = 0.15  # 提高比例增益，加快响应速度
        
    def start(self):
        if self.running:
            print("CPU controller is already running")
            return
            
        print(f"Starting CPU controller with target: {self.target_percent}%")
        print(f"System has {self.core_count} CPU cores")
        
        self.running = True
        self.stop_event = mp.Event()
        self.duty_value = mp.Value('d', 0.1)  # 初始duty值
        
        # 创建更多工作进程以达到更高CPU使用率
        worker_count = min(self.core_count, max(4, self.core_count * 3 // 4))
        print(f"Creating {worker_count} worker processes")
        
        try:
            for i in range(worker_count):
                p = mp.Process(
                    target=cpu_worker_loop,
                    args=(i, self.duty_value, self.stop_event),
                    daemon=True
                )
                p.start()
                self.processes.append(p)
            
            print(f"Started {len(self.processes)} worker processes")
            
            # 启动控制线程
            self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
            self.control_thread.start()
            print("Control thread started")
            
        except Exception as e:
            print(f"Error starting CPU controller: {e}")
            self.stop()
        
    def stop(self):
        if not self.running:
            return
            
        print("Stopping CPU controller...")
        self.running = False
        
        if self.stop_event:
            self.stop_event.set()
        
        # 等待控制线程结束
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=2)
        
        # 等待所有进程结束
        for p in self.processes:
            if p.is_alive():
                p.join(timeout=2)
                if p.is_alive():
                    p.terminate()
                    p.join(timeout=1)
                    if p.is_alive():
                        p.kill()
        
        self.processes.clear()
        print("CPU controller stopped")
        
    def _control_loop(self):
        """
        控制循环 - 监控和调整CPU使用率
        """
        print("Control loop started")
        last_cpu_readings = []
        max_readings = 5
        
        while self.running:
            try:
                # 获取当前CPU使用率
                current = psutil.cpu_percent(interval=1.0)  # 增加测量间隔提高准确性
                
                # 平滑CPU读数
                last_cpu_readings.append(current)
                if len(last_cpu_readings) > max_readings:
                    last_cpu_readings.pop(0)
                
                # 使用平均值进行控制
                avg_cpu = sum(last_cpu_readings) / len(last_cpu_readings)
                
                # 计算误差
                error = self.target_percent - avg_cpu
                
                # 改进的控制算法
                current_duty = self.duty_value.value
                
                # 根据误差大小调整控制强度
                if abs(error) > 10:  # 大误差时快速调整
                    adjustment = self.kp * 2 * (error / 100.0)
                elif abs(error) > 5:  # 中等误差时正常调整
                    adjustment = self.kp * (error / 100.0)
                else:  # 小误差时细微调整
                    adjustment = self.kp * 0.5 * (error / 100.0)
                
                new_duty = current_duty + adjustment
                new_duty = max(0.0, min(1.0, new_duty))  # 限制在0-1范围内
                
                # 避免过度振荡
                if abs(new_duty - current_duty) < 0.01 and abs(error) < 2:
                    new_duty = current_duty  # 保持当前值
                
                self.duty_value.value = new_duty
                
                # 输出状态信息
                print(f"CPU: {avg_cpu:.1f}% (target: {self.target_percent}%), "
                      f"Error: {error:.1f}%, Duty: {new_duty:.3f}, Workers: {len([p for p in self.processes if p.is_alive()])}")
                
                # 检查进程状态
                alive_processes = [p for p in self.processes if p.is_alive()]
                if len(alive_processes) < len(self.processes):
                    print(f"Warning: {len(self.processes) - len(alive_processes)} worker processes died")
                
                time.sleep(2)  # 控制循环间隔
                
            except Exception as e:
                print(f"Control loop error: {e}")
                time.sleep(1)
        
        print("Control loop stopped")

# 全局控制器实例
controller = None

def signal_handler(signum, frame):
    """信号处理函数"""
    print(f"\nReceived signal {signum}, stopping...")
    if controller:
        controller.stop()
    sys.exit(0)

def main():
    global controller
    
    print("=== CPU动态管理程序 - 命令行版本 ===")
    print("按 Ctrl+C 停止程序")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 获取目标CPU使用率
    target = 80.0
    if len(sys.argv) > 1:
        try:
            target = float(sys.argv[1])
            if target < 0 or target > 100:
                print("目标CPU使用率必须在0-100之间")
                return
        except ValueError:
            print("无效的目标CPU使用率")
            return
    
    # 创建控制器
    controller = CpuController(target_percent=target)
    
    try:
        # 启动控制器
        controller.start()
        
        # 主循环
        while controller.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"程序错误: {e}")
    finally:
        # 停止控制器
        if controller:
            controller.stop()
        print("程序结束")

if __name__ == "__main__":
    main()