@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===== Build single-file EXEs for Windows (no runtime needed on target) =====
REM This script will:
REM 1) Find or install Python 3.x on the build machine
REM 2) Create a local venv and install PyInstaller + requirements
REM 3) Build CPUManager.exe and MemoryManager.exe into dist\

:: 0) Detect Python
set "PY_CMD="
where python >NUL 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
  where py >NUL 2>&1 && set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo [Info] Python not found. Trying to install via winget...
  where winget >NUL 2>&1
  if %errorlevel%==0 (
    winget install -e --id Python.Python.3.12 -h
    if %errorlevel%==0 (
      set "PY_CMD=py -3"
    )
  )
)

if not defined PY_CMD (
  echo [Info] winget not available or install failed. Trying official installer download...
  set "TMPDIR=%TEMP%\pyinst"
  if exist "%TMPDIR%" rd /s /q "%TMPDIR%"
  mkdir "%TMPDIR%" >NUL 2>&1
  set "PY_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%TMPDIR%\python_installer.exe'"  || goto :error
  if exist "%TMPDIR%\python_installer.exe" (
    "%TMPDIR%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 || goto :error
    set "PY_CMD=py -3"
  )
)

if not defined PY_CMD (
  echo [Error] Python 3 not installed. Please install Python 3.10+ (64-bit) and re-run this script.
  pause
  exit /b 1
)

:: Sanity check
%PY_CMD% -V || (echo [Error] Failed to launch Python. & pause & exit /b 1)

:: 1) Create venv
if not exist .venv-build (
  echo [1/4] Creating virtual env .venv-build ...
  %PY_CMD% -m venv .venv-build || goto :error
)
call .\.venv-build\Scripts\activate.bat || goto :error

:: 2) Install build tools and deps
echo [2/4] Upgrading pip/setuptools/wheel ...
python -m pip install --upgrade pip setuptools wheel || goto :error

echo [3/4] Installing PyInstaller and project requirements ...
pip install pyinstaller==6.6.0 pyinstaller-hooks-contrib || goto :error
pip install -r requirements.txt || goto :error

:: 3) Build executables (collect PySide6 runtime)
echo [4/4] Building CPUManager.exe ...
pyinstaller --noconfirm --clean --windowed --onefile --collect-all PySide6 --name "CPUManager" cpu_manager_app.py || goto :error

echo Building MemoryManager.exe ...
pyinstaller --noconfirm --clean --windowed --onefile --collect-all PySide6 --name "MemoryManager" memory_manager_app.py || goto :error

echo.
echo Build finished. Find EXEs in .\dist\
echo   - CPUManager.exe
echo   - MemoryManager.exe
echo Copy these to your Windows/Windows Server target machines. No runtime needed there.
echo.
pause
exit /b 0

:error
echo.
echo [FAILED] See the messages above. Common fixes:
echo   - Ensure internet access (for pip and optional Python download)
echo   - Run this script in CMD as a normal or admin user
echo   - If winget install failed, install Python manually from python.org
echo.
pause
exit /b 1