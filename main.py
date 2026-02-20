from nicegui import ui, app
from app.layout import layout
from app.settings import settings
from app.project_list import project_list
from pathlib import Path
from app.project import project

static_folder = Path(__file__).parent / "assets"

app.add_static_files("/assets", str(static_folder))
ui.add_head_html('<meta charset="UTF-8">', shared=True)
ui.add_css("::-webkit-scrollbar { display: none; }", shared=True)
# 如果有乱码，可能需要安装中文字体：
# sudo apt install fonts-noto-cjk fonts-wqy-microhei

ui.add_css("""
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
                 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
""", shared=True)


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


ui.run(
    port=24512,
    title="Godot Love Wechat",
    window_size=(1024, 768),
    native=True,
    reload=False,
)
