# 音频适配层设计

## 概述

本文档描述 Godot 4.6 Web 音频与微信小游戏的适配方案。

---

## 背景问题

### Godot 4.6 Web 音频限制

| 功能 | 支持状态 |
|------|---------|
| 基础音频播放 | ✅ |
| 低延迟播放（Sample 模式） | ✅ |
| AudioEffects | ❌ |
| 混响效果 | ❌ |
| 多普勒效果 | ❌ |
| 程序式音频生成 | ❌ |
| 位置音频 | ⚠️ 部分工作 |

### 微信音频 API

```javascript
// 微信音频 API
wx.createInnerAudioContext()  // 音频实例
wx.setInnerAudioOption()      // 全局设置
```

---

## 适配架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Godot 游戏层                            │
│  AudioStreamPlayer / AudioStreamPlayer2D / AudioStreamPlayer3D │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     音频适配层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               AudioAdapter (JS)                      │   │
│  │  - 格式转换                                          │   │
│  │  - 音效降级                                          │   │
│  │  - 位置音频计算                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   微信音频 API                               │
│           wx.createInnerAudioContext()                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心实现

### 1. 音频适配器类

```javascript
// engine/audio-adapter.js

class WeChatAudioAdapter {
    constructor() {
        this.audioContexts = new Map();
        this.nextId = 0;
        this.masterVolume = 1.0;
    }

    // 创建音频实例
    create(filePath) {
        const id = this.nextId++;
        const audio = wx.createInnerAudioContext();

        audio.src = filePath;
        audio.volume = 1.0;
        audio.loop = false;

        this.audioContexts.set(id, {
            audio: audio,
            volume: 1.0,
            position: null,  // 3D 位置
            maxDistance: 100
        });

        return id;
    }

    // 播放
    play(id, loop = false) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.audio.loop = loop;
            ctx.audio.play();
        }
    }

    // 停止
    stop(id) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.audio.stop();
        }
    }

    // 暂停
    pause(id) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.audio.pause();
        }
    }

    // 设置音量
    setVolume(id, volume) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.volume = volume;
            ctx.audio.volume = volume * this.masterVolume;
        }
    }

    // 设置主音量
    setMasterVolume(volume) {
        this.masterVolume = volume;
        // 更新所有音频
        for (const [id, ctx] of this.audioContexts) {
            ctx.audio.volume = ctx.volume * this.masterVolume;
        }
    }

    // 销毁
    destroy(id) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.audio.destroy();
            this.audioContexts.delete(id);
        }
    }
}
```

### 2. 位置音频适配

```javascript
// 3D 位置音频降级为 2D
class PositionalAudioAdapter extends WeChatAudioAdapter {
    constructor() {
        super();
        this.listenerPosition = { x: 0, y: 0, z: 0 };
    }

    // 设置监听者位置
    setListenerPosition(x, y, z) {
        this.listenerPosition = { x, y, z };
        this.updateAllVolumes();
    }

    // 设置音源位置
    setSourcePosition(id, x, y, z) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.position = { x, y, z };
            this.updateVolume(id);
        }
    }

    // 计算距离衰减
    calculateVolume(id) {
        const ctx = this.audioContexts.get(id);
        if (!ctx || !ctx.position) return ctx ? ctx.volume : 0;

        const dx = ctx.position.x - this.listenerPosition.x;
        const dy = ctx.position.y - this.listenerPosition.y;
        const dz = ctx.position.z - this.listenerPosition.z;
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

        // 线性衰减
        const attenuation = Math.max(0, 1 - distance / ctx.maxDistance);
        return ctx.volume * attenuation * this.masterVolume;
    }

    // 更新单个音量
    updateVolume(id) {
        const ctx = this.audioContexts.get(id);
        if (ctx) {
            ctx.audio.volume = this.calculateVolume(id);
        }
    }

    // 更新所有音量
    updateAllVolumes() {
        for (const id of this.audioContexts.keys()) {
            this.updateVolume(id);
        }
    }
}
```

### 3. 音效降级策略

```javascript
// 音效降级处理
class AudioEffectFallback {
    constructor() {
        this.supportedEffects = new Set();
    }

    // 检测支持情况
    checkSupport() {
        // 微信不支持 AudioEffects
        // 标记所有效果为不支持
        return {
            reverb: false,
            chorus: false,
            delay: false,
            distortion: false,
            limiter: false,
            panner: false, // 使用位置音频替代
            phaser: false
        };
    }

    // 降级处理
    applyFallback(effectType, params) {
        switch (effectType) {
            case 'reverb':
            case 'chorus':
            case 'delay':
                // 忽略效果，使用原始音频
                console.warn(`Audio effect '${effectType}' not supported on WeChat`);
                return null;

            case 'panner':
                // 降级为位置音频
                return {
                    type: 'positional',
                    params: {
                        position: params.position || { x: 0, y: 0, z: 0 }
                    }
                };

            default:
                return null;
        }
    }
}
```

