#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows系统信息收集器
专为Windows 10/11和Windows Server 2016+设计

功能:
- 详细的Windows系统信息收集
- WMI查询支持
- Windows性能计数器
- 硬件信息检测
- 服务和进程监控
"""

import sys
import os
import json
import time
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import psutil
except ImportError:
    print("错误: 请安装psutil库 (pip install psutil)")
    sys.exit(1)

# Windows特定导入
if sys.platform == "win32":
    try:
        import wmi
        import win32api
        import win32con
        import win32security
        import win32net
        import win32netcon
        WINDOWS_MODULES_AVAILABLE = True
    except ImportError:
        print("警告: Windows特定模块未安装，某些功能将不可用")
        print("建议安装: pip install pywin32 wmi")
        WINDOWS_MODULES_AVAILABLE = False
else:
    WINDOWS_MODULES_AVAILABLE = False
    print("警告: 此工具专为Windows系统设计")

class WindowsSystemInfo:
    """Windows系统信息收集器"""
    
    def __init__(self):
        self.wmi_conn = None
        if WINDOWS_MODULES_AVAILABLE:
            try:
                self.wmi_conn = wmi.WMI()
            except Exception as e:
                print(f"WMI连接失败: {e}")
    
    def get_windows_version_info(self) -> Dict[str, Any]:
        """获取详细的Windows版本信息"""
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                # 获取操作系统详细信息
                for os_info in self.wmi_conn.Win32_OperatingSystem():
                    info.update({
                        "caption": os_info.Caption,
                        "build_number": os_info.BuildNumber,
                        "service_pack": os_info.ServicePackMajorVersion,
                        "architecture": os_info.OSArchitecture,
                        "install_date": str(os_info.InstallDate),
                        "last_boot_time": str(os_info.LastBootUpTime),
                        "total_memory_kb": int(os_info.TotalVisibleMemorySize),
                        "available_memory_kb": int(os_info.FreePhysicalMemory),
                    })
                    break
                
                # 获取计算机系统信息
                for computer in self.wmi_conn.Win32_ComputerSystem():
                    info.update({
                        "computer_name": computer.Name,
                        "domain": computer.Domain,
                        "manufacturer": computer.Manufacturer,
                        "model": computer.Model,
                        "total_physical_memory": int(computer.TotalPhysicalMemory),
                        "number_of_processors": computer.NumberOfProcessors,
                    })
                    break
                    
            except Exception as e:
                print(f"获取Windows详细信息失败: {e}")
        
        return info
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """获取硬件信息"""
        hardware = {
            "cpu": self._get_cpu_info(),
            "memory": self._get_memory_info(),
            "disk": self._get_disk_info(),
            "network": self._get_network_info(),
        }
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                # 主板信息
                for board in self.wmi_conn.Win32_BaseBoard():
                    hardware["motherboard"] = {
                        "manufacturer": board.Manufacturer,
                        "product": board.Product,
                        "serial_number": board.SerialNumber,
                    }
                    break
                
                # BIOS信息
                for bios in self.wmi_conn.Win32_BIOS():
                    hardware["bios"] = {
                        "manufacturer": bios.Manufacturer,
                        "version": bios.Version,
                        "release_date": str(bios.ReleaseDate),
                    }
                    break
                
                # 显卡信息
                hardware["graphics"] = []
                for gpu in self.wmi_conn.Win32_VideoController():
                    if gpu.Name:
                        hardware["graphics"].append({
                            "name": gpu.Name,
                            "driver_version": gpu.DriverVersion,
                            "video_memory": gpu.AdapterRAM,
                        })
                        
            except Exception as e:
                print(f"获取硬件信息失败: {e}")
        
        return hardware
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息"""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "usage_percent": psutil.cpu_percent(interval=1),
            "usage_per_core": psutil.cpu_percent(interval=1, percpu=True),
        }
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                for processor in self.wmi_conn.Win32_Processor():
                    cpu_info.update({
                        "name": processor.Name,
                        "manufacturer": processor.Manufacturer,
                        "max_clock_speed": processor.MaxClockSpeed,
                        "current_clock_speed": processor.CurrentClockSpeed,
                        "cores": processor.NumberOfCores,
                        "threads": processor.NumberOfLogicalProcessors,
                        "architecture": processor.Architecture,
                        "family": processor.Family,
                        "model": processor.Model,
                        "stepping": processor.Stepping,
                    })
                    break
            except Exception as e:
                print(f"获取CPU详细信息失败: {e}")
        
        return cpu_info
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percentage": swap.percent,
        }
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                # 物理内存模块信息
                memory_info["modules"] = []
                for memory_module in self.wmi_conn.Win32_PhysicalMemory():
                    memory_info["modules"].append({
                        "capacity": int(memory_module.Capacity),
                        "speed": memory_module.Speed,
                        "manufacturer": memory_module.Manufacturer,
                        "part_number": memory_module.PartNumber,
                        "serial_number": memory_module.SerialNumber,
                        "memory_type": memory_module.MemoryType,
                    })
            except Exception as e:
                print(f"获取内存模块信息失败: {e}")
        
        return memory_info
    
    def _get_disk_info(self) -> List[Dict[str, Any]]:
        """获取磁盘信息"""
        disks = []
        
        # 基本磁盘使用信息
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percentage": (usage.used / usage.total) * 100,
                }
                disks.append(disk_info)
            except PermissionError:
                continue
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                # 物理磁盘信息
                for disk in self.wmi_conn.Win32_DiskDrive():
                    disk_info = {
                        "model": disk.Model,
                        "size": int(disk.Size) if disk.Size else 0,
                        "interface_type": disk.InterfaceType,
                        "media_type": disk.MediaType,
                        "serial_number": disk.SerialNumber,
                    }
                    # 查找对应的逻辑磁盘
                    for i, existing_disk in enumerate(disks):
                        if existing_disk["device"].startswith(disk.DeviceID.replace("\\", "").replace(".", "")):
                            disks[i].update(disk_info)
                            break
            except Exception as e:
                print(f"获取物理磁盘信息失败: {e}")
        
        return disks
    
    def _get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        network_info = {
            "interfaces": [],
            "connections": len(psutil.net_connections()),
            "io_stats": dict(psutil.net_io_counters()._asdict()),
        }
        
        # 网络接口信息
        for interface, addresses in psutil.net_if_addrs().items():
            interface_info = {
                "name": interface,
                "addresses": [],
            }
            
            for addr in addresses:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                })
            
            # 获取接口统计信息
            if interface in psutil.net_io_counters(pernic=True):
                stats = psutil.net_io_counters(pernic=True)[interface]
                interface_info["stats"] = dict(stats._asdict())
            
            network_info["interfaces"].append(interface_info)
        
        return network_info
    
    def get_services_info(self) -> List[Dict[str, Any]]:
        """获取Windows服务信息"""
        services = []
        
        if WINDOWS_MODULES_AVAILABLE and self.wmi_conn:
            try:
                for service in self.wmi_conn.Win32_Service():
                    services.append({
                        "name": service.Name,
                        "display_name": service.DisplayName,
                        "state": service.State,
                        "start_mode": service.StartMode,
                        "path": service.PathName,
                        "description": service.Description,
                    })
            except Exception as e:
                print(f"获取服务信息失败: {e}")
        
        return services
    
    def get_processes_info(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """获取进程信息"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'create_time']):
            try:
                proc_info = proc.info
                proc_info['memory_mb'] = proc_info['memory_info'].rss / 1024 / 1024
                proc_info['create_time_str'] = datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        return processes[:top_n]
    
    def get_performance_counters(self) -> Dict[str, Any]:
        """获取Windows性能计数器"""
        counters = {}
        
        if WINDOWS_MODULES_AVAILABLE:
            try:
                # 这里可以添加更多的性能计数器查询
                # 例如：网络吞吐量、磁盘队列长度等
                counters["timestamp"] = datetime.now().isoformat()
                counters["cpu_usage"] = psutil.cpu_percent(interval=1)
                counters["memory_usage"] = psutil.virtual_memory().percent
                counters["disk_usage"] = {}
                
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        counters["disk_usage"][partition.device] = {
                            "usage_percent": (usage.used / usage.total) * 100,
                            "free_gb": usage.free / (1024**3),
                        }
                    except PermissionError:
                        continue
                        
            except Exception as e:
                print(f"获取性能计数器失败: {e}")
        
        return counters
    
    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整的系统报告"""
        print("正在收集Windows系统信息...")
        
        report = {
            "report_time": datetime.now().isoformat(),
            "windows_version": self.get_windows_version_info(),
            "hardware": self.get_hardware_info(),
            "performance": self.get_performance_counters(),
            "top_processes": self.get_processes_info(20),
        }
        
        # 可选的详细信息（可能较慢）
        if WINDOWS_MODULES_AVAILABLE:
            print("正在收集服务信息...")
            report["services"] = self.get_services_info()
        
        return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Windows系统信息收集器")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
    parser.add_argument("--monitor", "-m", action="store_true", help="持续监控模式")
    parser.add_argument("--interval", "-i", type=int, default=60, help="监控间隔（秒）")
    parser.add_argument("--services", "-s", action="store_true", help="包含服务信息")
    parser.add_argument("--processes", "-p", action="store_true", help="显示进程信息")
    
    args = parser.parse_args()
    
    if not sys.platform == "win32":
        print("错误: 此工具仅支持Windows系统")
        sys.exit(1)
    
    collector = WindowsSystemInfo()
    
    def collect_and_display():
        if args.processes:
            print("\n=== 进程信息 ===")
            processes = collector.get_processes_info(10)
            for proc in processes:
                print(f"PID: {proc['pid']:>6} | CPU: {proc['cpu_percent']:>5.1f}% | 内存: {proc['memory_mb']:>6.1f}MB | {proc['name']}")
        
        if args.services and WINDOWS_MODULES_AVAILABLE:
            print("\n=== 运行中的服务 ===")
            services = [s for s in collector.get_services_info() if s['state'] == 'Running']
            for service in services[:10]:
                print(f"{service['name']:30} | {service['display_name']}")
        
        # 生成完整报告
        report = collector.generate_full_report()
        
        if args.format == "json":
            output = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            # 文本格式输出
            output = format_text_report(report)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {args.output}")
        else:
            print(output)
    
    if args.monitor:
        print(f"开始监控模式，间隔 {args.interval} 秒...")
        try:
            while True:
                collect_and_display()
                print(f"\n{'='*50}")
                print(f"下次更新: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
    else:
        collect_and_display()

def format_text_report(report: Dict[str, Any]) -> str:
    """格式化文本报告"""
    lines = []
    lines.append("Windows系统信息报告")
    lines.append("=" * 50)
    lines.append(f"报告时间: {report['report_time']}")
    lines.append("")
    
    # Windows版本信息
    win_info = report['windows_version']
    lines.append("Windows版本信息:")
    lines.append(f"  系统: {win_info.get('caption', 'N/A')}")
    lines.append(f"  版本: {win_info.get('version', 'N/A')}")
    lines.append(f"  构建号: {win_info.get('build_number', 'N/A')}")
    lines.append(f"  架构: {win_info.get('architecture', 'N/A')}")
    lines.append(f"  计算机名: {win_info.get('computer_name', 'N/A')}")
    lines.append("")
    
    # 硬件信息
    hardware = report['hardware']
    lines.append("硬件信息:")
    
    # CPU
    cpu = hardware['cpu']
    lines.append(f"  CPU: {cpu.get('name', 'N/A')}")
    lines.append(f"  核心数: {cpu.get('cores', 'N/A')} 物理 / {cpu.get('threads', 'N/A')} 逻辑")
    lines.append(f"  频率: {cpu.get('current_clock_speed', 'N/A')} MHz")
    lines.append(f"  使用率: {cpu.get('usage_percent', 'N/A')}%")
    lines.append("")
    
    # 内存
    memory = hardware['memory']
    total_gb = memory['total'] / (1024**3)
    used_gb = memory['used'] / (1024**3)
    lines.append(f"  内存: {used_gb:.1f}GB / {total_gb:.1f}GB ({memory['percentage']:.1f}%)")
    lines.append("")
    
    # 磁盘
    lines.append("  磁盘:")
    for disk in hardware['disk']:
        total_gb = disk['total'] / (1024**3)
        used_gb = disk['used'] / (1024**3)
        lines.append(f"    {disk['device']} {used_gb:.1f}GB / {total_gb:.1f}GB ({disk['percentage']:.1f}%)")
    lines.append("")
    
    # 性能信息
    perf = report['performance']
    lines.append("当前性能:")
    lines.append(f"  CPU使用率: {perf.get('cpu_usage', 'N/A')}%")
    lines.append(f"  内存使用率: {perf.get('memory_usage', 'N/A')}%")
    lines.append("")
    
    # 进程信息
    lines.append("CPU使用率最高的进程:")
    for proc in report['top_processes'][:5]:
        lines.append(f"  {proc['name']:20} PID:{proc['pid']:>6} CPU:{proc['cpu_percent']:>5.1f}% 内存:{proc['memory_mb']:>6.1f}MB")
    
    return "\n".join(lines)

if __name__ == "__main__":
    main()