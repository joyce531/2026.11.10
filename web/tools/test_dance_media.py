"""Offline provenance and decode checks for Godot dance assets."""
import hashlib
import json
import unittest
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(r"D:\dachuang\naxi-game")
WEB = ROOT / "web"


class DanceMediaTest(unittest.TestCase):
    def test_original_mapping_and_mp4_decode(self):
        data = json.loads((WEB / "src/game/dance_content.json").read_text(encoding="utf-8"))["dance"]
        manifest = json.loads((WEB / "src/game/dance_video_manifest.json").read_text(encoding="utf-8"))
        expected = [data["full_video"], *(step["video"] for step in data["steps"])]
        self.assertEqual({item["game_path"] for item in manifest}, set(expected))
        for item in manifest:
            with self.subTest(item=item["game_path"]):
                source = ROOT / item["source"]
                original = SOURCE / item["game_path"].removeprefix("res://")
                output = WEB / "public" / item["web_path"].lstrip("/")
                self.assertTrue(source.is_file() and original.is_file() and output.is_file())
                self.assertEqual(source.read_bytes(), original.read_bytes())
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), item["source_sha256"])
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), item["web_sha256"])
                self.assertTrue(any(s["codec_name"] == "h264" for s in item["output_streams"]))
                self.assertTrue(any(s["codec_name"] == "aac" for s in item["output_streams"]))
                capture = cv2.VideoCapture(str(output))
                self.assertTrue(capture.isOpened())
                count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
                fps = capture.get(cv2.CAP_PROP_FPS)
                self.assertGreater(count, 0)
                self.assertGreater(fps, 0)
                capture.set(cv2.CAP_PROP_POS_FRAMES, min(int(count * 0.3), int(count - 1)))
                success, frame = capture.read()
                capture.release()
                self.assertTrue(success and frame is not None)
                self.assertGreater(frame.std(), 1)


if __name__ == "__main__":
    unittest.main()
