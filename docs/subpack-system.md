# 分包系统

本文档详细说明微信小游戏的分包机制及本项目的实现方式。

---

## 背景：微信小游戏包体限制

微信小游戏对包体有严格限制：

| 类型 | 限制 | 说明 |
|------|------|------|
| 单个分包 | 20 MB | 单个包的最大体积 |
| 总包体 | 30 MB | 主包 + 所有分包总和 |
| CDN 资源 | 无限制 | 网络加载的资源 |

对于大型 Godot 游戏，30MB 往往不够用。因此本项目实现了**分包系统**来突破限制。

---

## 分包类型

本项目支持三种分包类型：

### 1. 主包 (main)

```
位置：engine/godot.zip
说明：包含游戏核心资源和启动所需内容
```

- 游戏启动时首先加载
- 包含主场景、核心脚本、UI 资源等
- 必须存在

### 2. 内部分包 (inner_subpack)

```
位置：subpacks/{name}.zip
说明：随主包下载，在本地加载
```

- 计入 30MB 限制
- 适合非首屏必需的资源
- 按需加载

### 3. CDN 分包 (cdn_subpack)

```
位置：远程 S3 存储
说明：通过网络按需下载
```

- **不计入 30MB 限制**
- 适合大型资源（音频、视频、大图）
- 需要配置 CDN

---

## 分包配置

### minigame.export.json

在 Godot 项目根目录创建此文件：

```json
{
  "export_path": "minigame",
  "export_template": "minigame.2d.full_4.4.zip",
  "export_perset": "Web",
  "device_orientation": "landscape",
  "appid": "wx1234567890",
  "cdn_bucket": "my-game-cdn",
  "subpack_config": [
    {
      "name": "main",
      "subpack_type": "main",
      "subpack_resource": [
        "res://main.tscn",
        "res://scripts/",
        "res://ui/"
      ]
    },
    {
      "name": "level1",
      "subpack_type": "inner_subpack",
      "subpack_resource": [
        "res://levels/level1/"
      ]
    },
    {
      "name": "audio",
      "subpack_type": "cdn_subpack",
      "subpack_resource": [
        "res://audio/"
      ],
      "cdn_path": "v1.0"
    }
  ]
}
```

### 配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 分包名称 |
| `subpack_type` | enum | `main` / `inner_subpack` / `cdn_subpack` |
| `subpack_resource` | array | 该包包含的资源路径（`res://` 格式） |
| `cdn_path` | string | CDN 分包的存储路径前缀（可选） |

---

## 分包导出流程

### 流程图

```
用户点击导出
      │
      ▼
┌─────────────────────────────────────┐
│ 遍历 subpack_config 数组            │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 调用 set_preset.gd 修改导出预设     │
│ 设置 export_filter = "resources"    │
│ 设置 export_files = 指定资源列表    │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 调用 Godot --export-pack 导出 PCK   │
└─────────────────────────────────────┘
      │
      ├──► main → engine/godot.zip
      │
      ├──► inner_subpack → subpacks/{name}.zip
      │
      └──► cdn_subpack → 上传到 S3
```

### 代码实现

```python
# app/exporter.py:138-187
def export_subpack(self, subpacks, export_settings, project_path, godot_execute):
    tmpdir = os.path.join(localpath, "tmp")
    settings = self.storage.get("settings.json")

    for i, pack in enumerate(subpacks):
        # 修改导出预设（设置资源范围）
        gdscripts.set_export_presets(
            godot_execute, project_path,
            export_settings["export_perset"], i
        )

        if pack["subpack_type"] == "main":
            # 主包
            pckPath = os.path.join(export_path, "engine\\godot.zip")
            self.export_pck(project_path, export_settings, pckPath)

        if pack["subpack_type"] == "inner_subpack":
            # 内部分包
            pckPath = os.path.join(export_path, f"subpacks\\{pack['name']}.zip")
            self.export_pck(project_path, export_settings, pckPath)

        if pack["subpack_type"] == "cdn_subpack":
            # CDN 分包
            s3client = boto3.client(
                "s3",
                aws_access_key_id=settings["cdn_access_key_id"],
                aws_secret_access_key=settings["cdn_secret_access_key"],
                endpoint_url=settings["cdn_endpoint"],
            )
            pckPath = os.path.join(tmpdir, f"{pack['name']}.zip")
            self.export_pck(project_path, export_settings, pckPath)
            s3client.upload_file(pckPath, export_settings["cdn_bucket"], upload_path)
```

---

## 预设修改机制

### export_presets.cfg 结构

