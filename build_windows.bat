@echo off
chcp 65001 >nul
echo ========================================
echo Windows系统资源管理工具构建脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查pip是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pip，请检查Python安装
    pause
    exit /b 1
)

echo 正在升级pip...
python -m pip install --upgrade pip

echo 正在安装依赖包...
pip install -r requirements.txt
pip install pyinstaller

REM 创建输出目录
if not exist "dist" mkdir dist
if not exist "build" mkdir build

echo.
echo 开始构建可执行文件...
echo ========================================

REM 设置版本号
set VERSION=1.0.%date:~0,4%%date:~5,2%%date:~8,2%

echo 构建CPU管理器 (GUI版本)...
pyinstaller --onefile --windowed --name "CPUManager-v%VERSION%" --distpath dist --workpath build\cpu_manager_app cpu_manager_app.py
if %errorlevel% neq 0 (
    echo 错误: CPU管理器构建失败
    pause
    exit /b 1
)

echo 构建内存管理器 (GUI版本)...
pyinstaller --onefile --windowed --name "MemoryManager-v%VERSION%" --distpath dist --workpath build\memory_manager_app memory_manager_app.py
if %errorlevel% neq 0 (
    echo 错误: 内存管理器构建失败
    pause
    exit /b 1
)

echo 构建系统仪表盘...
pyinstaller --onefile --windowed --name "SystemDashboard-v%VERSION%" --distpath dist --workpath build\system_dashboard system_dashboard.py
if %errorlevel% neq 0 (
    echo 错误: 系统仪表盘构建失败
    pause
    exit /b 1
)

echo 构建CPU管理器 (CLI版本)...
pyinstaller --onefile --console --name "CPUManager-CLI-v%VERSION%" --distpath dist --workpath build\cpu_manager_cli cpu_manager_cli.py
if %errorlevel% neq 0 (
    echo 错误: CPU管理器CLI构建失败
    pause
    exit /b 1
)

echo 构建系统信息工具 (CLI版本)...
pyinstaller --onefile --console --name "SystemInfo-CLI-v%VERSION%" --distpath dist --workpath build\system_info_cli system_info_cli.py
if %errorlevel% neq 0 (
    echo 错误: 系统信息工具构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成！
echo ========================================
echo.
echo 生成的文件位于 dist\ 目录:
dir /b dist\*.exe
echo.
echo 文件大小:
for %%f in (dist\*.exe) do (
    echo %%~nxf: %%~zf 字节
)

echo.
echo 提示: 如需进一步压缩文件大小，可以使用UPX工具
echo 下载地址: https://github.com/upx/upx/releases
echo 使用方法: upx --best dist\*.exe
echo.
pause