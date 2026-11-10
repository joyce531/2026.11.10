"""平台边界与导航测试，不调用外部模型或修改原游戏。"""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from streamlit.testing.v1 import AppTest
from config.settings import game_settings
from services.game_service import start_local_game
from services.music_service import MusicRequest, generate_music, validate_request as validate_music
from services.dance_service import DanceRequest, generate_dance_video

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class PlatformTests(unittest.TestCase):
    def test_four_home_entries_and_game_page(self):
        with patch.dict(os.environ, {"GODOT_WEB_URL": "https://example.invalid/game/"}):
            app = AppTest.from_file(APP).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get("page_link")), 4)
            app.switch_page("pages/game.py").run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(app.title[0].value, "纳西文化互动学习游戏")
            self.assertEqual(len(app.get("link_button")), 1)

    def test_game_missing_and_invalid_configuration(self):
        with patch.dict(os.environ, {"GODOT_WEB_URL": "", "GODOT_WEB_DIR": ""}):
            app = AppTest.from_file(APP).run(timeout=20)
            app.switch_page("pages/game.py").run(timeout=20)
            self.assertFalse(app.exception)
            self.assertTrue(app.warning)
        for value in ["javascript:alert(1)", "file:///D:/game", "https://u:p@example.com", "http://host:bad"]:
            with patch.dict(os.environ, {"GODOT_WEB_URL": value}):
                with self.assertRaises(ValueError):
                    game_settings()

    def test_services_never_fake_generation(self):
        music = MusicRequest(["钢琴（通用）"], ["弹拨质感"], "自由探索", "宁静", 80, 30, "平稳", "test")
        self.assertEqual(validate_music(music), [])
        with self.assertRaises(NotImplementedError):
            generate_music(music)
        dance = DanceRequest("沿用参考视频舞步", "保留", "保留", "写实", 10, "test")
        with self.assertRaises(NotImplementedError):
            generate_dance_video(dance, b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42")
        with self.assertRaises(ValueError):
            generate_dance_video(dance, b"fake")

    def test_static_server_headers_and_path_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("index.html", "index.js", "index.wasm", "index.pck"):
                (root / name).write_bytes(b"test-fixture")
            (root / ".hidden.json").write_text("private")
            server = start_local_game(root)
            url = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(url + "/index.wasm") as response:
                    self.assertEqual(response.headers["Content-Type"], "application/wasm")
                    self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin")
                    self.assertEqual(response.read(), b"test-fixture")
                for path in ["/.hidden.json", "/%2e%2e/private.txt", "/missing/", "/project.godot"]:
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(url + path)
                    self.assertEqual(caught.exception.code, 404)
                    caught.exception.close()
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(url + "/index.html", data=b"write", method="POST"))
                self.assertEqual(caught.exception.code, 501)
                caught.exception.close()
                self.assertEqual((root / "index.html").read_bytes(), b"test-fixture")
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
