# Godot Love WeChat 技术文档

## 项目概述

**godot-love-wechat** 是一个基于 Python/NiceGUI 的桌面 GUI 工具，用于将 **Godot 4.x** 游戏项目导出为**微信小程序游戏**格式。

本项目通过以下核心技术实现 Godot 到微信小游戏的转换：

1. **WASM 模板系统** - 使用预编译的 Godot WebAssembly 运行时
2. **PCK 包导出** - 通过 Godot 命令行导出游戏资源
3. **文件系统同步** - 实现 WASM 内存与微信文件系统的桥接
4. **分包机制** - 支持主包、内部分包和 CDN 分包

## 文档索引

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | 系统架构设计，包括模块结构、数据流向、技术栈 |
| [conversion-principle.md](conversion-principle.md) | Godot → 微信小游戏的核心转换原理 |
| [module-guide.md](module-guide.md) | 各模块详细说明与代码解析 |
| [templates.md](templates.md) | 模板系统说明，包括模板类型和自定义方法 |
| [subpack-system.md](subpack-system.md) | 分包系统原理与配置 |
| [development.md](development.md) | 开发环境搭建、调试与构建指南 |

## 快速导航

### 我想了解整体架构
→ 阅读 [architecture.md](architecture.md)

### 我想了解转换原理
→ 阅读 [conversion-principle.md](conversion-principle.md)

### 我想阅读源码
→ 阅读 [module-guide.md](module-guide.md)

### 我想自定义模板
→ 阅读 [templates.md](templates.md)

### 我想配置分包
→ 阅读 [subpack-system.md](subpack-system.md)

### 我想参与开发
→ 阅读 [development.md](development.md)

## 项目状态

该项目目前已停止维护。如需适配新版本，建议使用 AI 辅助进行代码调整。

模板文件维护在独立仓库：https://github.com/yuchenyang1994/godot-minigame-template
