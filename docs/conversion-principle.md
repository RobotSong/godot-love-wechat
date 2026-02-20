# 转换原理

本文档详细说明 Godot 游戏如何转换为微信小程序游戏的核心原理。

## 背景：为什么需要转换

### Godot Web 导出

Godot 引擎支持将游戏导出为 Web 平台，生成以下文件：

| 文件 | 说明 |
|------|------|
| `index.html` | 入口页面 |
| `engine.wasm` | Godot 引擎的 WebAssembly 版本 |
| `engine.js` | JavaScript 胶水代码 |
| `game.pck` | 游戏资源包（脚本、图片、音频等） |

### 微信小游戏环境

微信小游戏基于 WebGL/Canvas 运行，但有以下特殊限制：

1. **没有标准 DOM** - 无法使用常规 HTML 元素
2. **文件系统隔离** - 需要使用微信提供的文件 API
3. **音频限制** - 不支持 Web Audio API 的所有特性
4. **包体限制** - 主包 + 分包总大小限制为 30MB

### 核心挑战

1. **运行时适配** - 需要让 Godot WASM 在微信环境中运行
2. **文件系统桥接** - WASM 内存文件系统 ↔ 微信文件系统
3. **音频兼容** - 使用微信支持的音频接口
4. **分包支持** - 突破 30MB 限制

---

## 转换核心原理

### 1. WASM 模板系统

本项目使用**预编译的微信适配模板**，而不是直接使用 Godot 官方 Web 导出。

```
┌─────────────────────────────────────────────────────────────┐
│                    微信小游戏模板结构                        │
├─────────────────────────────────────────────────────────────┤
│  game.js              # 小游戏入口                          │
│  game.json            # 小游戏配置（方向、分包等）           │
│  project.private.config.json  # 微信开发者工具项目配置       │
│  │                                                          │
│  └── engine/                                                │
│      ├── engine.js      # Godot JS 胶水代码（微信适配版）   │
│      ├── engine.wasm    # Godot WASM 运行时                 │
│      └── godot.zip      # 游戏资源包 (PCK)                  │
│                                                             │
│  └── subpacks/         # 分包目录（可选）                   │
│      └── {name}.zip    # 分包资源                           │
└─────────────────────────────────────────────────────────────┘
```

模板中的关键修改：

1. **engine.js 适配**
   - 移除 DOM 依赖
   - 添加微信 API 桥接
   - 实现文件系统同步接口

2. **音频适配**
   - 使用 ScriptProcessorNode（微信支持的音频接口）
   - 桥接到微信 InnerAudioContext

3. **文件系统同步**
   - 提供 `sdk.syncfs()` 接口
   - WASM 内存 ↔ 微信文件系统双向同步

### 2. PCK 资源包导出

PCK 是 Godot 的专有资源包格式，包含所有游戏资源。

#### 导出命令

```bash
godot --headless --path /path/to/project --export-pack "Web" output.zip
```

#### 代码实现

```python
# app/exporter.py:113-128
def export_pck(self, project_path: str, export_settings: dict, packPath: str):
    settings = self.storage.get("settings.json")
    if settings:
        godot_execute = settings["godot_execute"]
        result = subprocess.run([
            godot_execute,
            "--headless",          # 无头模式，不需要图形界面
            "--path", project_path,
            "--export-pack",       # 导出为 PCK 格式
            export_settings["export_perset"],  # 导出预设名称
            packPath,              # 输出路径
        ])
```

#### 预设修改机制

通过 GDScript 动态修改 `export_presets.cfg`：

```gdscript
# gdscripts/set_preset.gd
# 单参数模式：导出所有资源
config.set_value(section, "export_filter", "all_resources")

# 双参数模式：导出指定资源（分包用）
config.set_value(section, "export_filter", "resources")
config.set_value(section, "export_files", resources)
```

### 3. 文件系统同步机制

微信小游戏环境中，WASM 无法直接访问设备文件系统，需要通过 JavaScript 桥接。

#### 同步流程

```
┌────────────────┐     syncfs()      ┌────────────────┐
│  WASM 内存     │ ◄──────────────► │  微信文件系统   │
│  (MEMFS)       │                   │  (wx.getFileSystemManager) │
└────────────────┘                   └────────────────┘
```

