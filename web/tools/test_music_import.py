"""Offline provenance check for the read-only Godot music import."""
import hashlib
import json
from pathlib import Path
import unittest

WEB = Path(__file__).resolve().parents[1]
SOURCE = Path(r'D:\dachuang\naxi-game')


@unittest.skipUnless((SOURCE / 'project.godot').is_file(), 'Godot source not available on this machine')
class MusicImportTests(unittest.TestCase):
    def test_content_is_verbatim_from_godot(self):
        original = json.loads((SOURCE / 'Data/content.json').read_text(encoding='utf-8'))
        imported = json.loads((WEB / 'src/game/music_content.json').read_text(encoding='utf-8'))
        for source_key, target_key in [('culture_books', 'book'), ('quizzes', 'quiz'), ('completion_pages', 'completion')]:
            self.assertEqual(imported[target_key], original[source_key]['music'])

    def test_all_imported_music_is_identical(self):
        catalog = json.loads((WEB / 'src/game/music_content.json').read_text(encoding='utf-8'))
        manifest = json.loads((WEB / 'src/game/asset_manifest.json').read_text(encoding='utf-8'))
        media = [q['prompt']['audio'].removeprefix('res://') for q in catalog['quiz']['questions']]
        media += [
            'Assets/music/stingers/stinger_fail_dongjing.ogg',
            'Assets/music/stingers/stinger_win_baisha.ogg',
        ]
        media += [s['illustration'].removeprefix('res://') for s in catalog['book']['spreads'] if s['illustration']]
        for rel in media:
            with self.subTest(rel=rel):
                self.assertEqual(manifest[rel]['status'], 'copied')
                source_bytes = (SOURCE / rel).read_bytes()
                copied_bytes = (WEB / 'public/godot' / rel).read_bytes()
                self.assertEqual(source_bytes, copied_bytes)
                self.assertEqual(hashlib.sha256(copied_bytes).hexdigest(), manifest[rel]['sha256'])


if __name__ == '__main__':
    unittest.main()
