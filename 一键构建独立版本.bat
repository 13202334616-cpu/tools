@echo off
chcp 65001 >nul
title 一键构建独立可执行版本

echo.
echo ============================================================
echo            🚀 一键构建独立可执行版本
echo ============================================================
echo.

echo 📋 检查构建环境...
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到Python环境
    echo.
    echo 💡 解决方案：
    echo 1. 安装Python 3.7或更高版本
    echo 2. 确保Python已添加到系统PATH
    echo 3. 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python环境正常
python --version

REM 检查主程序文件
if not exist "gui_stress_tool_windows.py" (
    echo ❌ 错误：找不到主程序文件 gui_stress_tool_windows.py
    echo.
    pause
    exit /b 1
)

echo ✅ 主程序文件存在

REM 检查配置文件
if not exist "schedule_config.json" (
    echo ⚠️  警告：找不到配置文件 schedule_config.json
    echo    将使用默认配置
)

echo.
echo 🔨 开始构建过程...
echo.

REM 运行构建脚本
python build_windows_exe.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！
    echo.
    echo 💡 可能的解决方案：
    echo 1. 检查网络连接（需要下载依赖包）
    echo 2. 以管理员身份运行此脚本
    echo 3. 确保有足够的磁盘空间
    echo 4. 检查杀毒软件是否阻止了构建过程
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo                    🎉 构建完成！
echo ============================================================
echo.
echo 📁 生成的文件位置：dist/ 目录
echo.
echo 🚀 使用方法：
echo 1. 双击根目录的 "直接启动.bat" 运行程序（推荐）
echo 2. 或者进入 dist/ 目录双击 "ResourceStressTool.exe"
echo 3. 或者进入 dist/ 目录双击 "启动工具.bat"
echo.
echo 💡 重要提示：
echo - 首次运行可能需要等待几秒钟
echo - 如果被杀毒软件拦截，请添加信任
echo - 建议以管理员身份运行以获得最佳性能
echo.
echo 📋 文件说明：
echo - ResourceStressTool.exe    主程序（无需Python环境）
echo - 启动工具.bat             启动脚本
echo - Windows使用说明.txt      使用说明
echo - schedule_config.json     配置文件
echo.
echo 是否现在打开dist目录？(Y/N)
set /p open_dist=
if /i "%open_dist%"=="Y" (
    explorer dist
)

echo.
echo 构建过程完成！按任意键退出...
pause >nul