# Godot 4.6 微信小游戏设计文档

## 概述

本目录包含 godot-love-wechat 项目升级到 Godot 4.6 的完整设计文档。

## 文档索引

| 文档 | 说明 |
|------|------|
| [godot-4.6-spec.md](godot-4.6-spec.md) | Godot 4.6 Web 导出技术规范 |
| [wechat-minigame-2025.md](wechat-minigame-2025.md) | 微信小游戏 2025-2026 技术规范 |
| [upgrade-plan.md](upgrade-plan.md) | 4.4 → 4.6 升级实现方案 |
| [template-4.6.md](template-4.6.md) | Godot 4.6 模板开发指南 |
| [audio-adapter.md](audio-adapter.md) | 音频适配层设计 |

## 技术背景

### Godot 4.6 关键特性

| 特性 | 说明 |
|------|------|
| WASM SIMD | 默认启用，CPU 性能提升 1.5x-2x |
| 单线程导出 | 默认推荐，更好的平台兼容性 |
| Jolt 物理 | 默认物理引擎 |
| Shader Baker | 着色器预编译，启动时间缩短 20x |

### 微信小游戏限制

| 限制项 | 数值 |
|--------|------|
| 主包 | 4 MB |
| 本地总包 | 30 MB |
| CDN 包 | 无限制 |

## 快速导航

### 我想了解 Godot 4.6 的变化
→ 阅读 [godot-4.6-spec.md](godot-4.6-spec.md)

### 我想了解微信小游戏的技术要求
→ 阅读 [wechat-minigame-2025.md](wechat-minigame-2025.md)

### 我想升级现有项目
→ 阅读 [upgrade-plan.md](upgrade-plan.md)

### 我想开发新模板
→ 阅读 [template-4.6.md](template-4.6.md)

### 我想解决音频兼容问题
→ 阅读 [audio-adapter.md](audio-adapter.md)

## 参考资料

- [Godot 官方文档](https://docs.godotengine.org/)
- [微信小游戏开发文档](https://developers.weixin.qq.com/minigame/dev/guide/)
- [WebAssembly 规范](https://webassembly.org/)
