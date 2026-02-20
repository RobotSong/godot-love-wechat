import os
import json
import platform

class Storge:
    def __init__(self) -> None:
        # 跨平台数据目录
        if platform.system() == 'Windows':
            self.path = os.path.join(os.environ['LOCALAPPDATA'], 'godot-love-wechat')
        else:
            # Linux/macOS: 使用 ~/.local/share/ 或 XDG_DATA_HOME
            data_home = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            self.path = os.path.join(data_home, 'godot-love-wechat')

    def save(self, file, data):
        print(self.path)
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
            data = json.loads(f.read())
        return data

