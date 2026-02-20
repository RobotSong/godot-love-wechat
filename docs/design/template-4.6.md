# Godot 4.6 模板开发指南

## 概述

本文档描述如何为 Godot 4.6 创建微信小游戏导出模板。

---

## 模板结构

### 目录结构

```
minigame/
├── game.js                    # 小游戏入口
├── game.json                  # 小游戏配置
├── project.private.config.json # 开发者工具配置
│
└── engine/
    ├── engine.js              # Godot JS 胶水代码（微信适配版）
    ├── engine.wasm            # Godot WASM 运行时（含 SIMD）
    └── godot.zip              # 游戏资源包（导出时生成）
```

### 文件说明

| 文件 | 来源 | 说明 |
|------|------|------|
| game.js | 自定义 | 小游戏启动入口 |
| game.json | 自定义 | 微信配置 |
| project.private.config.json | 自定义 | 开发者工具配置 |
| engine.js | Godot + 适配 | JS 胶水代码 |
| engine.wasm | Godot 编译 | WASM 二进制 |

---

## 编译流程

### 1. 环境准备

```bash
# 克隆 Godot 4.6 源码
git clone https://github.com/godotengine/godot.git
cd godot
git checkout 4.6-stable

# 安装 Emscripten（Web 编译必需）
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh

# 安装 SCons
pip install scons
```

### 2. 编译 Web 模板

```bash
# 设置 Emscripten 环境
source /path/to/emsdk/emsdk_env.sh

# 编译 Release 模板
scons platform=web target=template_release -j$(nproc)

# 编译 Debug 模板（可选）
scons platform=web target=template_debug -j$(nproc)
```

### 3. 输出文件

```
bin/
├── godot.web.template_release.wasm32/
│   ├── engine.js
│   ├── engine.wasm
│   ├── engine.audio.worklet.js
│   └── index.html
└── godot.web.template_debug.wasm32/
    └── ...
```

---

## 微信适配

### engine.js 修改

#### 1. Canvas 适配

```javascript
// 原始代码（浏览器）
const canvas = document.getElementById('canvas');

// 微信适配
const canvas = wx.createCanvas();
```

#### 2. WebGL 上下文

```javascript
// 原始代码
const gl = canvas.getContext('webgl2');

// 微信适配（基本兼容）
const gl = canvas.getContext('webgl2');
// 注：微信支持 WebGL 2.0
```

#### 3. 文件系统桥接

```javascript
// 微信文件系统适配
const WeChatFS = {
    syncfs: function(onSuccess, onError) {
        try {
            // 从 MEMFS 读取文件
            const files = MEMFS.getAllFiles();

            // 写入微信文件系统
            const wxFS = wx.getFileSystemManager();
            const basePath = wx.env.USER_DATA_PATH;

            for (const file of files) {
                const data = MEMFS.readFile(file.path);
                wxFS.writeFileSync(
                    basePath + '/' + file.path,
                    data
                );
            }

            if (onSuccess) onSuccess();
        } catch (e) {
            if (onError) onError(e);
        }
    },

    loadFromWX: function(path) {
        const wxFS = wx.getFileSystemManager();
        const basePath = wx.env.USER_DATA_PATH;
        const data = wxFS.readFileSync(basePath + '/' + path);
        MEMFS.writeFile(path, data);
    }
};

// 暴露给 Godot
JavaScriptBridge.set_interface('godotSdk', WeChatFS);
```

#### 4. 音频适配

```javascript
// 微信音频适配
class WeChatAudio {
    constructor() {
        this.contexts = new Map();
    }

    createBuffer(sampleRate, channels, duration) {
        return {
            sampleRate,
            channels,
            duration,
            buffer: new Float32Array(sampleRate * duration * channels)
        };
    }

    play(buffer, loop = false) {
        const audio = wx.createInnerAudioContext();
        // ... 设置音频数据
        audio.loop = loop;
        audio.play();
        this.contexts.set(audio);
        return audio;
    }

    stop(audio) {
        audio.stop();
        audio.destroy();
        this.contexts.delete(audio);
    }
}
```

#### 5. 网络请求

```javascript
// 原始代码
fetch(url).then(response => response.arrayBuffer());

// 微信适配
wx.request({
    url: url,
    responseType: 'arraybuffer',
    success: (res) => {
        // res.data 为 ArrayBuffer
    }
});
```

