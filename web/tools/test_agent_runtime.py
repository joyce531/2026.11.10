"""Milestone 7 offline boundary tests. Every model and paid call is patched."""
import base64
from io import BytesIO
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

import mido
from PIL import Image, ImageDraw

from web.tools.agent_runtime import Runtime
from web.tools import mock_api


def media(raw, mime='application/octet-stream'):
    return 'data:' + mime + ';base64,' + base64.b64encode(raw).decode('ascii')


class RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_dongba_idempotency_and_source(self):
        image = BytesIO()
        Image.new('RGB', (64, 64), 'white').save(image, format='PNG')
        fake = {'status': 'close', 'source': 'qwen_vision', 'similarity_score': 72,
                'overall_feedback': 'test', 'differences': [], 'improvement_suggestions': [],
                'confidence': 'medium', 'character_id': 'dongba_01', 'input_method': 'online_canvas', 'model': 'configured-model'}
        with patch('web.tools.agent_runtime.config_value', return_value='true'), patch('web.tools.agent_runtime.DongbaHandwritingAgent') as agent:
            agent.return_value.evaluate.return_value = fake
            body = {'image': media(image.getvalue(), 'image/png'), 'character_id': 'dongba_01', 'input_method': 'online_canvas'}
            first = self.runtime.dongba(body, 'dongba_unique_key_01')
            second = self.runtime.dongba(body, 'dongba_unique_key_01')
            self.assertEqual(first, second)
            self.assertEqual(first['result']['source'], 'qwen_vision')
            agent.assert_called_once_with(mock=False)
            agent.return_value.evaluate.assert_called_once()

    def test_music_parse_and_saved_media(self):
        midi = mido.MidiFile()
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.Message('note_on', note=60, velocity=70, time=0))
        track.append(mido.Message('note_off', note=60, velocity=0, time=480))
        stream = BytesIO(); midi.save(file=stream)
        body = {'filename': 'example.mid', 'file': media(stream.getvalue())}
        parsed = self.runtime.recognize(body, 'music_recognize_key_01')
        self.assertEqual(parsed['result']['kind'], 'structured')
        self.assertEqual(parsed['result']['note_count'], 1)
        fake = {'midi': b'MThd1234', 'wav': b'RIFF1234', 'mode': 'local_rules', 'model': None,
                'plan': {'explanation': 'offline', 'limitations': []}, 'usage': [], 'duration_seconds': 1., 'cultural_status': 'test'}
        with patch('web.tools.agent_runtime.arrange_music', return_value=fake) as arrange:
            request = {**body, 'asset_ids': ['sample'], 'style': '洞经音乐', 'preservation': 80}
            result = self.runtime.arrange(request, 'music_arrange_key_01')
            again = self.runtime.arrange(request, 'music_arrange_key_01')
        self.assertEqual(result, again)
        arrange.assert_called_once()
        self.assertEqual(self.runtime.artifact(result['task_id'], 'wav'), b'RIFF1234')
        self.assertEqual(self.runtime.artifact(result['task_id'], 'midi'), b'MThd1234')

    def test_image_omr_review_gate_routes_to_existing_services(self):
        picture = Image.new('RGB', (120, 80), 'white')
        ImageDraw.Draw(picture).line([(10, 40), (110, 40)], fill='black', width=4)
        image = BytesIO(); picture.save(image, format='PNG')
        doc = {'notation': 'jianpu', 'engine': 'qwen_vision', 'model': 'configured-vision',
               'coverage': 'partial', 'unsupported_symbols': [], 'warnings': [], 'tokens': []}
        body = {'filename': 'printed.png', 'file': media(image.getvalue(), 'image/png')}
        with patch('web.tools.agent_runtime.classify', return_value={'kind': 'jianpu'}), \
             patch('web.tools.agent_runtime.recognize_jianpu', return_value=doc) as vision:
            result = self.runtime.recognize(body, 'music_image_key_01')
        self.assertEqual(result['result']['kind'], 'jianpu')
        self.assertEqual(result['model'], 'configured-vision')
        vision.assert_called_once()
        row = {'start': 0., 'duration': .5, 'pitch': 60, 'rest': False, 'voice': 'melody',
               'symbol': '1', 'uncertain': False, 'issue': '', 'reviewed': True}
        with patch('web.tools.agent_runtime.jianpu_rows', return_value=[row]) as convert:
            reviewed = self.runtime.review({'document': doc, 'tonic': 'C', 'degree': 1, 'octave': 4, 'bpm': 120})
        convert.assert_called_once()
        self.assertTrue(reviewed['has_limitations'])
        fake = {'midi': b'MThd1234', 'wav': b'RIFF1234', 'mode': 'local_rules', 'model': None}
        with patch('web.tools.agent_runtime.confirm_midi', return_value=b'MThd1234') as confirm, \
             patch('web.tools.agent_runtime.arrange_music', return_value=fake):
            self.runtime.arrange({'reviewed_rows': reviewed['rows'], 'tempos': reviewed['tempos'],
                                  'confirmed': True, 'has_limitations': True, 'limitations_accepted': True,
                                  'asset_ids': ['sample'], 'style': '洞经音乐', 'preservation': 80}, 'music_review_key_01')
        confirm.assert_called_once()

    def test_dance_create_poll_download_once(self):
        request = {'video': media(b'mock-video'), 'portrait': media(b'mock-image', 'image/png'),
                   'outfit': '女1', 'background': '雪山', 'style': '写实'}
        with patch('web.tools.agent_runtime.inspect_video'), patch('web.tools.agent_runtime.inspect_image'), \
             patch('web.tools.agent_runtime.submit_videoedit', return_value={'task_id': 'provider-12345678', 'status': 'PENDING', 'model': 'wan2.7-videoedit'}) as submit, \
             patch('web.tools.agent_runtime.query_videoedit', return_value={'status': 'SUCCEEDED', 'video_url': 'https://example.aliyuncs.com/result.mp4'}) as query, \
             patch('web.tools.agent_runtime.download_videoedit', return_value=b'generated-mp4') as download:
            first = self.runtime.dance_submit(request, 'dance_unique_key_01')
            second = self.runtime.dance_submit(request, 'dance_unique_key_01')
            self.assertEqual(first, second)
            submit.assert_called_once()
            done = self.runtime.dance_status(first['task_id'])
            self.assertEqual(done['status'], 'SUCCEEDED')
            self.assertEqual(self.runtime.artifact(first['task_id'], 'mp4'), b'generated-mp4')
            self.runtime.dance_status(first['task_id'])
            query.assert_called_once(); download.assert_called_once()

    def test_http_routes_and_range(self):
        with patch.object(mock_api, '_runtime', self.runtime):
            server = ThreadingHTTPServer(('127.0.0.1', 0), mock_api.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base + '/api/agents/dance/options') as response:
                    self.assertEqual(len(json.load(response)['outfits']), 4)
                midi = mido.MidiFile(); track = mido.MidiTrack(); midi.tracks.append(track)
                track.extend([mido.Message('note_on', note=60, velocity=70), mido.Message('note_off', note=60, time=480)])
                buf = BytesIO(); midi.save(file=buf)
                payload = json.dumps({'filename': 'one.mid', 'file': media(buf.getvalue())}).encode()
                request = Request(base + '/api/agents/music/recognize', payload,
                                  {'Content-Type': 'application/json', 'Idempotency-Key': 'http_music_key_01'})
                with urlopen(request) as response:
                    self.assertEqual(json.load(response)['result']['note_count'], 1)
                fake = {'midi': b'MThd1234', 'wav': b'RIFF1234', 'mode': 'local_rules', 'model': None}
                with patch('web.tools.agent_runtime.arrange_music', return_value=fake):
                    job = self.runtime.arrange({'filename': 'one.mid', 'file': media(buf.getvalue()),
                                                'asset_ids': ['sample'], 'style': '洞经音乐', 'preservation': 80}, 'http_arrange_key_01')
                partial = Request(base + job['result']['wav_url'], headers={'Range': 'bytes=0-3'})
                with urlopen(partial) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b'RIFF')
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_dongba_http_local_origins_and_external_rejection(self):
        fake = {'task_id': 'offline', 'agent': 'dongba', 'status': 'completed', 'result': {'source': 'mock'}}
        with patch.object(mock_api, '_runtime', self.runtime), patch.object(self.runtime, 'dongba', return_value=fake) as evaluate, \
             patch.dict('os.environ', {'NAXI_API_ENV': ''}):
            server = ThreadingHTTPServer(('127.0.0.1', 0), mock_api.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f'http://127.0.0.1:{server.server_port}/api/agents/dongba/evaluate'
                def send(origin, referer=None, content_type='application/json'):
                    headers = {'Origin': origin, 'Content-Type': content_type, 'Idempotency-Key': 'offline-key-1234'}
                    if referer:
                        headers['Referer'] = referer
                    return urlopen(Request(url, b'{}', headers))

                for port in (5173, 5174):
                    with self.subTest(port=port), send(f'http://127.0.0.1:{port}', f'http://127.0.0.1:{port}/agent/dongba') as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(json.load(response)['result']['source'], 'mock')
                with send('http://localhost:5174', 'http://localhost:5174/agent/dongba') as response:
                    self.assertEqual(response.status, 200)
                with self.assertRaises(HTTPError) as rejected:
                    send('https://evil.example', 'https://evil.example/agent/dongba')
                self.assertEqual(rejected.exception.code, 403)
                rejected.exception.close()
                with self.assertRaises(HTTPError) as rejected_referer:
                    send('http://localhost:5174', 'https://evil.example/agent/dongba')
                self.assertEqual(rejected_referer.exception.code, 403)
                rejected_referer.exception.close()
                with self.assertRaises(HTTPError) as wrong_type:
                    send('http://localhost:5174', content_type='text/plain')
                self.assertEqual(wrong_type.exception.code, 415)
                wrong_type.exception.close()
                self.assertEqual(evaluate.call_count, 3)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_production_origin_is_exact(self):
        self.assertTrue(mock_api.allowed_request('127.0.0.1:8765', 'https://naxi.example',
                        'https://naxi.example/agent/dongba', production=True,
                        configured_origins='https://naxi.example'))
        self.assertFalse(mock_api.allowed_request('127.0.0.1:8765', 'https://naxi.example.evil.test',
                         None, production=True, configured_origins='https://naxi.example'))
        self.assertFalse(mock_api.allowed_request('127.0.0.1:8765', None,
                         None, production=True, configured_origins='https://naxi.example'))
        self.assertFalse(mock_api.allowed_request('127.0.0.1:8765', 'https://naxi.example',
                         None, production=True, configured_origins=''))


if __name__ == '__main__':
    unittest.main()
