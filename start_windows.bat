@echo off
chcp 65001 >nul
echo ========================================
echo    服务器资源配置提升工具 - Windows版
echo ========================================
echo.
echo 正在启动程序...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show psutil >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖包 psutil...
    pip install psutil
)

REM 设置环境变量以抑制Tkinter警告
set TK_SILENCE_DEPRECATION=1

REM 启动程序
echo 启动服务器资源配置提升工具...
python resource_manager.py

REM 如果程序异常退出，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    echo 请检查错误信息并重试
    pause
)

echo.
echo 程序已退出
pause