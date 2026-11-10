"""仅为本机演示提供现有 Godot 导出文件；不导出、不修改、不复制资源。"""
import atexit
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote, urlsplit

REQUIRED_FILES = ("index.html", "index.js", "index.wasm", "index.pck")
ALLOWED_SUFFIXES = {".html", ".js", ".wasm", ".pck", ".png", ".ico", ".svg", ".css", ".json", ".webmanifest"}


class GameHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".wasm": "application/wasm", ".pck": "application/octet-stream",
                      ".js": "text/javascript"}

    def send_head(self):
        root = Path(self.directory).resolve()
        request = unquote(urlsplit(self.path).path).lstrip("/") or "index.html"
        path = (root / request).resolve()
        if (not path.is_relative_to(root) or not path.is_file()
                or path.suffix.lower() not in ALLOWED_SUFFIXES
                or any(part.startswith(".") for part in Path(request).parts)):
            self.send_error(404, "Game resource not found")
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, *args):
        pass  # 不记录客户端路径、参数或用户输入。


def start_local_game(directory):
    root = Path(directory).resolve()
    for name in REQUIRED_FILES:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or not path.stat().st_size:
            raise ValueError(f"缺少可用的 Godot Web 导出文件：{name}。请配置 GODOT_WEB_URL 或 GODOT_WEB_DIR。")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(GameHandler, directory=str(root)))
    server.daemon_threads = True
    Thread(target=server.serve_forever, name="naxi-godot-static", daemon=True).start()
    def close():
        server.shutdown()
        server.server_close()
    atexit.register(close)
    return server
