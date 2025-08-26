#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的CPU控制测试程序
用于验证CPU动态控制逻辑是否正确
"""

import os
import time
import psutil
import multiprocessing as mp
from typing import List

def cpu_worker_loop(worker_id: int, duty_value: mp.Value, stop_event: mp.Event):
    """
    CPU工作进程函数
    通过调节工作强度来控制CPU占用
    """
    print(f"Worker {worker_id} started")
    
    while not stop_event.is_set():
        if duty_value.value > 0:
            # 工作阶段 - 执行计算密集型任务
            work_time = duty_value.value * 0.05  # 减少工作时间单位
            rest_time = (1.0 - duty_value.value) * 0.05  # 减少休息时间单位
            
            # 执行更密集的计算任务
            start_time = time.time()
            while time.time() - start_time < work_time:
                _ = sum(i * i * i for i in range(5000))  # 增加计算强度
            
            # 休息
            if rest_time > 0:
                time.sleep(rest_time)
        else:
            # 如果duty_value为0，则休息
            time.sleep(0.05)
    
    print(f"Worker {worker_id} stopped")

class SimpleCpuController:
    def __init__(self, target_percent=80.0):
        self.target_percent = target_percent
        self.running = False
        self.processes: List[mp.Process] = []
        self.stop_event: mp.Event = None
        self.duty_value: mp.Value = None
        self.core_count = max(1, os.cpu_count() or 1)
        self.kp = 0.15  # 提高比例增益，加快响应速度
        
    def start(self):
        if self.running:
            return
            
        print(f"Starting CPU controller with target: {self.target_percent}%")
        print(f"System has {self.core_count} CPU cores")
        
        self.running = True
        self.stop_event = mp.Event()
        self.duty_value = mp.Value('d', 0.1)  # 初始duty值
        
        # 创建适量工作进程
        worker_count = min(6, max(2, self.core_count // 2))
        print(f"Creating {worker_count} worker processes")
        
        for i in range(worker_count):
            p = mp.Process(
                target=cpu_worker_loop,
                args=(i, self.duty_value, self.stop_event)
            )
            p.start()
            self.processes.append(p)
        
        print(f"Started {len(self.processes)} worker processes")
        
    def stop(self):
        if not self.running:
            return
            
        print("Stopping CPU controller...")
        self.running = False
        
        if self.stop_event:
            self.stop_event.set()
        
        # 等待所有进程结束
        for p in self.processes:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
                p.join()
        
        self.processes.clear()
        print("CPU controller stopped")
        
    def control_loop(self, duration=30):
        """
        控制循环 - 监控和调整CPU使用率
        """
        if not self.running:
            return
            
        print(f"Starting control loop for {duration} seconds...")
        last_cpu_readings = []
        max_readings = 5
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                # 获取当前CPU使用率
                current = psutil.cpu_percent(interval=1.0)
                
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
                      f"Error: {error:.1f}%, Duty: {new_duty:.3f}")
                
                time.sleep(2)  # 控制循环间隔
                
            except Exception as e:
                print(f"Control loop error: {e}")
                time.sleep(1)

def main():
    print("=== CPU动态控制测试程序 ===")
    print("此程序将测试CPU动态控制逻辑")
    
    # 创建控制器
    controller = SimpleCpuController(target_percent=60.0)  # 设置较低的目标值便于测试
    
    try:
        # 启动控制器
        controller.start()
        
        # 运行控制循环
        controller.control_loop(duration=30)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        # 停止控制器
        controller.stop()
        print("测试完成")

if __name__ == "__main__":
    main()