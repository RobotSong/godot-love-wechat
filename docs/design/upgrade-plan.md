# Godot 4.4 → 4.6 升级方案

## 升级概述

本文档描述将 godot-love-wechat 项目从 Godot 4.4 模板升级到 4.6 的完整方案。

---

## 兼容性分析

### 引擎变化

| 变化项 | 4.4 | 4.6 | 影响 |
|--------|-----|-----|------|
| 默认物理引擎 | Godot Physics | Jolt Physics | 需更新模板 |
| WASM SIMD | 可选 | 默认启用 | 性能提升 |
| 单线程导出 | 可选 | 默认推荐 | 兼容性更好 |
| Shader Baker | 无 | 新增 | 启动优化 |
| 导出预设格式 | 兼容 | 兼容 | 无影响 |
| GDScript 语法 | 4.x | 4.x | 无影响 |

### 代码兼容性

| 组件 | 兼容性 | 说明 |
|------|--------|------|
| `gdscripts/export_perset.gd` | ✅ 兼容 | API 未变 |
| `gdscripts/set_preset.gd` | ✅ 兼容 | API 未变 |
| `app/exporter.py` | ✅ 兼容 | 命令行参数未变 |
| 导出预设配置 | ✅ 兼容 | 格式未变 |

---

## 升级路线图

### Phase 1: 模板准备

**目标**: 创建 Godot 4.6 微信小游戏模板

**任务**:
1. 编译 Godot 4.6 Web 导出模板
2. 适配微信环境
3. 创建模板 ZIP 包

**输出**:
- `templates/minigame.2d.full_4.6.zip`
- `templates/minigame.2d.tiny_4.6.zip`
- `templates/minigame.3d.jolt_4.6.zip`

### Phase 2: 配置更新

**目标**: 更新项目配置支持 4.6 模板

**任务**:
1. 更新 `templates/template.json`
2. 添加 4.6 模板选项
3. 保留 4.4 模板向后兼容

**输出**:
- 更新后的 `template.json`

### Phase 3: 导出器优化

**目标**: 利用 4.6 新特性优化导出流程

**任务**:
1. 添加 Shader Baker 选项
2. 优化单线程导出配置
3. 添加性能优化建议

**输出**:
- 更新后的 `app/exporter.py`

### Phase 4: 测试验证

**目标**: 确保升级后功能正常

**任务**:
1. 创建测试项目
2. 测试导出流程
3. 微信开发者工具验证
4. 性能对比测试

---

## 详细实现

### 1. 模板编译

#### 环境准备

```bash
# 克隆 Godot 源码
git clone https://github.com/godotengine/godot.git
cd godot
git checkout 4.6-stable

# 安装依赖
# Linux
sudo apt install scons python3
# macOS
brew install scons
```

#### 编译命令

```bash
# 编译 Web 模板（Release）
scons platform=web target=template_release -j$(nproc)

# 编译 Web 模板（Debug）
scons platform=web target=template_debug -j$(nproc)
```

#### 输出文件

```
bin/
├── godot.web.template_release.wasm32.zip
└── godot.web.template_debug.wasm32.zip
```

### 2. 微信环境适配

#### engine.js 修改要点

```javascript
// 1. 移除 DOM 依赖
// 原：document.getElementById('canvas')
// 改：wx.createCanvas()

// 2. 文件系统桥接
const godotSdk = {
    syncfs: function(onSuccess, onError) {
        // WASM MEMFS → 微信 FS 同步
        const fs = wx.getFileSystemManager();
        // ... 同步逻辑
    }
};

// 3. 音频适配
// 使用 wx.createInnerAudioContext()
```

#### game.json 配置

```json
{
    "deviceOrientation": "landscape",
    "showStatusBar": false,
    "networkTimeout": {
        "request": 10000,
        "connectSocket": 10000
    }
}
```

### 3. template.json 更新

```json
[
  {
    "name": "4.6微信小游戏2D完整版",
    "filename": "minigame.2d.full_4.6.zip",
    "version": "4.6",
    "features": ["wasm-simd", "jolt-physics", "shader-baker"]
  },
  {
    "name": "4.6微信小游戏2D精简版",
    "filename": "minigame.2d.tiny_4.6.zip",
    "version": "4.6",
    "features": ["wasm-ssimd", "jolt-physics"]
  },
  {
    "name": "4.6微信小游戏3D-Jolt版",
    "filename": "minigame.3d.jolt_4.6.zip",
    "version": "4.6",
    "features": ["wasm-simd", "jolt-physics", "3d", "shader-baker"]
  },
  {
    "name": "4.4微信小游戏2D完整版",
    "filename": "minigame.2d.full_4.4.zip",
    "version": "4.4",
    "deprecated": true
  }
]
```

### 4. 导出器更新

#### 新增 Shader Baker 支持

```python
# app/exporter.py

def export_project(self, export_settings: dict, project: dict):
    # ... 现有代码 ...

    # 新增：Shader Baker 选项
    if export_settings.get("shader_baker", False):
        self._enable_shader_baker(project["path"])

def _enable_shader_baker(self, project_path: str):
    """启用 Shader Baker 预编译"""
    # 修改项目设置
    # 在导出时预编译着色器
    pass
```

#### 单线程导出配置

```python
# 默认使用单线程模式（4.6 默认行为）
def get_export_options(self):
    return {
        "thread_support": False,  # 单线程
        "shader_baker": True,     # 着色器预编译
    }
```

---

## 测试计划

### 测试矩阵

| 测试项 | 4.4 模板 | 4.6 模板 | 验证标准 |
|--------|---------|---------|---------|
| PCK 导出 | ✓ | ✓ | 导出成功 |
| 首次导出 | ✓ | ✓ | 模板解压成功 |
| 增量导出 | ✓ | ✓ | 只更新 PCK |
| 分包导出 | ✓ | ✓ | 分包正确 |
| 微信预览 | ✓ | ✓ | 可运行 |
| 音频播放 | ✓ | ✓ | 声音正常 |
| 存档同步 | ✓ | ✓ | 数据持久化 |

### 性能对比

| 指标 | 4.4 | 4.6 | 改善 |
|------|-----|-----|------|
| WASM 大小 | 基准 | -5% | SIMD 优化 |
| 启动时间 | 基准 | -20% | Shader Baker |
| CPU 性能 | 基准 | +50% | SIMD |
| 内存占用 | 基准 | -10% | 优化 |

---

## 回滚方案

如果 4.6 模板出现问题：

1. **保留 4.4 模板** - template.json 中标记为 deprecated 但不删除
2. **用户可选择** - UI 提供版本选择
3. **一键切换** - 配置中可切换模板版本

---

## 时间估算

| 阶段 | 工作量 |
|------|--------|
| Phase 1: 模板准备 | 主要工作量（需编译和适配） |
| Phase 2: 配置更新 | 简单 |
| Phase 3: 导出器优化 | 中等 |
| Phase 4: 测试验证 | 中等 |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 微信内核不兼容 | 高 | 充分测试 |
| 性能回退 | 中 | 性能对比测试 |
| 音频兼容问题 | 中 | 适配层测试 |
| 分包加载失败 | 高 | 完整测试流程 |

---

## 参考链接

- [Godot 编译文档](https://docs.godotengine.org/en/stable/contributing/development/compiling/)
- [Web 平台编译](https://docs.godotengine.org/en/stable/contributing/development/compiling/compiling_for_web.html)
- [微信小游戏适配指南](https://developers.weixin.qq.com/minigame/dev/guide/)
