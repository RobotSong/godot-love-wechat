# 模板系统

本文档详细说明微信小游戏模板的结构、类型和自定义方法。

---

## 模板概述

模板是预编译的微信小游戏运行时环境，包含：

1. **Godot WASM 运行时** - 针对微信环境优化的 WebAssembly 二进制
2. **JavaScript 胶水代码** - WASM 与微信 API 的桥接层
3. **配置文件** - 微信小游戏所需的配置文件

---

## 模板类型

项目提供以下模板（定义于 `templates/template.json`）：

| 模板名称 | 文件名 | 适用场景 |
|---------|--------|---------|
| 2D 完整版 | `minigame.2d.full_4.4.zip` | 2D 游戏，需要完整 GUI 组件 |
| 2D 精简版 | `minigame.2d.tiny_4.4.zip` | 2D 游戏，追求更小体积 |
| 3D Jolt 版 | `minigame.3d.jolt_4.4.zip` | 3D 游戏，使用 Jolt 物理引擎 |
| 3D 老物理版 | `minigame.3d.gp.zip` | 3D 游戏，使用 Godot Physics |

### 模板选择建议

| 游戏类型 | 推荐模板 | 说明 |
|---------|---------|------|
| 纯 2D 游戏 | 2D 精简版 | 体积最小，无高级 GUI |
| 2D + 复杂 UI | 2D 完整版 | 包含完整 Control 节点支持 |
| 3D 游戏（新项目） | 3D Jolt 版 | Jolt 物理更稳定 |
| 3D 游戏（旧项目） | 3D 老物理版 | 兼容旧物理行为 |

---

## 模板结构

解压后的目录结构：

```
minigame/
├── game.js                    # 小游戏入口脚本
├── game.json                  # 小游戏配置
├── project.private.config.json # 开发者工具配置
│
└── engine/
    ├── engine.js              # Godot JS 胶水代码（微信适配版）
    ├── engine.wasm            # Godot WASM 运行时
    ├── engine.wasm.code       # WASM 代码段（可选）
    └── godot.zip              # 游戏资源包（导出时生成）
```

### 核心文件说明

#### game.js

小游戏入口，负责：
- 初始化 WebGL 上下文
- 加载 WASM 模块
- 提供微信 API 桥接

```javascript
// 简化结构示例
const godot = require('./engine/engine.js');

GameGlobal.godot = godot;

// 初始化
godot({
    canvas: canvas,
    locateFile: (path) => `engine/${path}`,
    // 微信适配...
}).then(() => {
    // 加载游戏
    godot.loadPck('engine/godot.zip');
});
```

#### game.json

微信小游戏配置：

```json
{
    "deviceOrientation": "landscape",
    "showStatusBar": false,
    "networkTimeout": {
        "request": 10000,
        "connectSocket": 10000
    },
    "subpackages": []
}
```

#### engine.js

Godot JavaScript 胶水代码，关键修改：

1. **DOM 替换** - 用微信 Canvas API 替换 DOM 操作
2. **文件系统** - 实现微信文件系统桥接
3. **音频适配** - 使用 ScriptProcessor + InnerAudioContext
4. **网络请求** - 使用 wx.request 替换 fetch

---

## 模板来源

模板文件维护在独立仓库：

**https://github.com/yuchenyang1994/godot-minigame-template**

### 模板构建原理

模板基于 Godot 官方 Web 导出，进行以下修改：

#### 1. 编译选项

```bash
# 编译 Godot 为 Web 平台
scons platform=web target=template_release

# 启用 ScriptProcessor 音频（微信兼容）
scons platform=web audio_driver=scriptprocessor
```

#### 2. JavaScript 适配

修改 `engine.js` 中的平台相关代码：

```javascript
// 原始：浏览器 DOM
document.getElementById('canvas')

// 适配：微信 Canvas
wx.createCanvas()
```

```javascript
// 原始：Web Audio
new AudioContext()

// 适配：微信音频
wx.createInnerAudioContext()
```

#### 3. 文件系统桥接

```javascript
// MEMFS → 微信 FS 同步
function syncfs() {
    const fs = wx.getFileSystemManager();
    // 读取 WASM 内存中的文件
    const data = MEMFS.readFile('/save/game.dat');
    // 写入微信文件系统
    fs.writeFileSync(`${wx.env.USER_DATA_PATH}/save/game.dat`, data);
}
```

---

## 自定义模板

### 何时需要自定义

- 需要 Godot 的新版本特性
- 需要特定的模块编译选项
- 需要额外的微信 API 桥接

### 自定义步骤

#### 1. 编译 Godot WASM

```bash
# 克隆 Godot 源码
git clone https://github.com/godotengine/godot.git
cd godot

# 编译 Web 目标
scons platform=web target=template_release \
    -j$(nproc)

# 输出文件
# bin/godot.web.template_release.wasm32.zip
```

#### 2. 修改 JavaScript 胶水

参考 godot-minigame-template 仓库的适配代码。

#### 3. 打包模板

```bash
# 创建模板目录结构
mkdir minigame.custom
cp game.js game.json project.private.config.json minigame.custom/
cp engine.js engine.wasm minigame.custom/engine/

# 打包
cd minigame.custom
zip -r ../minigame.custom.zip .
```

#### 4. 添加到项目

1. 将 ZIP 文件放入 `templates/` 目录
2. 更新 `templates/template.json`：

```json
[
  {
    "name": "自定义模板",
    "filename": "minigame.custom.zip"
  }
]
```

---

## 模板版本兼容性

| 模板版本 | Godot 版本 | 兼容性说明 |
|---------|-----------|-----------|
| 4.4 | Godot 4.4.x | 当前主版本 |
| 4.x | Godot 4.0-4.3 | 可能需要调整 |

### 版本不匹配问题

如果使用不匹配的 Godot 版本导出，可能出现：

- PCK 格式不兼容
- 脚本 API 差异
- 运行时崩溃

**建议**：使用模板对应的 Godot 版本进行开发。

---

## 模板文件管理

### 获取官方模板

```bash
# 从模板仓库下载
git clone https://github.com/yuchenyang1994/godot-minigame-template.git

# 复制到项目
cp godot-minigame-template/templates/*.zip godot-love-wechat/templates/
```

### 模板配置加载

```python
# app/exporter.py
def get_tempalte_json(self):
    with open("./templates/template.json", "rb") as f:
        templates = json.loads(f.read())
    return templates
```

UI 中显示模板选择列表时，会调用此方法获取可用模板。

---

## 总结

| 要点 | 说明 |
|------|------|
| 模板作用 | 提供微信适配的 Godot 运行时 |
| 选择依据 | 2D/3D、完整/精简、物理引擎 |
| 自定义时机 | 需要新版本或特殊功能 |
| 版本匹配 | 模板版本需与 Godot 版本对应 |