#### JavaScript 桥接接口

在模板的 `engine.js` 中：

```javascript
// 暴露同步接口给 Godot
JavaScriptBridge.get_interface("godotSdk") => {
    syncfs: function(success_cb, error_cb) {
        // 将 MEMFS 数据同步到微信 FS
        // 或从微信 FS 恢复到 MEMFS
    }
}
```

#### 使用时机

- **游戏启动时** - 从微信 FS 恢复存档数据
- **游戏保存时** - 将存档数据同步到微信 FS
- **下载资源后** - 将 CDN 资源同步到可访问位置

### 4. 音频适配

#### 问题

微信小游戏不支持 Web Audio API 的 `AudioContext`，而是使用 `wx.createInnerAudioContext()`。

#### 解决方案

模板中使用 **ScriptProcessorNode**（已弃用但微信支持）进行音频处理：

```
Godot Audio Bus
      │
      ▼
ScriptProcessorNode (微信兼容)
      │
      ▼
Audio Buffer → wx.createInnerAudioContext()
```

---

## 完整转换流程

### 首次导出

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 解压模板                                                  │
│    templates/minigame.2d.full_4.4.zip → export_path/        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 修改配置文件                                              │
│    - game.json: 设置屏幕方向                                 │
│    - project.private.config.json: 设置 appid、项目名等      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 导出 PCK                                                  │
│    调用 Godot --export-pack 生成资源包                       │
│    放入 export_path/engine/godot.zip                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 分包处理（如果配置）                                      │
│    - 内部分包 → export_path/subpacks/{name}.zip            │
│    - CDN 分包 → 上传到 S3 存储                              │
└─────────────────────────────────────────────────────────────┘
```

### 后续导出

```
┌─────────────────────────────────────────────────────────────┐
│ 检测 game.json 是否存在                                      │
│   存在 → 只重新导出 PCK（增量更新）                          │
│   不存在 → 执行完整导出流程                                  │
└─────────────────────────────────────────────────────────────┘
```

### 代码实现

```python
# app/exporter.py:34-86
def export_project(self, export_settings: dict, project: dict):
    # 检查是否已导出
    exported = os.path.exists(
        os.path.join(export_settings["export_path"], "game.json")
    )

    if exported and settings:
        # 增量导出：只更新 PCK
        if export_settings["subpack_config"]:
            self.export_subpack(...)
        else:
            gdscripts.set_export_presets(...)
            self.export_pck(...)
    else:
        # 完整导出：解压模板 + 导出 PCK
        with zipfile.ZipFile(template_path) as zf:
            zf.extractall(export_settings["export_path"])
        self.replace_gamejson(export_settings)
        self.replace_privatejson(project, export_settings)
        # ... 导出 PCK
```

---

## 关键配置文件

### game.json（微信小游戏配置）

```json
{
  "deviceOrientation": "landscape",
  "subpackages": [
    {
      "name": "subpack_name",
      "root": "subpacks/subpack_name/"
    }
  ]
}
```

### project.private.config.json（开发者工具配置）

```json
{
  "projectname": "我的游戏",
  "description": "游戏描述",
  "appid": "wx1234567890"
}
```

### minigame.export.json（本项目导出配置）

```json
{
  "export_path": "minigame",
  "export_template": "minigame.2d.full_4.4.zip",
  "export_perset": "Web",
  "device_orientation": "landscape",
  "appid": "wx1234567890",
  "subpack_config": [
    {
      "name": "main",
      "subpack_type": "main"
    },
    {
      "name": "level2",
      "subpack_type": "inner_subpack",
      "subpack_resource": ["res://levels/level2/"]
    }
  ]
}
```

---

## 总结

Godot 到微信小游戏的转换本质上是一个**打包适配**过程：

1. **不编译代码** - GDScript 已在 PCK 中，由 WASM 运行时解释执行
2. **模板提供运行时** - 预适配的 WASM + JS 环境
3. **工具负责打包** - 生成正确的目录结构和配置文件

这种设计的优点：
- 转换速度快（无需重新编译）
- 支持热更新（只替换 PCK）
- 兼容性好（模板针对微信优化）
