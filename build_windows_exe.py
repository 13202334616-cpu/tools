#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows可执行文件构建工具
在Windows系统上运行此脚本来创建.exe文件
"""

import os
import sys
import subprocess
import platform
import shutil

def check_windows():
    """检查是否在Windows系统上运行"""
    if platform.system() != "Windows":
        print("❌ 错误：此脚本需要在Windows系统上运行")
        print(f"   当前系统：{platform.system()}")
        print("   请将整个项目文件夹复制到Windows电脑上运行")
        return False
    return True

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print("✅ PyInstaller已安装")
        return True
    except ImportError:
        print("📦 正在安装PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                         check=True, capture_output=True, text=True)
            print("✅ PyInstaller安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller安装失败: {e}")
            return False

def install_dependencies():
    """安装项目依赖"""
    print("📦 检查并安装项目依赖...")
    try:
        # 直接安装必要的依赖包
        dependencies = ["psutil>=5.8.0"]
        for dep in dependencies:
            print(f"正在安装 {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True, text=True)
        print("✅ 项目依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def build_windows_exe():
    """构建Windows可执行文件"""
    print("🔨 开始构建Windows可执行文件...")
    
    # 检查主程序文件是否存在
    main_file = "gui_stress_tool_windows.py"
    if not os.path.exists(main_file):
        print(f"❌ 错误：找不到主程序文件 {main_file}")
        return False
    
    # PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # 单文件模式
        "--noconsole",                  # 无控制台窗口
        "--name", "ResourceStressTool", # 程序名称
        "--add-data", "schedule_config.json;.",  # 添加配置文件
        "--hidden-import", "tkinter",   # 确保tkinter被包含
        "--hidden-import", "psutil",    # 确保psutil被包含
        main_file                       # 主程序文件
    ]
    
    try:
        print("正在打包，请稍候...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        print("错误输出:", e.stderr)
        return False

def create_windows_batch():
    """创建Windows批处理启动脚本"""
    batch_content = '''@echo off
chcp 65001 >nul
title 资源压力测试工具

echo.
echo ============================================================
echo              🚀 资源压力测试工具启动器
echo ============================================================
echo.

if not exist "ResourceStressTool.exe" (
    echo ❌ 错误：找不到 ResourceStressTool.exe 文件
    echo    请确保此批处理文件与可执行文件在同一目录
    pause
    exit /b 1
)

REM 检查是否已有实例在运行
tasklist /FI "IMAGENAME eq ResourceStressTool.exe" 2>NUL | find /I /N "ResourceStressTool.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ⚠️  程序已在运行中
    echo    如需重新启动，请先关闭现有程序
    pause
    exit /b 0
)

echo ✅ 正在启动图形界面...
echo.
"ResourceStressTool.exe"

echo ✅ 程序已启动！
echo    如果程序没有显示，请检查防火墙设置
echo.
timeout /t 3 >nul
exit /b 0
'''
    
    with open("启动工具.bat", "w", encoding="utf-8-sig") as f:
        f.write(batch_content)
    
    print("✅ 创建Windows启动脚本: 启动工具.bat")

def create_windows_readme():
    """创建Windows使用说明"""
    readme_content = '''# 🖥️ Windows服务器资源压力测试工具

## 📦 文件说明
- `ResourceStressTool.exe` - 主程序（双击运行）
- `启动工具.bat` - 启动脚本（推荐使用）
- `Windows使用说明.txt` - 本文件

## 🚀 使用方法

### 方法1：双击运行（推荐）
1. 双击 `启动工具.bat`
2. 图形界面会自动打开

### 方法2：直接运行
1. 双击 `ResourceStressTool.exe`
2. 如果没有反应，请使用方法1

## 🛡️ 安全设置

### Windows Defender
如果Windows Defender阻止运行：
1. 打开Windows安全中心
2. 选择"病毒和威胁防护"
3. 点击"管理设置"
4. 添加排除项 → 文件夹
5. 选择程序所在文件夹

### 防火墙设置
如果防火墙阻止：
1. 右键点击程序 → "以管理员身份运行"
2. 或在防火墙中添加例外

## ⚙️ 功能特性

### 🎛️ 图形界面
- 拖拽滑块设置参数
- 实时监控系统状态
- 一键启停控制

### 📊 压力测试
- CPU使用率控制（1-95%）
- 内存占用控制（100MB-8GB）
- 峰值保护机制
- 紧急停止功能

### ⏰ 定时任务
- 多时间段配置
- 工作日/周末设置
- 自动启停控制
- 安全模式保护

### 📈 实时监控
- CPU使用率曲线
- 内存使用状态
- 系统负载信息
- 运行日志记录

## 🔧 系统要求
- Windows 7/8/10/11/Server
- 至少1GB可用内存
- 管理员权限（推荐）

## 📝 使用建议

### 服务器环境
1. 首次运行建议使用较低参数测试
2. 在非业务高峰期进行压力测试
3. 设置合理的峰值保护参数
4. 使用定时任务功能自动化测试

### 参数设置
- **CPU目标**: 建议不超过80%
- **CPU峰值**: 建议设置为85-90%
- **内存占用**: 根据服务器配置调整
- **内存峰值**: 建议不超过85%

### 定时任务
1. 设置夜间运行（如22:00-06:00）
2. 避开业务高峰期
3. 启用安全模式
4. 设置紧急停止时间

## ❓ 常见问题

**Q: 程序无法启动？**
A: 尝试右键"以管理员身份运行"

**Q: 图形界面没有显示？**
A: 检查防火墙设置，或使用启动脚本

**Q: CPU使用率达不到目标值？**
A: 检查系统负载，适当降低目标值

**Q: 内存占用异常？**
A: 检查可用内存，调整占用参数

**Q: 定时任务不工作？**
A: 确保程序持续运行，检查时间设置

## 🆘 技术支持
如果遇到问题，请检查：
1. Windows版本兼容性
2. 防火墙和杀毒软件设置
3. 系统资源可用性
4. 管理员权限

---
📅 构建日期: {build_date}
🔧 构建工具: PyInstaller
💻 目标系统: Windows
'''
    
    from datetime import datetime
    build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("Windows使用说明.txt", "w", encoding="utf-8-sig") as f:
        f.write(readme_content.format(build_date=build_date))
    
    print("✅ 创建Windows使用说明: Windows使用说明.txt")

def copy_files_to_dist():
    """复制必要文件到dist目录"""
    print("📁 复制必要文件...")
    
    # 创建dist目录（如果不存在）
    if not os.path.exists("dist"):
        os.makedirs("dist")
    
    # 复制配置文件
    files_to_copy = [
        "schedule_config.json",
        "启动工具.bat",
        "Windows使用说明.txt"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, "dist/")
            print(f"✅ 复制: {file}")
        else:
            print(f"⚠️  文件不存在: {file}")

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 Windows可执行文件构建工具")
    print("=" * 60)
    print()
    
    # 检查系统
    if not check_windows():
        print("\n💡 解决方案:")
        print("1. 将整个项目文件夹复制到Windows电脑")
        print("2. 在Windows上运行: python build_windows_exe.py")
        print("3. 或者使用现有的Python环境运行GUI程序")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，请检查网络连接")
        return
    
    # 安装PyInstaller
    if not install_pyinstaller():
        return
    
    # 构建可执行文件
    if not build_windows_exe():
        return
    
    # 创建辅助文件
    create_windows_batch()
    create_windows_readme()
    
    # 复制文件到dist目录
    copy_files_to_dist()
    
    print()
    print("🎉 Windows可执行文件构建完成！")
    print()
    print("📁 生成的文件:")
    print("   dist/ResourceStressTool.exe  - 主程序")
    print("   dist/启动工具.bat           - 启动脚本")
    print("   dist/Windows使用说明.txt     - 使用说明")
    print("   dist/schedule_config.json   - 配置文件")
    print()
    print("🚀 使用方法:")
    print("1. 进入dist目录")
    print("2. 双击'启动工具.bat'运行程序")
    print("3. 或者直接双击'ResourceStressTool.exe'")
    print()
    print("💡 提示:")
    print("- 首次运行可能需要等待几秒钟")
    print("- 如果被杀毒软件拦截，请添加信任")
    print("- 建议以管理员身份运行以获得最佳性能")
    print()

if __name__ == "__main__":
    main()
