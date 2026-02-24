# Windows 镜像管理器

Windows全局镜像管理工具，单EXE文件，用于管理Git、Pip、HuggingFace镜像源。

## 功能特性

- **三种镜像源管理**：Git、Pip、HuggingFace
- **一键切换**：快速切换镜像源
- **连接测试**：每个镜像源独立测试按钮，显示延时
- **自动检测**：自动检测当前系统配置状态
- **智能修复**：自动清理用户级和虚拟环境配置，统一为全局配置
- **即时生效**：配置后立即生效，无需重启终端
- **重启持久**：配置写入全局，重启电脑不丢失

## 系统要求

- Windows 10/11
- 无需安装Python（打包为单EXE）

## 使用方法

1. 运行 `Windows镜像管理器.exe`
2. 选择各镜像源的镜像
3. 点击"测试"验证连接
4. 点击"应用配置"生效

## 配置说明

- 配置文件：`mirrors.json`（与EXE同目录）
- 支持自定义添加镜像源

## 镜像列表

### Git
- 原始（官方）
- 阿里云
- 腾讯云
- 华为云

### Pip
- 原始（官方）
- 阿里云
- 清华
- 腾讯云
- 华为云

### HuggingFace
- 原始（官方）
- 镜像1

## 技术栈

- Python 3.13
- CustomTkinter 5.2.2（UI框架）
- PyInstaller（打包）

## 开发

```bash
# 安装依赖
pip install customtkinter pyinstaller

# 开发运行
python mirror_manager/app.py

# 打包EXE
pyinstaller --onefile --windowed --name "Windows镜像管理器" mirror_manager/app.py
```

## 版本历史

见 [CHANGELOG.md](CHANGELOG.md)
