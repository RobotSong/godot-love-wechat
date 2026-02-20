# 模块详解

本文档详细解析项目的各个模块及其实现细节。

---

## 1. 入口模块 - main.py

### 功能

应用入口，定义路由和启动配置。

### 源码解析

```python
from nicegui import ui, app
from app.layout import layout
from app.settings import settings
from app.project_list import project_list
from app.project import project

# 静态资源目录
static_folder = Path(__file__).parent / "assets"
app.add_static_files("/assets", str(static_folder))

# 隐藏滚动条
ui.add_css("::-webkit-scrollbar { display: none; }")

# 路由定义
@ui.page("/")
def index_page():
    with layout("home"):
        project_list()

@ui.page("/settings")
def settings_page():
    with layout("setting"):
        settings()

@ui.page("/projects/{id}")
def project_page(id: str):
    with layout("project"):
        project(id)

# 启动配置
ui.run(
    port=24512,           # 本地端口
    title="Godot Love Wechat",
    window_size=(1024, 768),
    native=True,          # 原生窗口模式
    reload=False,         # 禁用热重载
)
```

### 关键点

- **NiceGUI 路由** - 使用 `@ui.page()` 装饰器定义页面
- **布局装饰器** - `layout()` 提供统一的页面框架
- **原生窗口** - `native=True` 使用 pywebview 创建桌面窗口

---

## 2. 导出器模块 - app/exporter.py

### 功能

核心导出逻辑，负责将 Godot 项目转换为微信小游戏格式。

### 类结构

```python
class Exporter:
    def __init__(self):
        self.storage: Storge = Storge()

    # 模板相关
    def get_tempalte_json(self) -> list

    # 配置相关
    def get_export_settings(self, project: dict) -> dict
    def save_export_settings(self, export_settings: dict, project_path: str)

    # 导出相关
    def export_project(self, export_settings: dict, project: dict)
    def export_pck(self, project_path: str, export_settings: dict, packPath: str)
    def export_subpack(self, subpacks: list, ...)

    # 配置文件修改
    def replace_gamejson(self, export_settings: dict)
    def replace_privatejson(self, project: dict, export_settings: dict)

    # 预览
    def preview_project(self, export_settings: dict)
```

### 核心方法详解

#### export_project()

主导出流程入口：

```python
def export_project(self, export_settings: dict, project: dict):
    # 检查是否已导出（game.json 存在与否）
    exported = os.path.exists(
        os.path.join(export_settings["export_path"], "game.json")
    )

    self.save_export_settings(export_settings, project["path"])
    settings = self.storage.get("settings.json")

    if exported and settings:
        # 增量导出
        if export_settings["subpack_config"]:
            self.export_subpack(...)
        else:
            gdscripts.set_export_presets(...)
            self.export_pck(...)
    else:
        # 完整导出
        # 1. 解压模板
        with zipfile.ZipFile(f"./templates/{export_settings['export_template']}") as zf:
            zf.extractall(export_settings["export_path"])

        # 2. 修改配置
        self.replace_gamejson(export_settings)
        self.replace_privatejson(project, export_settings)

        # 3. 导出 PCK
        # ...（同增量导出）
```

#### export_pck()

调用 Godot 命令行导出资源包：

```python
def export_pck(self, project_path: str, export_settings: dict, packPath: str):
    settings = self.storage.get("settings.json")
    if settings:
        godot_execute = settings["godot_execute"]
        result = subprocess.run([
            godot_execute,
            "--headless",      # 无头模式
            "--path", project_path,
            "--export-pack",   # 导出 PCK 格式
            export_settings["export_perset"],  # 预设名
            packPath,          # 输出路径
        ])
```

#### export_subpack()

处理分包导出：

