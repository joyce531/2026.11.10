import base64
from io import BytesIO
import sys
from pathlib import Path
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_api import evaluate_request


def payload(blank=False):
    image = Image.new('RGB', (400, 400), 'white')
    if not blank:
        ImageDraw.Draw(image).line([(50, 50), (350, 350)], fill='black', width=12)
    stream = BytesIO()
    image.save(stream, format='PNG')
    return {'character_id': 'dongba_01', 'input_method': 'online_canvas',
            'image': 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')}


class MockApiTests(unittest.TestCase):
    def test_mismatch_is_not_passed_as_ai(self):
        result = evaluate_request(payload())
        self.assertEqual(result['source'], 'mock')
        self.assertEqual(result['status'], 'incorrect')
        self.assertGreater(len(result['improvement_suggestions']), 0)

    def test_blank_is_rejected(self):
        result = evaluate_request(payload(blank=True))
        self.assertEqual(result['source'], 'quality_check')
        self.assertEqual(result['status'], 'uncertain')

    def test_missing_reference_fails_explicitly(self):
        data = payload()
        data['character_id'] = 'not_in_catalog'
        with self.assertRaisesRegex(Exception, '找不到目标字形'):
            evaluate_request(data)


if __name__ == '__main__':
    unittest.main()
