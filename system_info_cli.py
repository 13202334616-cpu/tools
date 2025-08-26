#!/usr/bin/env python3
"""
系统信息收集命令行工具
提供详细的系统资源监控信息
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import psutil

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    # CPU信息
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    # 内存信息
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # 磁盘信息
    disk_usage = psutil.disk_usage('/')
    
    try:
        disk_io = psutil.disk_io_counters()
    except:
        disk_io = None
    
    # 网络信息
    try:
        network_io = psutil.net_io_counters()
    except:
        network_io = None
    
    # 系统启动时间
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    # 进程信息
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            proc_info = proc.info
            if proc_info['cpu_percent'] is not None and proc_info['cpu_percent'] > 0:
                processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # 按CPU使用率排序
    processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'platform': sys.platform,
            'boot_time': boot_time.isoformat(),
            'uptime_hours': (datetime.now() - boot_time).total_seconds() / 3600
        },
        'cpu': {
            'percent': cpu_percent,
            'count_logical': cpu_count,
            'count_physical': psutil.cpu_count(logical=False),
            'freq_current': cpu_freq.current if cpu_freq else 0,
            'freq_max': cpu_freq.max if cpu_freq else 0,
            'freq_min': cpu_freq.min if cpu_freq else 0
        },
        'memory': {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent': memory.percent,
            'swap_total_gb': swap.total / (1024**3),
            'swap_used_gb': swap.used / (1024**3),
            'swap_percent': swap.percent
        },
        'disk': {
            'total_gb': disk_usage.total / (1024**3),
            'used_gb': disk_usage.used / (1024**3),
            'free_gb': disk_usage.free / (1024**3),
            'percent': (disk_usage.used / disk_usage.total) * 100,
            'read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0
        },
        'network': {
            'bytes_sent_gb': network_io.bytes_sent / (1024**3) if network_io else 0,
            'bytes_recv_gb': network_io.bytes_recv / (1024**3) if network_io else 0,
            'packets_sent': network_io.packets_sent if network_io else 0,
            'packets_recv': network_io.packets_recv if network_io else 0
        },
        'top_processes': processes[:10]
    }

def format_bytes(bytes_value: float) -> str:
    """格式化字节数"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def print_system_overview(info: Dict[str, Any]):
    """打印系统概览"""
    print("\n" + "="*60)
    print("           系统资源监控概览")
    print("="*60)
    
    # 系统信息
    print(f"\n📊 系统信息:")
    print(f"   平台: {info['system']['platform']}")
    print(f"   启动时间: {info['system']['boot_time'][:19]}")
    print(f"   运行时间: {info['system']['uptime_hours']:.1f} 小时")
    
    # CPU信息
    cpu = info['cpu']
    print(f"\n🖥️  CPU信息:")
    print(f"   使用率: {cpu['percent']:.1f}%")
    print(f"   逻辑核心: {cpu['count_logical']} 个")
    print(f"   物理核心: {cpu['count_physical']} 个")
    print(f"   当前频率: {cpu['freq_current']:.0f} MHz")
    print(f"   最大频率: {cpu['freq_max']:.0f} MHz")
    
    # 内存信息
    mem = info['memory']
    print(f"\n💾 内存信息:")
    print(f"   使用率: {mem['percent']:.1f}%")
    print(f"   总内存: {mem['total_gb']:.1f} GB")
    print(f"   已使用: {mem['used_gb']:.1f} GB")
    print(f"   可用: {mem['available_gb']:.1f} GB")
    if mem['swap_total_gb'] > 0:
        print(f"   交换分区: {mem['swap_percent']:.1f}% ({mem['swap_used_gb']:.1f}/{mem['swap_total_gb']:.1f} GB)")
    
    # 磁盘信息
    disk = info['disk']
    print(f"\n💿 磁盘信息:")
    print(f"   使用率: {disk['percent']:.1f}%")
    print(f"   总容量: {disk['total_gb']:.0f} GB")
    print(f"   已使用: {disk['used_gb']:.0f} GB")
    print(f"   可用: {disk['free_gb']:.0f} GB")
    print(f"   累计读取: {format_bytes(disk['read_mb'] * 1024**2)}")
    print(f"   累计写入: {format_bytes(disk['write_mb'] * 1024**2)}")
    
    # 网络信息
    net = info['network']
    print(f"\n🌐 网络信息:")
    print(f"   累计发送: {net['bytes_sent_gb']:.2f} GB ({net['packets_sent']} 包)")
    print(f"   累计接收: {net['bytes_recv_gb']:.2f} GB ({net['packets_recv']} 包)")
    
    print("\n" + "="*60)

