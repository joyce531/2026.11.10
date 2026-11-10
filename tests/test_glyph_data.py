"""只使用临时非文化几何图形，不向正式 CSV 写入假资料。"""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw
from services.glyph_data import GlyphDataService, GLYPH_FIELDS, SAMPLE_FIELDS


class GlyphDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = GlyphDataService(self.root)
        self.relative = "data/glyphs/processed/fixture.png"
        path = self.root / self.relative
        path.parent.mkdir(parents=True)
        image = Image.new("RGB", (32, 32), "white")
        ImageDraw.Draw(image).rectangle((8, 8, 24, 24), outline="black")
        image.save(path)
        self.row = dict.fromkeys(GLYPH_FIELDS, "")
        self.row.update(glyph_id="test-1", chinese_meaning="非文字测试", english_label="fixture",
                        image_file="fixture.png", image_path=self.relative, image_width="32", image_height="32")

    def write(self, rows, sample=False, fields=None):
        path = self.root / ("data/handwriting_samples/sample_annotations.csv" if sample else "data/glyphs/glyph_catalog.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields or (SAMPLE_FIELDS if sample else GLYPH_FIELDS))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_real_inventory_consistency(self):
        service = GlyphDataService()
        records = service.read_glyph_catalog().records
        self.assertEqual(len(records), 5)
        self.assertEqual(service.read_glyph_catalog().messages, [])
        manifest = json.loads((service.root/'data/glyphs/glyph_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest), len(records))
        for row, entry in zip(records, manifest):
            self.assertEqual(row, {key: str(entry[key]) for key in GLYPH_FIELDS})
            self.assertEqual(hashlib.sha256((service.root/entry['image_path']).read_bytes()).hexdigest(), entry['sha256'])
            self.assertFalse(entry['is_blank'])
            self.assertIsNotNone(service.load_reference_image(row).image)
        self.assertEqual(service.find_samples().records, [])

    def test_query_multiple_variants_and_load(self):
        self.row['chinese_meaning'] = '测试逗号,换行\n只用于工程测试'
        self.write([self.row, {**self.row, 'glyph_id': 'test-2'}])
        result = self.service.find_glyphs('test-1')
        self.assertEqual(len(result.records), 1)
        self.assertFalse(result.messages)
        loaded = self.service.load_reference_image(result.records[0])
        self.assertEqual(loaded.image.size, (32, 32))
        self.assertTrue(self.service.find_glyphs('missing').messages)

    def test_missing_and_corrupt_images_do_not_block_catalog(self):
        missing = {**self.row, 'glyph_id': 'missing', 'image_path': 'data/glyphs/missing.png', 'image_file': 'missing.png'}
        self.write([missing, self.row])
        self.assertEqual(len(self.service.read_glyph_catalog().records), 2)
        self.assertTrue(self.service.read_glyph_catalog().messages)
        self.assertIsNone(self.service.load_reference_image(missing).image)
        (self.root/self.relative).write_bytes(b'not-image')
        result = self.service.load_reference_image(self.row)
        self.assertIsNone(result.image)
        self.assertTrue(result.messages)

    def test_dimensions_and_filename_validation(self):
        for updates in ({'image_width':'0'}, {'image_height':'unknown'}, {'image_file':'wrong.png'}):
            row = {**self.row, **updates}
            self.write([row])
            self.assertTrue(self.service.read_glyph_catalog().messages)
        self.assertIsNone(self.service.load_reference_image({**self.row, 'image_width':'31'}).image)

    def test_invalid_paths(self):
        for path in ('../outside.png', 'C:/outside.png', '/outside.png', 'https://host/image.png', '.env', 'data/glyphs/../x.png'):
            self.assertFalse(self.service.check_path(path)[0])
        self.assertTrue(self.service.check_path(self.relative.replace('/', '\\'))[0])

    def test_invalid_csv(self):
        self.write([], fields=['glyph_id'])
        self.assertTrue(self.service.read_glyph_catalog().messages)
        self.write([self.row, self.row])
        self.assertEqual(self.service.read_glyph_catalog().records, [])
        self.write([{**self.row, 'glyph_id':''}, self.row])
        result = self.service.read_glyph_catalog()
        self.assertEqual(len(result.records), 1)
        self.assertTrue(result.messages)
        path = self.write([])
        with path.open('a', encoding='utf-8') as f:
            f.write('too,few,columns\n')
        self.assertTrue(self.service.read_glyph_catalog().messages)

    def test_missing_csv(self):
        self.assertTrue(self.service.read_glyph_catalog().messages)
        self.assertTrue(self.service.find_samples().messages)

    def test_sample_query_and_optional_strokes(self):
        image = self.root/'data/handwriting_samples/images/test.png'
        image.parent.mkdir(parents=True)
        image.write_bytes((self.root/self.relative).read_bytes())
        row = dict.fromkeys(SAMPLE_FIELDS, '')
        row.update(sample_id='sample-test', character_id='test-only', input_method='photo_upload',
                   image_path='data/handwriting_samples/images/test.png', annotation_status='pending')
        self.write([row], sample=True)
        result = self.service.find_samples('test-only')
        self.assertEqual(len(result.records), 1)
        self.assertTrue(result.messages)
        self.assertEqual(self.service.find_samples('unknown').records, [])
        row['stroke_data_path'] = 'data/handwriting_samples/strokes/missing.json'
        self.write([row], sample=True)
        self.assertTrue(any('missing.json' in message for message in self.service.find_samples().messages))


if __name__ == '__main__':
    unittest.main()