```python
def export_subpack(self, subpacks: list, export_settings: dict,
                   project_path: str, godot_execute: str):
    # 创建临时目录
    tmpdir = os.path.join(localpath, "tmp")

    for i, pack in enumerate(subpacks):
        # 修改导出预设（指定资源范围）
        gdscripts.set_export_presets(
            godot_execute, project_path,
            export_settings["export_perset"], i
        )

        if pack["subpack_type"] == "main":
            # 主包 → engine/godot.zip
            pckPath = os.path.join(export_path, "engine\\godot.zip")
            self.export_pck(project_path, export_settings, pckPath)

        if pack["subpack_type"] == "inner_subpack":
            # 内部分包 → subpacks/{name}.zip
            pckPath = os.path.join(export_path, f"subpacks\\{pack['name']}.zip")
            self.export_pck(project_path, export_settings, pckPath)

        if pack["subpack_type"] == "cdn_subpack":
            # CDN 分包 → 上传到 S3
            s3client = boto3.client("s3", ...)
            pckPath = os.path.join(tmpdir, f"{pack['name']}.zip")
            self.export_pck(project_path, export_settings, pckPath)
            s3client.upload_file(pckPath, bucket, upload_path)
```

---

## 3. Godot 脚本执行 - app/gdscripts.py

### 功能

执行 Godot 脚本以读取/修改导出预设。

### 函数详解

#### get_export_presets()

获取可用的导出预设列表：

```python
def get_export_presets(godot_execute: str, project_path: str):
    abs = Path().resolve()
    script_path = abs.joinpath("gdscripts/export_perset.gd")

    result = subprocess.run([
        godot_execute,
        "--headless",
        "--path", project_path,
        "-d",              # 调试模式
        "--script", script_path.as_posix(),
    ], capture_output=True, text=True)

    # 从输出中提取 JSON 数组
    output = result.stdout
    match = re.search(r"\[.*?\]", output)
    if match:
        return json.loads(match.group())
    return []
```

#### set_export_presets()

修改导出预设：

```python
def set_export_presets(godot_execute: str, project_path: str,
                       preset: str, config_index: int | None):
    script_path = abs.joinpath("gdscripts/set_preset.gd")

    if config_index is None:
        # 导出所有资源
        subprocess.run([
            godot_execute, "--headless", "--path", project_path,
            "-d", "--script", script_path.as_posix(),
            "--", preset,
        ], ...)
    else:
        # 导出指定资源（分包用）
        subprocess.run([
            godot_execute, "--headless", "--path", project_path,
            "-d", "--script", script_path.as_posix(),
            "--", preset, str(config_index),
        ], ...)
```

---

## 4. GDScript 文件 - gdscripts/

### export_perset.gd

读取 `export_presets.cfg` 并输出预设名称列表：

```gdscript
extends SceneTree

func _init() -> void:
    var config = ConfigFile.new()
    var err = config.load("res://export_presets.cfg")
    if err != OK:
        return

    var presets = []
    for section in config.get_sections():
        if section.begins_with("preset."):
            var name = config.get_value(section, "name", "")
            if name != "":
                presets.append(name)

    print(JSON.stringify(presets))  # 输出 JSON 数组
    quit()
```

### set_preset.gd

修改 `export_presets.cfg` 的导出过滤器：

```gdscript
extends SceneTree

func _init() -> void:
    var args = OS.get_cmdline_user_args()
    var config = ConfigFile.new()
    config.load("res://export_presets.cfg")

    if args.size() == 1:
        # 单参数：导出所有资源
        var name = args[0]
        for section in config.get_sections():
            if section.begins_with("preset."):
                if config.get_value(section, "name", "") == name:
                    config.set_value(section, "export_filter", "all_resources")
                    config.erase_section_key(section, "export_files")
                    config.save("res://export_presets.cfg")
                    quit()

    if args.size() == 2:
        # 双参数：导出指定资源（分包）
        var name = args[0]
        var index = int(args[1])

        # 从 minigame.export.json 读取分包配置
        var export_settings = load_json_file("res://minigame.export.json")
        var subpack_config = export_settings["subpack_config"][index]

        for section in config.get_sections():
            if section.begins_with("preset."):
                if config.get_value(section, "name", "") == name:
                    var resources = PackedStringArray()
                    resources.append_array(subpack_config["subpack_resource"])
                    config.set_value(section, "export_filter", "resources")
                    config.set_value(section, "export_files", resources)
                    config.save("res://export_presets.cfg")
                    quit()

func load_json_file(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var file = FileAccess.open(path, FileAccess.READ)
    var content = file.get_as_text()
    file.close()
    return JSON.parse_string(content)
```