def print_top_processes(processes: List[Dict[str, Any]]):
    """打印进程信息"""
    print("\n🔥 CPU使用率最高的进程:")
    print("-" * 70)
    print(f"{'PID':<8} {'进程名':<25} {'CPU%':<8} {'内存%':<8} {'状态':<10}")
    print("-" * 70)
    
    for proc in processes:
        pid = proc.get('pid', 'N/A')
        name = proc.get('name', 'N/A')[:24]
        cpu_percent = proc.get('cpu_percent', 0) or 0
        memory_percent = proc.get('memory_percent', 0) or 0
        status = proc.get('status', 'N/A')
        
        print(f"{pid:<8} {name:<25} {cpu_percent:<8.1f} {memory_percent:<8.1f} {status:<10}")

def print_resource_bars(info: Dict[str, Any]):
    """打印资源使用条形图"""
    def create_bar(percent: float, width: int = 40) -> str:
        filled = int(percent * width / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percent:.1f}%"
    
    print("\n📈 资源使用情况:")
    print("-" * 60)
    
    cpu_percent = info['cpu']['percent']
    mem_percent = info['memory']['percent']
    disk_percent = info['disk']['percent']
    
    print(f"CPU:  {create_bar(cpu_percent)}")
    print(f"内存: {create_bar(mem_percent)}")
    print(f"磁盘: {create_bar(disk_percent)}")
    
    # 颜色提示
    print("\n💡 状态说明:")
    if cpu_percent > 80:
        print("   ⚠️  CPU使用率较高")
    if mem_percent > 80:
        print("   ⚠️  内存使用率较高")
    if disk_percent > 90:
        print("   ⚠️  磁盘空间不足")
    
    if cpu_percent < 50 and mem_percent < 70 and disk_percent < 80:
        print("   ✅ 系统资源使用正常")

def monitor_mode(interval: int = 5):
    """监控模式"""
    print("\n🔄 进入实时监控模式 (按 Ctrl+C 退出)")
    print(f"   更新间隔: {interval} 秒")
    
    try:
        while True:
            # 清屏
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # 获取并显示信息
            info = get_system_info()
            print_system_overview(info)
            print_resource_bars(info)
            
            # 等待
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='系统资源监控工具')
    parser.add_argument('-m', '--monitor', action='store_true', help='进入实时监控模式')
    parser.add_argument('-i', '--interval', type=int, default=5, help='监控间隔(秒), 默认5秒')
    parser.add_argument('-j', '--json', action='store_true', help='输出JSON格式')
    parser.add_argument('-p', '--processes', action='store_true', help='显示进程信息')
    parser.add_argument('-s', '--save', type=str, help='保存信息到文件')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_mode(args.interval)
        return
    
    # 获取系统信息
    info = get_system_info()
    
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print_system_overview(info)
        print_resource_bars(info)
        
        if args.processes:
            print_top_processes(info['top_processes'])
    
    # 保存到文件
    if args.save:
        try:
            with open(args.save, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            print(f"\n💾 信息已保存到: {args.save}")
        except Exception as e:
            print(f"\n❌ 保存失败: {e}")

if __name__ == "__main__":
    main()