```ini
[preset.0]
name="Web"
platform="Web"
export_filter="all_resources"
; export_filter="resources" 时生效
export_files=["res://path/to/resource"]
```

### set_preset.gd 逻辑

```gdscript
# gdscripts/set_preset.gd
func _init():
    var args = OS.get_cmdline_user_args()

    if args.size() == 2:
        var name = args[0]        # 预设名称
        var index = int(args[1])  # 分包配置索引

        # 从 minigame.export.json 读取分包资源列表
        var export_settings = load_json_file("res://minigame.export.json")
        var subpack_config = export_settings["subpack_config"][index]

        # 修改预设
        config.set_value(section, "export_filter", "resources")
        config.set_value(section, "export_files", subpack_config["subpack_resource"])
        config.save("res://export_presets.cfg")
```

---

## 微信小游戏分包配置

### game.json

导出后需要在 `game.json` 中声明内部分包：

```json
{
  "deviceOrientation": "landscape",
  "subpackages": [
    {
      "name": "level1",
      "root": "subpacks/level1/"
    },
    {
      "name": "level2",
      "root": "subpacks/level2/"
    }
  ]
}
```

> 注：本项目目前未自动生成此配置，需要手动添加。

---

## 分包加载代码

在 Godot 游戏中，需要编写代码来加载分包：

### 内部分包加载

```gdscript
# 加载内部分包
func load_subpack(subpack_name: String):
    var path = "user://subpacks/" + subpack_name + ".zip"

    if not FileAccess.file_exists(path):
        # 微信环境下，分包已下载到本地
        # 需要先从微信文件系统复制到 user://
        pass

    # 加载 PCK
    var err = ProjectSettings.load_resource_pack(path)
    if err != OK:
        push_error("Failed to load subpack: " + subpack_name)
```

### CDN 分包加载

```gdscript
# 下载并加载 CDN 分包
func load_cdn_subpack(subpack_name: String, cdn_url: String):
    var http = HTTPRequest.new()
    add_child(http)

    var save_path = "user://cache/" + subpack_name + ".zip"

    # 下载
    var err = http.request(cdn_url)
    if err != OK:
        return

    # 等待下载完成
    var result = await http.request_completed

    # 加载 PCK
    ProjectSettings.load_resource_pack(save_path)
```

---

## CDN 配置

在设置页面配置 CDN：

| 字段 | 说明 |
|------|------|
| CDN Endpoint | S3 兼容存储的端点 URL |
| Access Key ID | 访问密钥 ID |
| Secret Access Key | 访问密钥 |

### 支持的存储服务

任何 S3 兼容的对象存储：
- AWS S3
- 阿里云 OSS
- 腾讯云 COS
- MinIO（自建）

### 示例配置

```
Endpoint: https://oss-cn-hangzhou.aliyuncs.com
Access Key ID: LTAI5t...
Secret Access Key: abc123...
Bucket: my-game-cdn
```

---

## 分包策略建议

### 资源分类

| 资源类型 | 推荐分包 | 原因 |
|---------|---------|------|
| 主场景、核心脚本 | 主包 | 启动必需 |
| UI 资源 | 主包 | 通常较小 |
| 关卡资源 | 内部分包 | 按需加载 |
| 音频文件 | CDN 分包 | 体积大 |
| 视频文件 | CDN 分包 | 体积大 |
| 高清贴图 | CDN 分包 | 体积大 |

### 分包粒度

- **太粗**：加载慢，用户等待时间长
- **太细**：管理复杂，请求次数多

**建议**：按游戏功能模块划分（如按关卡、按场景类型）

---

## 调试技巧

### 检查分包内容

```bash
# 解压 PCK 查看内容
unzip -l engine/godot.zip
unzip -l subpacks/level1.zip
```

### 验证 CDN 上传

```bash
# 使用 AWS CLI
aws s3 ls s3://my-game-cdn/v1.0/
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 分包未加载 | game.json 未配置 | 添加 subpackages 配置 |
| 资源找不到 | 路径错误 | 检查 res:// 路径是否正确 |
| CDN 下载失败 | 跨域问题 | 配置 CORS |
| 包体超限 | 内部分包过多 | 将部分改为 CDN 分包 |

---

## 总结

| 要点 | 说明 |
|------|------|
| 目的 | 突破 30MB 包体限制 |
| 三种类型 | 主包、内部分包、CDN 分包 |
| 配置文件 | minigame.export.json |
| 核心机制 | 动态修改 export_presets.cfg |
| 加载方式 | ProjectSettings.load_resource_pack() |
