@echo off
chcp 65001 >nul
title 直接启动 - 资源压力测试工具

echo.
echo ============================================================
echo            🚀 直接启动资源压力测试工具
echo ============================================================
echo.

REM 优先检查dist目录中的可执行版本
if exist "dist\ResourceStressTool.exe" (
    echo ✅ 发现构建的独立可执行版本，正在启动...
    echo.
    start "" "dist\ResourceStressTool.exe"
    exit /b 0
)

REM 检查当前目录的可执行版本
if exist "ResourceStressTool.exe" (
    echo ✅ 发现独立可执行版本，正在启动...
    echo.
    start "" "ResourceStressTool.exe"
    exit /b 0
)

REM 检查Python版本
if exist "gui_stress_tool_windows.py" (
    echo ✅ 发现Python源码版本，正在检查环境...
    echo.
    
    python --version >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ Python环境正常，正在启动...
        echo.
        python gui_stress_tool_windows.py
        exit /b 0
    )
    
    python3 --version >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ Python3环境正常，正在启动...
        echo.
        python3 gui_stress_tool_windows.py
        exit /b 0
    )
    
    py --version >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ Python Launcher正常，正在启动...
        echo.
        py gui_stress_tool_windows.py
        exit /b 0
    )
    
    echo ❌ 未找到Python环境
    echo.
    echo 💡 建议：
    echo 1. 安装Python 3.7+
    echo 2. 或者构建独立可执行版本
    echo 3. 或者运行"主菜单.bat"获取帮助
    echo.
    pause
    exit /b 1
)

echo ❌ 未找到程序文件
echo.
echo 💡 请确保以下文件之一存在：
echo    - ResourceStressTool.exe （独立可执行版本）
echo    - gui_stress_tool_windows.py （Python源码版本）
echo.
pause
exit /b 1