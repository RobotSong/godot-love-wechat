# 开发指南

本文档说明如何搭建开发环境、调试项目以及构建可执行文件。

---

## 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.12+ | 运行时环境 |
| Godot | 4.4.x | 游戏引擎（用于导出测试） |
| 微信开发者工具 | 最新版 | 小游戏预览和调试 |
| uv 或 pip | - | Python 包管理 |

### 操作系统

- **Windows** - 主要支持平台
- macOS/Linux - 理论可用，但路径和存储位置需要调整

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xxx/godot-love-wechat.git
cd godot-love-wechat
```

### 2. 安装依赖

使用 uv（推荐）：

```bash
# 安装 uv
pip install uv

# 同步依赖
uv sync
```

或使用 pip：

```bash
pip install -r requirements.txt
```

### 3. 运行项目

```bash
# 使用 uv
uv run python main.py

# 或直接运行
python main.py
```

应用将在 `http://localhost:24512` 启动，并打开原生窗口。

---

## 依赖说明

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| nicegui | >=2.9.0 | Web UI 框架 |
| pywebview | >=5.3.2 | 原生窗口 |
| pillow | >=11.0.0 | 图像处理 |
| boto3 | >=1.37.8 | S3 CDN 上传 |

### 开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| pyinstaller | >=6.11.1 | 构建可执行文件 |
| nuitka | >=2.5.9 | 备选编译器 |

---

## 项目配置

### pyproject.toml

```toml
[project]
name = "godot-love-wechat"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.37.8",
    "nicegui>=2.9.0",
    "nuitka>=2.5.9",
    "pillow>=11.0.0",
    "pyinstaller>=6.11.1",
    "pywebview>=5.3.2",
]
```

---

## 调试指南

### 开启调试模式

修改 `main.py`：

```python
ui.run(
    port=24512,
    title="Godot Love Wechat",
    window_size=(1024, 768),
    native=True,
    reload=True,    # 启用热重载
)
```

### 查看日志

NiceGUI 会输出请求日志到控制台。

### 断点调试

使用 VSCode 或 PyCharm 的调试功能：

1. 设置断点
2. 以调试模式运行 `main.py`
3. 在 UI 中触发对应操作

### 常见调试场景

#### 导出流程调试

```python
# 在 exporter.py 中添加日志
def export_project(self, export_settings, project):
    print(f"[DEBUG] export_settings: {export_settings}")
    print(f"[DEBUG] project: {project}")
    # ...
```

#### Godot 脚本调试

```gdscript
# 在 gdscripts 中添加输出
func _init():
    print("[DEBUG] set_preset.gd called with args: ", args)
```

---

## 构建可执行文件

### 使用 PyInstaller

```bash
pyinstaller godot-love-wechat.spec
```

输出文件位于 `dist/` 目录。

### PyInstaller 配置说明

`godot-love-wechat.spec`：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    'main.py',
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),      # 包含静态资源
        ('templates', 'templates'), # 包含模板文件
        ('gdscripts', 'gdscripts'), # 包含 GDScript
    ],
    hiddenimports=[
        'nicegui',
        'pywebview',
        'PIL',
        'boto3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='godot-love-wechat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',  # 应用图标
)
```

### 使用 Nuitka（备选）

```bash
nuitka --standalone --onefile \
    --windows-console-mode=disable \
    --enable-plugin=nicegui \
    --include-data-dir=assets=assets \
    --include-data-dir=templates=templates \
    --include-data-dir=gdscripts=gdscripts \
    --windows-icon-from-ico=assets/logo.ico \
    main.py
```

---

## 目录结构（开发视角）

```
godot-love-wechat/
├── main.py              # 入口，从这里开始调试
├── pyproject.toml       # 依赖配置
├── uv.lock              # 依赖锁定
│
├── app/                 # 核心应用代码
│   ├── exporter.py      # ★ 导出逻辑核心
│   ├── gdscripts.py     # Godot 脚本执行
│   ├── stroge.py        # 本地存储
│   ├── utils.py         # 工具函数
│   ├── layout.py        # 页面布局
│   ├── menu.py          # 导航菜单
│   ├── settings.py      # 设置页面
│   ├── project.py       # 项目详情页
│   └── project_list.py  # 项目列表页
│
├── gdscripts/           # Godot 脚本
│   ├── export_perset.gd # 读取导出预设
│   └── set_preset.gd    # 修改导出预设
│
├── templates/           # 微信小游戏模板
│   ├── template.json    # 模板元数据
│   └── *.zip            # 模板文件
│
├── assets/              # 静态资源
│   ├── logo.svg
│   └── logo.ico
│
└── docs/                # 文档（本目录）
```

---

## 代码风格

### Python

- 使用 4 空格缩进
- 类型注解（部分）
- 函数和变量使用 snake_case
- 类使用 PascalCase

### GDScript

- 遵循 Godot 官方风格指南
- 函数使用 snake_case
- 使用类型注解

---

## 扩展开发

### 添加新模板

1. 将 ZIP 文件放入 `templates/`
2. 更新 `templates/template.json`

### 添加新功能

1. 在 `app/` 下创建新模块
2. 在 `main.py` 添加路由
3. 在 `menu.py` 添加导航项

### 修改导出流程

主要修改 `app/exporter.py` 中的 `Exporter` 类。

---

## 测试

### 手动测试流程

1. 启动应用
2. 配置 Godot 路径和微信工具路径
3. 导入一个 Godot 项目
4. 配置导出设置
5. 执行导出
6. 用微信开发者工具打开预览

### 测试用例

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 首次导出 | 点击导出 | 解压模板，生成 PCK |
| 增量导出 | 再次点击导出 | 只更新 PCK |
| 分包导出 | 配置分包后导出 | 生成多个 ZIP |
| CDN 上传 | 配置 CDN 分包 | 上传成功 |

---

## 常见问题

### Q: 运行时找不到模块

```bash
# 确保在虚拟环境中
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 或使用 uv
uv run python main.py
```

### Q: PyInstaller 打包后资源丢失

检查 `datas` 配置是否包含所有必要目录。

### Q: 窗口不显示

检查 `native=True` 和 pywebview 是否正确安装。

### Q: 导出失败

1. 检查 Godot 路径是否正确
2. 确认项目有 Web 导出预设
3. 查看控制台错误信息

---

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 提交前检查

- [ ] 代码风格一致
- [ ] 功能测试通过
- [ ] 更新相关文档

---

## 相关链接

- [NiceGUI 文档](https://nicegui.io/)
- [Godot 文档](https://docs.godotengine.org/)
- [微信小游戏文档](https://developers.weixin.qq.com/minigame/dev/guide/)
- [模板仓库](https://github.com/yuchenyang1994/godot-minigame-template)
