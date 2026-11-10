"""One local Web boundary for the existing Python agents. No third-party calls at import time."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import uuid

from PIL import Image, ImageOps

from naxi_agents.dongba_agent import DongbaHandwritingAgent
from services.dongba_vision import config_value
from services import qwen_service
from services.music_library import list_assets
from services.music_score import parse_score
from services.music_service import arrange_music
from services.score_image import load_score_image, preprocess, classify
from services.score_omr import recognize_jianpu, recognize_staff, recognize_staff_vision, TONICS
from services.score_review import jianpu_rows, confirm_midi
from services.dance_service import (
    MODEL as DANCE_MODEL, OUTFIT_DIR, BACKGROUND_DIR, DanceRequest, choices,
    inspect_video, inspect_image, submit_videoedit, query_videoedit, download_videoedit,
)

ROOT = Path(__file__).resolve().parents[2]
MAX_IMAGE = 10 * 1024 * 1024
MAX_VIDEO = 50 * 1024 * 1024
LOCK = threading.RLock()


def decode_media(value, limit):
    if not isinstance(value, str) or not value.startswith('data:') or ';base64,' not in value[:80]:
        raise ValueError('上传文件编码无效。')
    encoded = value.split(';base64,', 1)[1]
    if len(encoded) > (limit * 4 // 3) + 100:
        raise ValueError('上传文件超过大小限制。')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        raise ValueError('上传文件 Base64 无效。') from None
    if not raw or len(raw) > limit:
        raise ValueError('上传文件为空或超过大小限制。')
    return raw


def image_from_data(value, limit=MAX_IMAGE):
    raw = decode_media(value, limit)
    try:
        with Image.open(BytesIO(raw)) as opened:
            if opened.format not in ('PNG', 'JPEG') or opened.width * opened.height > 20_000_000:
                raise ValueError('图片只支持 PNG/JPG 且不超过 2000 万像素。')
            image = ImageOps.exif_transpose(opened).convert('RGB')
            image.load()
            return image
    except (OSError, Image.DecompressionBombError):
        raise ValueError('图片损坏或无法读取。') from None


def _utc():
    return datetime.now(timezone.utc).isoformat()


class Runtime:
    def __init__(self, root=None):
        base = Path(root) if root is not None else Path(os.environ['NAXI_DATA_DIR']) if os.environ.get('NAXI_DATA_DIR') else Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'NaxiAIStudio' / 'web'
        self.root = base.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / 'artifacts').mkdir(exist_ok=True)
        self.db = self.root / 'works.sqlite3'
        with self._connect() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, idem TEXT UNIQUE NOT NULL, kind TEXT NOT NULL,
                created_at TEXT NOT NULL, status TEXT NOT NULL, model TEXT,
                provider_task_id TEXT, result_json TEXT, error TEXT)''')
            if 'user_id' not in [column[1] for column in con.execute('PRAGMA table_info(jobs)')]:
                con.execute('ALTER TABLE jobs ADD COLUMN user_id TEXT')

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def _row(self, field, value):
        with self._connect() as con:
            return con.execute(f'SELECT * FROM jobs WHERE {field}=?', (value,)).fetchone()

    def _start(self, kind, key, user_id=None):
        if not isinstance(key, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{12,100}', key):
            raise ValueError('缺少有效幂等键；未提交计费请求。')
        with LOCK:
            old = self._row('idem', key)
            if old:
                if old['kind'] != kind or old['user_id'] != user_id:
                    raise ValueError('幂等键已用于另一类任务。')
                return old['id'], False
            job_id = uuid.uuid4().hex
            with self._connect() as con:
                con.execute('INSERT INTO jobs (id,idem,kind,created_at,status,user_id) VALUES (?,?,?,?,?,?)',
                            (job_id, key, kind, _utc(), 'submitting', user_id))
            return job_id, True

    def _set(self, job_id, **changes):
        allowed = {'status', 'model', 'provider_task_id', 'result_json', 'error'}
        if set(changes) - allowed:
            raise ValueError('内部字段无效。')
        with self._connect() as con:
            con.execute('UPDATE jobs SET ' + ','.join(f'{key}=?' for key in changes) + ' WHERE id=?',
                        (*changes.values(), job_id))

    def _public(self, row):
        result = json.loads(row['result_json']) if row['result_json'] else None
        return {'task_id': row['id'], 'agent': row['kind'], 'submitted_at': row['created_at'],
                'status': row['status'], 'model': row['model'], 'result': result, 'error': row['error']}

    def _owns(self, row, user_id, admin=False):
        if user_id is not None and row['user_id'] != user_id and not admin:
            raise ValueError('任务不存在或无权访问。')

    def job(self, job_id, user_id=None, admin=False):
        if not isinstance(job_id, str) or not re.fullmatch(r'[0-9a-f]{32}', job_id):
            raise ValueError('任务 ID 无效。')
        row = self._row('id', job_id)
        if not row:
            raise ValueError('任务不存在。')
        self._owns(row, user_id, admin)
        return self._public(row)

    def by_key(self, key, user_id=None, admin=False):
        row = self._row('idem', key)
        if not row:
            raise ValueError('未找到该提交记录。')
        self._owns(row, user_id, admin)
        return self._public(row)

    def works(self, user_id=None, admin=False):
        with self._connect() as con:
            rows = (con.execute('SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100').fetchall()
                    if admin or user_id is None else con.execute(
                        'SELECT * FROM jobs WHERE user_id=? ORDER BY created_at DESC LIMIT 100', (user_id,)).fetchall())
        return [self._public(row) for row in rows]

    def _execute(self, kind, key, operation, user_id=None):
        job_id, created = self._start(kind, key, user_id)
        if not created:
            return self.job(job_id, user_id)
        try:
            result, model, status = operation(job_id)
            self._set(job_id, status=status, model=model, result_json=json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            # Preserve the idempotency record even after an ambiguous external timeout.
            message = str(exc)[:500] if isinstance(exc, ValueError) else '任务执行失败；未自动重试，请检查服务端配置和日志。'
            self._set(job_id, status='failed', error=message)
            raise
        return self.job(job_id, user_id)

    def dongba(self, body, key, user_id=None):
        def operation(_job_id):
            image = image_from_data(body.get('image'), 5 * 1024 * 1024)
            real = config_value('USE_REAL_AI', 'false').lower() == 'true'
            result = DongbaHandwritingAgent(mock=not real).evaluate(body.get('character_id'), image, body.get('input_method'))
            safe = {field: result.get(field) for field in ('character_id', 'status', 'similarity_score', 'overall_feedback',
                    'structure_analysis', 'differences', 'improvement_suggestions', 'confidence', 'source', 'fallback_reason', 'input_method')}
            return safe, result.get('model'), 'completed'
        return self._execute('dongba', key, operation, user_id)

    def music_assets(self):
        return [{key: asset[key] for key in ('asset_id', 'label', 'identity_status', 'sample_mapping')}
                for asset in list_assets() if asset['material_type'] == 'instrument' and asset['analysis_status'].startswith('decoded')]

    def recognize(self, body, key, user_id=None):
        def operation(_job_id):
            filename = Path(str(body.get('filename', ''))).name
            suffix = Path(filename).suffix.lower()
            data = decode_media(body.get('file'), MAX_IMAGE)
            if suffix in ('.mid', '.midi', '.xml', '.musicxml', '.mxl'):
                score = parse_score(data, filename)
                return {'kind': 'structured', 'format': score['format'], 'notes': score['melody'][:100],
                        'note_count': score['note_count'], 'duration_seconds': score['duration_seconds'],
                        'tempos': score['tempos'], 'meters': score['meters'], 'warnings': score['warnings']}, None, 'completed'
            if suffix not in ('.png', '.jpg', '.jpeg', '.webp'):
                raise ValueError('仅支持 MIDI、MusicXML/MXL 和清晰印刷曲谱图片。')
            image = load_score_image(data, filename)
            processed, ink, meta = preprocess(image)
            kind = classify(ink)['kind']
            if kind == 'unknown':
                kind = body.get('notation')
                if kind not in ('staff', 'jianpu'):
                    return {'kind': 'needs_notation', 'message': '无法自动判断简谱或五线谱，请手动选择后重新点击识谱。', 'preprocess': meta}, None, 'completed'
            if kind == 'jianpu':
                doc = recognize_jianpu(processed)
            else:
                doc = recognize_staff_vision(processed) if qwen_service.enabled() else recognize_staff(processed)
            doc.pop('export_bytes', None)
            return {'kind': kind, 'document': doc, 'preprocess': meta}, doc.get('model'), 'completed'
        return self._execute('music_recognize', key, operation, user_id)

    def review(self, body):
        doc = body.get('document')
        if not isinstance(doc, dict):
            raise ValueError('缺少识谱草稿。')
        if doc.get('notation') == 'jianpu':
            tonic = body.get('tonic') or doc.get('tonic_note')
            if tonic not in TONICS:
                raise ValueError('调号未知，请先确认 1=C、6=A 等调号；不会默认 1=C。')
            degree = int(body.get('degree') or doc.get('tonic_degree') or 0)
            bpm = float(body.get('bpm') or doc.get('bpm') or 0)
            rows = jianpu_rows(doc, tonic, degree, int(body.get('octave', 4)), bpm)
            tempos = [{'time': 0., 'bpm': bpm}]
        elif doc.get('notation') == 'staff':
            rows, tempos = doc['rows'], doc['tempos']
        else:
            raise ValueError('识谱类型无效。')
        return {'rows': rows, 'tempos': tempos, 'has_limitations': doc.get('coverage') != 'complete' or bool(doc.get('unsupported_symbols')),
                'warnings': doc.get('warnings', []), 'unsupported_symbols': doc.get('unsupported_symbols', [])}

    def arrange(self, body, key, user_id=None):
        def operation(job_id):
            if body.get('reviewed_rows') is not None:
                rows = body['reviewed_rows']
                if not isinstance(rows, list):
                    raise ValueError('校对音符格式无效。')
                reviewed = [{**row, 'reviewed': bool(row.get('reviewed'))} for row in rows]
                midi = confirm_midi(reviewed, body.get('tempos'), confirmed=body.get('confirmed') is True,
                    limitations_accepted=body.get('limitations_accepted') is True,
                    has_limitations=body.get('has_limitations') is True)
                filename = 'reviewed.mid'
                data = midi
            else:
                filename = Path(str(body.get('filename', ''))).name
                data = decode_media(body.get('file'), 2 * 1024 * 1024)
            result = arrange_music(data, filename, body.get('asset_ids'), body.get('style'), body.get('preservation'))
            folder = self.root / 'artifacts'
            (folder / (job_id + '.mid')).write_bytes(result.pop('midi'))
            (folder / (job_id + '.wav')).write_bytes(result.pop('wav'))
            safe = {**result, 'midi_url': f'/api/artifacts/{job_id}/midi', 'wav_url': f'/api/artifacts/{job_id}/wav'}
            return safe, result.get('model'), 'completed'
        return self._execute('music_arrange', key, operation, user_id)

    def dance_options(self):
        return {'outfits': list(choices(OUTFIT_DIR)), 'backgrounds': list(choices(BACKGROUND_DIR)), 'model': DANCE_MODEL}

    def dance_asset(self, kind, name):
        if not re.fullmatch(r'[\w\u4e00-\u9fff-]{1,60}', name):
            raise ValueError('素材名称无效。')
        directory = OUTFIT_DIR if kind == 'outfit' else BACKGROUND_DIR if kind == 'background' else None
        if directory is None or name not in choices(directory):
            raise ValueError('素材不存在。')
        return choices(directory)[name].read_bytes()

    def dance_submit(self, body, key, user_id=None):
        def operation(_job_id):
            video = decode_media(body.get('video'), MAX_VIDEO)
            portrait = decode_media(body.get('portrait'), MAX_IMAGE)
            inspect_video(video)
            inspect_image(portrait)
            outfit = self.dance_asset('outfit', body.get('outfit'))
            background = self.dance_asset('background', body.get('background'))
            request = DanceRequest(step='沿用参考视频舞步', costume=body['outfit'], background=body['background'],
                style=str(body.get('style', '写实'))[:80], duration_seconds=5,
                description=str(body.get('description', ''))[:500])
            result = submit_videoedit(video, portrait, outfit, background, request)
            self._set(_job_id, provider_task_id=result['task_id'])
            return {'status': result['status'], 'message': '已提交百炼异步任务；查询状态不会再次创建任务。'}, result['model'], result['status']
        return self._execute('dance', key, operation, user_id)

    def dance_status(self, job_id, user_id=None, admin=False):
        with LOCK:
            row = self._row('id', job_id)
            if not row or row['kind'] != 'dance':
                raise ValueError('舞蹈任务不存在。')
            self._owns(row, user_id, admin)
            if row['status'] in ('SUCCEEDED', 'FAILED', 'CANCELED', 'failed', 'submitting'):
                return self._public(row)
            if not row['provider_task_id']:
                raise ValueError('任务 ID 尚未确认；请勿重复提交。')
            result = query_videoedit(row['provider_task_id'])
            if result['status'] == 'SUCCEEDED':
                video = download_videoedit(result['video_url'])
                (self.root / 'artifacts' / (job_id + '.mp4')).write_bytes(video)
                safe = {'video_url': f'/api/agents/dance/jobs/{job_id}/result', 'size_bytes': len(video)}
                self._set(job_id, status='SUCCEEDED', result_json=json.dumps(safe))
            else:
                self._set(job_id, status=result['status'], error=result.get('error'))
            return self.job(job_id, user_id, admin)

    def artifact(self, job_id, extension, user_id=None, admin=False):
        if not re.fullmatch(r'[0-9a-f]{32}', job_id) or extension not in ('midi', 'wav', 'mp4'):
            raise ValueError('作品地址无效。')
        row = self._row('id', job_id)
        if not row or row['status'] not in ('completed', 'SUCCEEDED'):
            raise ValueError('作品尚不可下载。')
        self._owns(row, user_id, admin)
        if not ((row['kind'] == 'dance' and extension == 'mp4') or
                (row['kind'] == 'music_arrange' and extension in ('midi', 'wav'))):
            raise ValueError('作品格式不匹配。')
        suffix = '.mid' if extension == 'midi' else '.' + extension
        return (self.root / 'artifacts' / (job_id + suffix)).read_bytes()
