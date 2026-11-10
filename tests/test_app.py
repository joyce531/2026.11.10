"""使用 Streamlit 内置 AppTest 和标准库测试，不增加依赖。"""

from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

from tools.upload_validation import prepare_image, validate_size, validate_video

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


class UploadTests(unittest.TestCase):
    def test_real_image_and_invalid_inputs(self):
        buffer = BytesIO()
        Image.new("RGB", (24, 32), "white").save(buffer, format="PNG")
        preview, size = prepare_image(buffer.getvalue(), "drawing.png")
        self.assertEqual(size, (24, 32))
        self.assertEqual(preview.mode, "RGB")
        for data, name in [(b"", "x.png"), (b"fake", "x.png"),
                           (buffer.getvalue(), "x.jpg"), (buffer.getvalue(), "x.svg")]:
            with self.subTest(name=name, data_size=len(data)):
                with self.assertRaises(ValueError):
                    prepare_image(data, name)

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            validate_size(b"a" * (1024 * 1024 + 1), 1)

    def test_oversized_image_dimensions(self):
        buffer = BytesIO()
        Image.new("1", (4001, 4000)).save(buffer, format="PNG")
        with self.assertRaisesRegex(ValueError, "1600"):
            prepare_image(buffer.getvalue(), "large.png")

    def test_video_header_only(self):
        # 人工文件头仅用于验证基础校验，不作为可播放视频或产品素材。
        header = b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42"
        validate_video(header, "clip.mp4")
        for data, name in [(b"", "x.mp4"), (b"fake video", "x.mp4"),
                           (header, "x.exe"), (header[:16], "x.mp4")]:
            with self.subTest(name=name, data_size=len(data)):
                with self.assertRaises(ValueError):
                    validate_video(data, name)


class PageTests(unittest.TestCase):
    def test_home_and_navigation(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        self.assertFalse(app.exception)
        for page in ["pages/dongba.py", "pages/music.py", "pages/dance.py"]:
            with self.subTest(page=page):
                app.switch_page(page).run(timeout=20)
                self.assertFalse(app.exception)
                self.assertTrue(any("开发中" in item.value for item in app.info))
                self.assertTrue(all(button.disabled for button in app.button))

    def test_music_controls(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.switch_page("pages/music.py").run()
        app.slider[0].set_value(75).run()
        app.selectbox[0].select('白沙细乐').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.slider[0].value,75)
        self.assertEqual(len(app.multiselect[0].options),8)
        app.multiselect[0].set_value([]).run()
        self.assertTrue(app.button[0].disabled)

    def test_other_controls(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.switch_page("pages/dongba.py").run()
        if not app.toggle[0].disabled:
            app.toggle[0].set_value(True).run()
        self.assertEqual(len(app.selectbox[0].options), 5)
        self.assertFalse(app.exception)
        app.switch_page("pages/dance.py").run()
        self.assertEqual(len(app.selectbox[0].options), 4)
        self.assertEqual(len(app.selectbox[1].options), 6)
        app.selectbox[1].select("雪山").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[1].value, "雪山")
        self.assertTrue(app.button[0].disabled)

    def test_real_first_configuration_never_calls_on_page_load(self):
        with patch('services.dongba_vision.use_real_ai',return_value=True), patch('naxi_agents.dongba_agent.create_client',side_effect=AssertionError('no submit')):
            app = AppTest.from_file(APP_PATH).run(timeout=20)
            app.switch_page('pages/dongba.py').run()
            self.assertFalse(app.exception)
            self.assertFalse(app.toggle[0].value)
            app.run()
            self.assertFalse(app.exception)
            app.toggle[0].set_value(True).run()
            self.assertTrue(app.toggle[0].value)


if __name__ == "__main__":
    unittest.main()
