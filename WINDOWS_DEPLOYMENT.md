# Windows系统资源管理工具部署指南

## 🎯 适用系统

本工具专为以下Windows系统设计和优化：

### 桌面版本
- **Windows 10** (版本 1909 及以上)
- **Windows 11** (所有版本)

### 服务器版本
- **Windows Server 2016**
- **Windows Server 2019** 
- **Windows Server 2022**

### 架构支持
- **x64** (Intel/AMD 64位)
- **ARM64** (Windows 11 ARM版本)

## 📋 系统要求

### 最低配置
- **内存**: 4GB RAM
- **存储**: 100MB 可用空间
- **处理器**: 双核 1.6GHz
- **.NET Framework**: 4.7.2 或更高版本

### 推荐配置
- **内存**: 8GB RAM 或更高
- **存储**: 500MB 可用空间
- **处理器**: 四核 2.4GHz 或更高
- **显卡**: 支持硬件加速的显卡

## 🚀 快速部署

### 方式一：使用预编译可执行文件（推荐）

1. **下载发布版本**
   ```
   从GitHub Releases页面下载最新的Windows版本
   文件名: windows-system-tools-{version}.zip
   ```

2. **解压到目标目录**
   ```
   推荐路径: C:\Program Files\SystemResourceTools\
   或: C:\Tools\SystemResourceTools\
   ```

3. **运行工具**
   ```
   双击 CPUManager.exe - CPU资源管理
   双击 MemoryManager.exe - 内存资源管理
   双击 SystemInfo.exe - 系统信息查看
   ```

### 方式二：从源码构建

1. **安装Python 3.8+**
   ```cmd
   # 从 https://python.org 下载并安装
   # 确保勾选 "Add Python to PATH"
   python --version
   ```

2. **克隆项目**
   ```cmd
   git clone <repository-url>
   cd 服务器资源配置提升工具
   ```

3. **运行构建脚本**
   ```cmd
   # 以管理员身份运行命令提示符
   build_windows.bat
   ```

## 🔧 Windows特定配置

### 管理员权限

某些功能需要管理员权限才能正常工作：

1. **右键点击可执行文件**
2. **选择 "以管理员身份运行"**
3. **或设置永久管理员权限：**
   - 右键 → 属性 → 兼容性
   - 勾选 "以管理员身份运行此程序"

### Windows Defender配置

为避免误报，建议添加信任：

1. **打开Windows安全中心**
2. **病毒和威胁防护 → 管理设置**
3. **添加或删除排除项 → 添加排除项**
4. **选择 "文件夹" → 选择工具安装目录**

### 防火墙配置

如果工具需要网络访问：

1. **控制面板 → 系统和安全 → Windows Defender防火墙**
2. **允许应用或功能通过Windows Defender防火墙**
3. **更改设置 → 允许其他应用**
4. **浏览并添加工具可执行文件**

## 📊 Windows Server部署

### Server Core部署

对于Windows Server Core（无GUI）：

1. **使用命令行版本**
   ```cmd
   # 复制到服务器
   copy SystemInfo.exe C:\Tools\
   
   # 运行系统监控
   C:\Tools\SystemInfo.exe --monitor --interval 60
   ```

2. **创建计划任务**
   ```cmd
   schtasks /create /tn "SystemMonitor" /tr "C:\Tools\SystemInfo.exe --monitor" /sc minute /mo 5
   ```

### 远程管理

1. **启用远程桌面**
   ```cmd
   # PowerShell (管理员)
   Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
   ```

2. **通过远程桌面运行GUI工具**

## 🔄 自动化部署

### 使用PowerShell脚本

创建 `deploy.ps1`：

```powershell
# Windows系统资源工具自动部署脚本

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "需要管理员权限，正在重新启动..." -ForegroundColor Red
    Start-Process PowerShell -Verb RunAs "-File '$($MyInvocation.MyCommand.Path)'"
    exit
}

# 创建安装目录
$InstallPath = "C:\Program Files\SystemResourceTools"
New-Item -ItemType Directory -Force -Path $InstallPath

# 下载最新版本
$DownloadUrl = "https://github.com/your-repo/releases/latest/download/windows-system-tools.zip"
$ZipPath = "$env:TEMP\system-tools.zip"
Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath

# 解压文件
Expand-Archive -Path $ZipPath -DestinationPath $InstallPath -Force

# 添加到系统PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($CurrentPath -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallPath", "Machine")
}

# 创建桌面快捷方式
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\CPU管理器.lnk")
$Shortcut.TargetPath = "$InstallPath\CPUManager.exe"
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\内存管理器.lnk")
$Shortcut.TargetPath = "$InstallPath\MemoryManager.exe"
$Shortcut.Save()

Write-Host "部署完成！" -ForegroundColor Green
Write-Host "工具已安装到: $InstallPath" -ForegroundColor Yellow
Write-Host "桌面快捷方式已创建" -ForegroundColor Yellow
```

### 使用组策略部署

1. **创建MSI安装包**（可选）
2. **通过组策略分发到域内计算机**
3. **配置自动更新策略**

## 🛠️ 故障排除

### 常见问题

**问题1: 程序无法启动**
```
解决方案:
1. 检查是否以管理员身份运行
2. 确认Windows版本兼容性
3. 检查.NET Framework版本
4. 查看Windows事件日志
```

**问题2: 权限不足错误**
```
解决方案:
1. 右键 → 以管理员身份运行
2. 检查UAC设置
3. 确认用户账户权限
```

**问题3: 防病毒软件误报**
```
解决方案:
1. 添加到防病毒软件白名单
2. 从官方渠道下载
3. 验证文件数字签名
```

### 日志文件位置

```
应用程序日志: %APPDATA%\SystemResourceTools\logs\
Windows事件日志: 事件查看器 → Windows日志 → 应用程序
系统日志: %WINDIR%\System32\winevt\Logs\
```

## 📞 技术支持

### 收集诊断信息

运行诊断脚本：
```cmd
SystemInfo.exe --diagnostic > diagnostic.txt
```

### 联系支持

- **GitHub Issues**: 报告Bug和功能请求
- **文档**: 查看完整文档和FAQ
- **社区**: 参与讨论和经验分享

## 🔄 更新和维护

### 自动更新

工具支持自动检查更新：
1. 启动时检查新版本
2. 提示用户下载更新
3. 支持静默更新模式

### 手动更新

1. **下载新版本**
2. **停止正在运行的工具**
3. **替换可执行文件**
4. **重新启动工具**

---

**注意**: 本工具专为Windows系统优化，在Windows Server环境中具有最佳性能表现。建议在生产环境部署前进行充分测试。