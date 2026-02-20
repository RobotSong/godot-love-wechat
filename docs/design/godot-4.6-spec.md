# Godot 4.6 Web 导出技术规范

## 版本概述

Godot 4.6 于 2026 年 1 月正式发布，是 Godot 4.x 系列的重要功能版本。

### 主要更新

| 功能 | 说明 |
|------|------|
| Jolt 物理引擎 | 默认启用（4.4 起为实验性） |
| 屏幕空间反射 | SSR 算法重写，效果提升 |
| LibGodot | 新增库模式，可嵌入其他应用 |
| 现代主题 | 新编辑器 UI 主题 |
| OpenXR 1.1 | 原生支持 |
| D3D12 | Windows 默认渲染后端 |

---

## Web 导出技术栈

### 渲染后端

| 后端 | 支持状态 | 说明 |
|------|---------|------|
| WebGL 2.0 | ✅ 支持 | 兼容渲染模式 |
| WebGPU | ❌ 不支持 | 计划中，Forward+/Mobile 需要 |
| Forward+ | ❌ Web 不支持 | 需要 WebGPU |
| Mobile | ❌ Web 不支持 | 需要 WebGPU |

### 编译目标

```
WebAssembly (WASM)
├── 默认启用 SIMD
├── 单线程模式（默认）
├── 多线程模式（可选，需 CORS 头）
└── 使用 Emscripten 工具链
```

---

## WASM SIMD 性能分析

### 技术背景

SIMD（Single Instruction, Multiple Data）允许 CPU 并行处理多个数据，显著提升计算密集型任务性能。

### 性能基准测试

| 场景 | 无 SIMD | 有 SIMD | 提升比例 |
|------|---------|---------|---------|
| Jolt 物理压力测试（Firefox） | 100% | 200% | 2x |
| Jolt 物理极限测试（Firefox） | 100% | 1017% | 10x* |
| Jolt 物理压力测试（Chromium） | 100% | 137% | 1.37x |
| Jolt 物理极限测试（Chromium） | 100% | 1417% | 14x* |

> *注：极限测试进入"死亡螺旋"时帧率会骤降至个位数，SIMD 版本更能抵抗帧率下降。实际游戏场景提升约 1.5x-2x。

### 浏览器兼容性

| 浏览器 | SIMD 支持 |
|--------|----------|
| Chrome 91+ | ✅ |
| Firefox 89+ | ✅ |
| Safari 16.4+ | ✅ |
| Edge 91+ | ✅ |
| 微信内核 | ✅ |

### 启用方式

Godot 4.5+ 编译时默认启用：

```bash
scons platform=web target=template_release
# SIMD 默认启用
```

---

## 单线程 vs 多线程导出

### 对比

| 特性 | 单线程 | 多线程 |
|------|--------|--------|
| 默认状态 | ✅ 默认 | 可选 |
| 性能 | 较低 | 较高 |
| 服务器配置 | 无特殊要求 | 需 CORS 头 |
| 跨域隔离 | 不需要 | 需要 |
| 第三方集成 | 无限制 | 受限 |
| itch.io 兼容 | ✅ | ⚠️ 复杂 |
| 微信兼容 | ✅ | ⚠️ 受限 |

### 推荐

**微信小游戏推荐使用单线程模式**，原因：

1. 无需配置 Cross-Origin-Isolation 头
2. 兼容性更好
3. 微信环境对 SharedArrayBuffer 有限制

### 导出配置

```python
# Godot 导出预设
{
    "thread_support": false,  # 单线程（默认）
    # 或
    "thread_support": true,   # 多线程
}
```

---

## Shader Baker

### 功能说明

Shader Baker 在导出时预编译着色器，显著减少首次运行时的编译等待时间。

### 性能提升

| 平台 | 启动时间缩短 |
|------|-------------|
| Windows + D3D12 | 最高 20x |
| macOS + Metal | 最高 20x |
| Web + WebGL 2.0 | 显著（视着色器复杂度） |

### 使用方式

在导出设置中启用：

```
Export → Web → Shader Baker → Enable
```

### 注意事项

- 增加导出时间（需要预编译）
- 增加包体大小（存储编译后的着色器）
- 首次运行性能提升明显

---

## 音频限制

### Web 平台音频特性

自 Godot 4.3 起，Web 平台使用 Web Audio API：

| 功能 | 支持状态 |
|------|---------|
| 基础音频播放 | ✅ |
| 低延迟播放 | ✅ |
| AudioEffects | ❌ 不支持 |
| 混响效果 | ❌ 不支持 |
| 多普勒效果 | ❌ 不支持 |
| 程序式音频生成 | ❌ 不支持 |
| 位置音频 | ⚠️ 部分工作 |

### 音频模式

```python
# 项目设置
Audio > General > Default Playback Type
├── Sample (默认) - 低延迟，功能受限
└── Stream - 高延迟，完整功能
```

### 微信适配建议

```javascript
// 使用 wx.createInnerAudioContext() 替代
// 不依赖 AudioEffects
// 位置音频降级为 2D
```

---

## C# Web 导出状态

### 当前状态

**Godot 4.x 不支持 C# Web 导出**

- 原因：从 Mono 迁移到 .NET 运行时后，WASM 支持尚未完成
- 状态：原型/实验性阶段
- 时间线：无明确发布日期

### 解决方案

| 方案 | 说明 |
|------|------|
| 使用 GDScript | 推荐方案 |
| 使用 Godot 3 | 需要 C# 时 |
| 等待官方支持 | 时间不确定 |

---

## 已知限制与解决方案

### 1. 包体过大

**问题**：GDScript 导出包体 > 3MB

**解决方案**：
- 精简导出模板（禁用未使用功能）
- 使用 VRAM 压缩
- 分包加载

### 2. Safari 兼容性

**问题**：Safari 对 WebGL 2.0 支持存在多个问题

**解决方案**：
- 推荐使用 Chromium 或 Firefox
- 添加功能降级

### 3. 移动端性能

**问题**：WASM 性能低于原生代码

**解决方案**：
- 使用 WASM SIMD
- 优化资源大小
- 降低画质设置

### 4. 首屏加载慢

**问题**：WASM 模块初始化耗时

**解决方案**：
- 启用 Shader Baker
- 流式加载
- CDN 加速

---

## 参考链接

- [Godot Web 导出文档](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_web.html)
- [WASM SIMD 性能提升](https://godotengine.org/article/upcoming-serious-web-performance-boost/)
- [Godot 4.5 发布说明](https://www.oschina.net/news/372546/godot-4-5-released)
- [Godot 4.6 发布](https://www.nxrte.com/zixun/64512.html)