---

## Godot 端集成

### GDScript 音频管理器

```gdscript
# audio_manager.gd
extends Node

# 音频适配器引用（通过 JS Bridge）
var _js_audio_adapter: JavaScriptObject

func _ready():
    # 获取微信音频适配器
    if OS.has_feature("web"):
        var godot_sdk = JavaScriptBridge.get_interface("godotSdk")
        if godot_sdk and godot_sdk.audioAdapter:
            _js_audio_adapter = godot_sdk.audioAdapter

# 播放 2D 音频
func play_2d(sound_path: String, loop: bool = false) -> int:
    if _js_audio_adapter:
        var id = JavaScriptBridge.create_callback(self, "_on_audio_created")
        _js_audio_adapter.create.call(sound_path, id)
        return id
    return -1

# 播放 3D 音频
func play_3d(sound_path: String, position: Vector3) -> int:
    if _js_audio_adapter:
        var id = _js_audio_adapter.create.call(sound_path)
        _js_audio_adapter.setSourcePosition.call(id, position.x, position.y, position.z)
        _js_audio_adapter.play.call(id, false)
        return id
    return -1

# 更新监听者位置
func update_listener_position(position: Vector3):
    if _js_audio_adapter:
        _js_audio_adapter.setListenerPosition.call(position.x, position.y, position.z)

# 更新音源位置
func update_source_position(audio_id: int, position: Vector3):
    if _js_audio_adapter and audio_id >= 0:
        _js_audio_adapter.setSourcePosition.call(audio_id, position.x, position.y, position.z)

# 停止音频
func stop(audio_id: int):
    if _js_audio_adapter and audio_id >= 0:
        _js_audio_adapter.stop.call(audio_id)

# 销毁音频
func destroy(audio_id: int):
    if _js_audio_adapter and audio_id >= 0:
        _js_audio_adapter.destroy.call(audio_id)
```

---

## 使用示例

### 基础音频播放

```gdscript
# 播放背景音乐
var bgm_id = AudioManager.play_2d("res://audio/bgm.mp3", true)

# 播放音效
var sfx_id = AudioManager.play_2d("res://audio/click.wav")
```

### 位置音频

```gdscript
# 在 3D 场景中播放位置音频
func _process(delta):
    # 更新监听者位置（通常是玩家）
    AudioManager.update_listener_position(player.position)

    # 更新音源位置（例如环境音效）
    AudioManager.update_source_position(ambient_id, fire.position)
```

### 音量控制

```gdscript
# 设置单个音频音量
AudioManager.set_volume(bgm_id, 0.5)

# 设置主音量
AudioManager.set_master_volume(0.8)
```

---

## 性能优化

### 音频池

```javascript
// 预创建音频实例池
class AudioPool {
    constructor(size = 10) {
        this.pool = [];
        for (let i = 0; i < size; i++) {
            this.pool.push({
                audio: wx.createInnerAudioContext(),
                inUse: false
            });
        }
    }

    acquire() {
        for (const item of this.pool) {
            if (!item.inUse) {
                item.inUse = true;
                return item;
            }
        }
        // 池满，创建新实例
        const item = {
            audio: wx.createInnerAudioContext(),
            inUse: true
        };
        this.pool.push(item);
        return item;
    }

    release(item) {
        item.audio.stop();
        item.inUse = false;
    }
}
```

### 资源预加载

```javascript
// 预加载常用音频
async function preloadAudio(paths) {
    const promises = paths.map(path => {
        return new Promise((resolve) => {
            const audio = wx.createInnerAudioContext();
            audio.src = path;
            audio.onCanplay(() => {
                resolve(audio);
            });
            audio.onError((e) => {
                console.error(`Failed to load audio: ${path}`, e);
                resolve(null);
            });
        });
    });
    return Promise.all(promises);
}
```

---

## 已知限制

| 限制 | 说明 | 解决方案 |
|------|------|---------|
| 无 AudioEffects | 不支持混响、延迟等 | 在游戏设计时避免依赖 |
| 无多普勒效果 | 移动音源无多普勒 | 使用音量变化模拟 |
| 位置音频简化 | 仅支持距离衰减 | 使用 GDScript 计算立体声 |
| 同时播放数限制 | 过多音频影响性能 | 使用音频池管理 |

---

## 参考链接

- [微信音频 API](https://developers.weixin.qq.com/minigame/dev/api/media/audio/wx.createInnerAudioContext.html)
- [Godot Web 音频](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html#audio-playback)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
