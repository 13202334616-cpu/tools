# Windows系统资源管理工具

> 专为Windows 10/11和Windows Server 2016+设计的系统资源监控与管理工具集

[![Windows Support](https://img.shields.io/badge/Windows-10%2F11%20%7C%20Server%202016%2B-blue?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://github.com/your-repo/actions/workflows/windows-build.yml/badge.svg)](https://github.com/your-repo/actions)

## 🎯 项目概述

本项目是一个专为**Windows和Windows Server**系统设计的综合性资源管理工具集，提供CPU和内存资源的实时监控、动态控制和性能优化功能。通过现代化的图形界面和强大的命令行工具，帮助系统管理员和开发者优化服务器性能。

### 🏢 适用场景

- **Windows Server环境**: 生产服务器资源监控和调优
- **开发测试环境**: 性能测试和压力测试
- **桌面系统**: 个人电脑性能监控和优化
- **企业环境**: 批量部署和集中管理

## 🖥️ 系统支持

### 桌面版本
- ✅ **Windows 10** (版本 1909 及以上)
- ✅ **Windows 11** (所有版本)

### 服务器版本
- ✅ **Windows Server 2016**
- ✅ **Windows Server 2019**
- ✅ **Windows Server 2022**

### 架构支持
- ✅ **x64** (Intel/AMD 64位)
- ✅ **ARM64** (Windows 11 ARM版本)

## 🚀 快速开始

### 方式一：下载预编译版本（推荐）

1. **下载最新版本**
   ```
   访问 GitHub Releases 页面
   下载 windows-system-tools-{version}.zip
   ```

2. **解压并运行**
   ```cmd
   # 解压到任意目录
   unzip windows-system-tools.zip
   
   # 运行工具（可能需要管理员权限）
   CPUManager.exe      # CPU资源管理
   MemoryManager.exe   # 内存资源管理
   SystemInfo.exe      # 系统信息查看
   ```

### 方式二：从源码安装

1. **环境准备**
   ```cmd
   # 安装Python 3.8+（从 https://python.org 下载）
   python --version
   
   # 克隆项目
   git clone <repository-url>
   cd 服务器资源配置提升工具
   ```

2. **安装依赖**
   ```cmd
   # 安装Windows优化的依赖包
   pip install -r requirements.txt
   ```

3. **运行工具**
   ```cmd
   # GUI版本
   python cpu_manager_app.py
   python memory_manager_app.py
   
   # 命令行版本
   python cpu_manager_cli.py 70
   python system_info_cli.py
   ```

## 📊 核心功能

### 🔥 CPU资源管理
- **实时监控**: CPU使用率、温度、频率监控
- **动态控制**: 智能调节CPU使用率到目标值
- **压力测试**: 多线程CPU压力测试
- **性能图表**: 实时CPU使用率曲线

### 💾 内存资源管理
- **内存监控**: 实时内存使用情况
- **智能分配**: 动态内存分配和释放
- **内存优化**: 自动内存清理和优化
- **可视化**: 内存使用趋势图表

### 📈 系统监控仪表盘
- **统一界面**: CPU和内存集成监控
- **实时图表**: 多指标实时可视化
- **进程管理**: 进程监控和管理
- **主题切换**: 深色/浅色主题支持

### 🛠️ Windows特定功能
- **WMI集成**: 深度系统信息获取
- **Windows API**: 系统级资源控制
- **服务监控**: Windows服务状态监控
- **性能计数器**: Windows性能计数器支持

## 📁 项目结构

```
服务器资源配置提升工具/
├── 📱 GUI应用
│   ├── cpu_manager_app.py          # CPU管理器GUI
│   ├── memory_manager_app.py       # 内存管理器GUI
│   ├── cpu_manager_enhanced.py     # 增强版CPU管理器
│   ├── memory_manager_enhanced.py  # 增强版内存管理器
│   └── system_dashboard.py         # 系统监控仪表盘
│
├── 💻 命令行工具
│   ├── cpu_manager_cli.py          # CPU管理器CLI
│   ├── system_info_cli.py          # 系统信息CLI
│   └── windows_system_info.py      # Windows专用系统信息
│
├── 🎨 主题和UI
│   └── theme_manager.py            # 主题管理系统
│
├── 🔧 构建和部署
│   ├── build_windows.bat           # Windows构建脚本
│   ├── requirements.txt            # Python依赖
│   └── .github/workflows/          # GitHub Actions
│
└── 📚 文档
    ├── README.md                   # 项目说明
    ├── WINDOWS_DEPLOYMENT.md       # Windows部署指南
    ├── PROJECT_SUMMARY.md          # 项目总结
    └── IMPROVEMENT_SUGGESTIONS.md  # 改进建议
```

## 🎮 使用示例

### CPU管理示例

```cmd
# 设置CPU使用率为70%
python cpu_manager_cli.py 70

# 运行GUI版本
python cpu_manager_app.py
```

### 内存管理示例

```cmd
# 运行内存管理器
python memory_manager_app.py

# 设置内存使用率为80%
python memory_manager_cli.py 80
```

### 系统监控示例

```cmd
# 查看系统信息
python system_info_cli.py

# 持续监控（每60秒更新）
python system_info_cli.py --monitor --interval 60

# 查看进程信息
python system_info_cli.py --processes

# Windows专用系统信息
python windows_system_info.py --services --processes
```

## 🔧 Windows特定配置

### 管理员权限

某些功能需要管理员权限：

```cmd
# 方法1: 右键 → 以管理员身份运行
# 方法2: 在管理员命令提示符中运行
# 方法3: 设置程序属性 → 兼容性 → 以管理员身份运行
```

### Windows Defender配置

添加信任以避免误报：

1. 打开Windows安全中心
2. 病毒和威胁防护 → 管理设置
3. 添加或删除排除项 → 添加排除项
4. 选择工具安装目录

### 防火墙配置

如需网络功能，请配置防火墙：

1. 控制面板 → Windows Defender防火墙
2. 允许应用或功能通过防火墙
3. 添加工具可执行文件

## 🏗️ 构建可执行文件

### 使用构建脚本

```cmd
# 运行Windows构建脚本
build_windows.bat

# 生成的可执行文件位于 dist/ 目录
dir dist\
```

### 手动构建

```cmd
# 安装PyInstaller
pip install pyinstaller

# 构建CPU管理器
pyinstaller --onefile --windowed --name="CPUManager" cpu_manager_app.py

# 构建内存管理器
pyinstaller --onefile --windowed --name="MemoryManager" memory_manager_app.py

# 构建系统信息工具
pyinstaller --onefile --console --name="SystemInfo" system_info_cli.py
```

## 📋 系统要求

### 最低配置
- **操作系统**: Windows 10 (1909+) 或 Windows Server 2016+
- **内存**: 4GB RAM
- **存储**: 100MB 可用空间
- **处理器**: 双核 1.6GHz
- **.NET Framework**: 4.7.2+

### 推荐配置
- **操作系统**: Windows 11 或 Windows Server 2022
- **内存**: 8GB RAM+
- **存储**: 500MB 可用空间
- **处理器**: 四核 2.4GHz+
- **显卡**: 支持硬件加速

## 🛠️ 故障排除

### 常见问题

**Q: 程序无法启动**
```
A: 1. 检查是否以管理员身份运行
   2. 确认Windows版本兼容性
   3. 检查.NET Framework版本
   4. 查看Windows事件日志
```

**Q: 权限不足错误**
```
A: 1. 右键 → 以管理员身份运行
   2. 检查UAC设置
   3. 确认用户账户权限
```

**Q: 防病毒软件误报**
```
A: 1. 添加到防病毒软件白名单
   2. 从官方渠道下载
   3. 验证文件数字签名
```

### 日志文件

```
应用程序日志: %APPDATA%\SystemResourceTools\logs\
Windows事件日志: 事件查看器 → Windows日志 → 应用程序
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. **Fork项目**
2. **创建功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送分支** (`git push origin feature/AmazingFeature`)
5. **创建Pull Request**

### 开发环境设置

```cmd
# 克隆项目
git clone <your-fork-url>
cd 服务器资源配置提升工具

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **PySide6**: 现代化的Python GUI框架
- **psutil**: 跨平台系统信息库
- **matplotlib**: 数据可视化库
- **Windows API**: 系统级功能支持

## 📞 支持与反馈

- **GitHub Issues**: [报告Bug和功能请求](https://github.com/your-repo/issues)
- **文档**: [完整文档和FAQ](https://github.com/your-repo/wiki)
- **讨论**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**注意**: 本工具专为Windows系统优化，在Windows Server环境中具有最佳性能表现。建议在生产环境部署前进行充分测试。

**Windows Server管理员**: 请参考 [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md) 获取详细的部署指南。