"""Offline checks for five exact Godot quiz-video mappings and Web MP4 copies."""
import hashlib
import json
from pathlib import Path
import unittest

import cv2

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(r'D:\dachuang\naxi-game')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless((SOURCE / 'project.godot').is_file(), 'Godot source unavailable')
class MusicVideoTests(unittest.TestCase):
    def test_all_five_have_original_mapping_picture_and_audio(self):
        data = json.loads((SOURCE / 'Data/content.json').read_text(encoding='utf-8'))
        manifest = json.loads((ROOT / 'web/src/game/music_video_manifest.json').read_text(encoding='utf-8'))
        questions = data['quizzes']['music']['questions']
        self.assertEqual(len(manifest), len(questions))
        for question, item in zip(questions, manifest):
            with self.subTest(question=question['id']):
                original_path = question['prompt']['audio']
                self.assertEqual(item['game_path'], original_path)
                source = ROOT / item['source']
                original = SOURCE / original_path.removeprefix('res://')
                output = ROOT / 'web/public' / item['web_path'].lstrip('/')
                self.assertEqual(digest(source), digest(original))
                self.assertEqual(digest(source), item['source_sha256'])
                self.assertEqual(digest(output), item['web_sha256'])
                streams = {s['codec_type']: s['codec_name'] for s in item['output_streams']}
                self.assertEqual(streams['video'], 'h264')
                self.assertEqual(streams['audio'], 'aac')
                self.assertAlmostEqual(item['output_duration_seconds'], item['source_duration_seconds'], delta=.3)
                capture = cv2.VideoCapture(str(output))
                capture.set(cv2.CAP_PROP_POS_MSEC, 1500)
                valid, frame = capture.read()
                capture.release()
                self.assertTrue(valid)
                self.assertGreater(float(frame.std()), 5)


if __name__ == '__main__':
    unittest.main()