---

## 模板类型

### 2D 完整版 (full)

包含所有 Godot 功能：

```
功能模块：
├── 2D 渲染
├── GUI 系统（完整）
├── 动画系统
├── 物理引擎（Jolt 2D）
├── 音频系统
├── 网络模块
└── 文件系统
```

### 2D 精简版 (tiny)

移除高级 GUI 功能，减小体积：

```
功能模块：
├── 2D 渲染
├── GUI 系统（基础）
├── 动画系统
├── 物理引擎（Jolt 2D）
├── 音频系统
└── 文件系统

移除：
├── 高级 Control 节点
├──富文本编辑器
└── 复杂样式系统
```

### 3D Jolt 版

支持 3D 渲染和 Jolt 物理：

```
功能模块：
├── 2D/3D 渲染
├── GUI 系统
├── 动画系统
├── 物理引擎（Jolt 3D）
├── 音频系统
├── 网络模块
└── 文件系统
```

---

## 打包流程

### 创建模板

```bash
# 创建模板目录
mkdir -p minigame.2d.full_4.6/engine

# 复制编译输出
cp bin/godot.web.template_release.wasm32/engine.js minigame.2d.full_4.6/engine/
cp bin/godot.web.template_release.wasm32/engine.wasm minigame.2d.full_4.6/engine/

# 创建配置文件
# game.js - 小游戏入口
# game.json - 微信配置
# project.private.config.json - 开发者工具配置

# 打包
cd minigame.2d.full_4.6
zip -r ../minigame.2d.full_4.6.zip .
```

### game.js 模板

```javascript
// game.js - 微信小游戏入口
const godot = require('./engine/engine.js');

GameGlobal.godot = godot;

// 初始化配置
const config = {
    canvas: canvas,
    locateFile: (path) => {
        if (path.endsWith('.wasm')) {
            return 'engine/engine.wasm';
        }
        if (path.endsWith('.js')) {
            return 'engine/engine.js';
        }
        return path;
    },
    // 微信适配
    onRuntimeInitialized: () => {
        console.log('Godot runtime initialized');

        // 加载游戏资源
        godot.loadPck('engine/godot.zip').then(() => {
            console.log('Game loaded');
        });
    }
};

// 启动引擎
godot(config);
```

### game.json 模板

```json
{
    "deviceOrientation": "landscape",
    "showStatusBar": false,
    "networkTimeout": {
        "request": 10000,
        "connectSocket": 10000,
        "uploadFile": 60000,
        "downloadFile": 60000
    },
    "subpackages": []
}
```

### project.private.config.json 模板

```json
{
    "projectname": "GodotGame",
    "description": "A Godot game",
    "appid": "",
    "setting": {
        "urlCheck": false,
        "es6": true,
        "postcss": true,
        "minified": true
    }
}
```

---

## 优化建议

### 1. 减小 WASM 体积

```bash
# 编译时禁用未使用模块
scons platform=web target=template_release \
    module_freetype_enabled=no \
    module_svg_enabled=no \
    module_webp_enabled=no \
    -j$(nproc)
```

### 2. 启用压缩

```bash
# 使用 Brotli 压缩
brotli -Z engine.wasm
```

### 3. 分离资源

```
engine/
├── engine.js
├── engine.wasm      # 核心引擎
├── engine.data      # 数据文件（可选）
└── godot.zip        # 游戏资源
```

---

## 调试技巧

### 查看日志

```javascript
// 在 engine.js 中添加
console.log = function(...args) {
    wx.getLogManager().log(args.join(' '));
};
```

### 性能分析

```javascript
// 使用微信性能面板
wx.setPreferredFramesPerSecond(60);
const performance = wx.getPerformance();
```

### 内存监控

```javascript
// 监控内存使用
setInterval(() => {
    const memory = wx.getPerformance().memory;
    console.log(`Memory: ${memory.used / 1024 / 1024}MB`);
}, 5000);
```

---

## 参考链接

- [Godot Web 编译文档](https://docs.godotengine.org/en/stable/contributing/development/compiling/compiling_for_web.html)
- [Emscripten 文档](https://emscripten.org/)
- [微信小游戏 API](https://developers.weixin.qq.com/minigame/dev/api/)
- [WebAssembly SIMD](https://webassembly.org/features/simd/)
