@echo off
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

echo ✅ 正在启动图形界面...
echo.
start "" "ResourceStressTool.exe"

echo ✅ 程序已启动！
echo    如果程序没有显示，请检查防火墙设置
echo.
timeout /t 3 >nul
exit /b 0