---

## 5. 本地存储 - app/stroge.py

### 功能

简单的 JSON 文件存储，用于持久化设置和项目列表。

### 实现

```python
class Storge:
    def __init__(self):
        # 存储在用户本地 AppData 目录
        self.path = os.path.join(os.environ['LOCALAPPDATA'], 'godot-love-wechat')

    def save(self, file, data):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        _data = json.dumps(data, indent=2)
        path = os.path.join(self.path, file)
        with open(path, "w+") as f:
            f.write(_data)

    def get(self, file):
        path = os.path.join(self.path, file)
        if not os.path.exists(path):
            return
        with open(path, "rb") as f:
            return json.loads(f.read())
```

### 存储的文件

| 文件 | 内容 |
|------|------|
| `settings.json` | Godot 路径、微信工具路径、CDN 配置 |
| `projects.json` | 已导入的项目列表 |

---

## 6. 工具函数 - app/utils.py

### parse_godot_project()

解析 Godot 的 `project.godot` 文件：

```python
def parse_godot_project(file_path):
    """使用正则表达式解析 Godot project.godot 文件"""
    section_pattern = re.compile(r"^\[(.+?)\]$")
    key_value_pattern = re.compile(r"^([\w/]+)=(.+)$")

    result = {}
    current_section = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            section_match = section_pattern.match(line)
            if section_match:
                current_section = section_match.group(1)
                result[current_section] = {}
                continue

            key_value_match = key_value_pattern.match(line)
            if key_value_match and current_section:
                key, value = key_value_match.groups()
                value = value.strip().strip('"')
                result[current_section][key] = value

    return result
```

### build_tree_dict()

构建文件树结构（用于分包资源选择 UI）：

```python
def build_tree_dict(root_path, excludes=[".import", ".uid", ...],
                    depth=0, max_depth=10, base_path=None):
    """递归构建文件树"""
    path = Path(root_path)

    # 过滤隐藏文件和特定文件
    if path.name.startswith("."):
        return None
    if path.name in ["export_presets.cfg", "minigame.export.json"]:
        return None

    node = {
        "id": f"res://{path.relative_to(base_path).as_posix()}",
        "icon": "folder" if path.is_dir() else "description",
        "label": path.name,
    }

    # 递归处理子目录
    if path.is_dir() and depth < max_depth:
        children = []
        for child in sorted(os.listdir(path)):
            if child in excludes:
                continue
            child_node = build_tree_dict(path / child, ...)
            if child_node:
                children.append(child_node)
        if children:
            node["children"] = children

    return node
```

---

## 7. 页面模块

### app/layout.py

页面布局装饰器，提供统一的侧边栏和内容区：

```python
def layout(current_page: str):
    def decorator(func):
        def wrapper():
            with ui.row().classes("w-full h-screen"):
                # 侧边栏
                menu(current_page)
                # 内容区
                with ui.column().classes("flex-1 p-4 overflow-auto"):
                    func()
        return wrapper
    return decorator
```

### app/menu.py

导航菜单组件。

### app/settings.py

设置页面，配置：
- Godot 可执行文件路径
- 微信开发者工具路径
- CDN 访问密钥和端点

### app/project_list.py

项目列表页面，功能：
- 显示已导入的项目卡片
- 导入新项目（选择 Godot 项目目录）
- 删除项目

### app/project.py

项目详情页面，功能：
- 显示项目信息
- 配置导出设置（模板、预设、方向等）
- 配置分包
- 执行导出
- 打开微信开发者工具预览

---

## 模块依赖图

```
main.py
    │
    ├── layout.py ──────────► menu.py
    │
    ├── settings.py ────────► stroge.py
    │
    ├── project_list.py ────► stroge.py
    │                       ► utils.py
    │
    └── project.py ─────────► exporter.py
                            ► stroge.py
                            ► gdscripts.py
                            ► utils.py
```
