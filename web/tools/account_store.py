"""Local account, session, quota and approval store for the Web API.

No provider call is made here. Production requires persistent storage and a
same-origin proxy or an explicit HTTPS origin allowlist.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import sys
import uuid

from services.dance_service import inspect_image, inspect_video
from web.tools.agent_runtime import decode_media, MAX_IMAGE, MAX_VIDEO


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def password_hash(password):
    if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
        raise ValueError('密码须为 12–256 个字符。')
    salt = secrets.token_bytes(32)
    key = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**15, r=8, p=1,
                         maxmem=128*1024*1024, dklen=32)
    return 'scrypt$32768$8$1$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(key).decode()


def verify_password(password, encoded):
    try:
        scheme, n, r, p, salt, expected = encoded.split('$')
        if scheme != 'scrypt' or (int(n), int(r), int(p)) != (32768, 8, 1):
            return False
        actual = hashlib.scrypt(password.encode('utf-8'), salt=base64.b64decode(salt),
                                n=int(n), r=int(r), p=int(p), maxmem=128*1024*1024, dklen=32)
        return hmac.compare_digest(actual, base64.b64decode(expected))
    except (ValueError, TypeError, UnicodeError):
        return False


class AccessError(ValueError):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.status = status


class AccountStore:
    def __init__(self, database):
        self.db = Path(database).resolve()
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self.private = self.db.parent / 'private' / 'approvals'
        self.private.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def migrate(self):
        with self.connect() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','judge')), password_hash TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1, expires_at TEXT, created_at TEXT NOT NULL, last_login TEXT);
            CREATE TABLE IF NOT EXISTS auth_sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                csrf_hash TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT);
            CREATE TABLE IF NOT EXISTS auth_failures(id TEXT PRIMARY KEY, username TEXT NOT NULL,
                ip TEXT NOT NULL, happened_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS user_quotas(user_id TEXT NOT NULL, agent TEXT NOT NULL,
                daily_limit INTEGER NOT NULL, PRIMARY KEY(user_id,agent));
            CREATE TABLE IF NOT EXISTS agent_requests(id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                agent TEXT NOT NULL, idem TEXT UNIQUE NOT NULL, day_utc TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, job_id TEXT, model TEXT);
            CREATE TABLE IF NOT EXISTS agent_usage(id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL, agent TEXT NOT NULL, at TEXT NOT NULL, model TEXT,
                task_id TEXT, input_tokens INTEGER, output_tokens INTEGER, estimated_cost REAL);
            CREATE TABLE IF NOT EXISTS dance_approval_requests(id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                idem TEXT UNIQUE NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                decided_at TEXT, decided_by TEXT, video_path TEXT NOT NULL, portrait_path TEXT NOT NULL,
                video_info TEXT NOT NULL, outfit TEXT NOT NULL, background TEXT NOT NULL,
                style TEXT NOT NULL, description TEXT NOT NULL, job_id TEXT);
            CREATE TABLE IF NOT EXISTS quota_requests(id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                agent TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                decided_at TEXT, decided_by TEXT);
            CREATE TABLE IF NOT EXISTS agent_tasks(job_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                agent TEXT NOT NULL, status TEXT NOT NULL, model TEXT, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS works(job_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                agent TEXT NOT NULL, artifact_path TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_logs(id TEXT PRIMARY KEY, actor_id TEXT,
                action TEXT NOT NULL, target_id TEXT, at TEXT NOT NULL);
            ''')
            defaults = {'quota_dongba': '10', 'quota_music': '3', 'ai_paused': 'false'}
            for key, value in defaults.items():
                con.execute('INSERT OR IGNORE INTO system_settings VALUES (?,?)', (key, value))
            jobs = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()
            if jobs and 'user_id' not in [row[1] for row in con.execute('PRAGMA table_info(jobs)')]:
                con.execute('ALTER TABLE jobs ADD COLUMN user_id TEXT')

    def audit(self, actor, action, target=None):
        with self.connect() as con:
            con.execute('INSERT INTO audit_logs VALUES (?,?,?,?,?)', (uuid.uuid4().hex, actor, action, target, utc()))

    def public_user(self, row):
        return {key: row[key] for key in ('id','username','role','active','expires_at','created_at','last_login')}

    def init_admin(self, username, password):
        username = self._username(username)
        encoded = password_hash(password)
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if con.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
                raise AccessError('管理员已初始化；不会重复创建。', 409)
            user_id = uuid.uuid4().hex
            con.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)',
                        (user_id, username, 'admin', encoded, 1, None, utc(), None))
        self.audit(user_id, 'admin_initialized', user_id)
        return user_id

    def _username(self, username):
        if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}', username):
            raise ValueError('用户名须为 3–40 位英文字母、数字、点、下划线或连字符。')
        return username.lower()

    def login(self, username, password, ip):
        try:
            name = self._username(username)
        except ValueError:
            name = ''
        now = utc()
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        failure = None
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            failures = con.execute('SELECT COUNT(*) FROM auth_failures WHERE happened_at>=? AND (ip=? OR username=?)',
                                   (cutoff, ip, name)).fetchone()[0]
            if failures >= 5:
                raise AccessError('登录尝试过多，请 15 分钟后再试。', 429)
            row = con.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
            good = bool(row and isinstance(password, str) and verify_password(password, row['password_hash']))
            if not good:
                con.execute('INSERT INTO auth_failures VALUES (?,?,?,?)', (uuid.uuid4().hex, name, ip, now))
                failure = AccessError('用户名或密码不正确。', 401)
            elif not row['active']:
                failure = AccessError('账号已禁用，请联系管理员。', 403)
            elif row['expires_at'] and row['expires_at'] <= now:
                failure = AccessError('账号已到期，请联系管理员。', 403)
            else:
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                expiry = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
                con.execute('INSERT INTO auth_sessions VALUES (?,?,?,?,?,?)',
                            (digest(token), row['id'], digest(csrf), now, expiry, None))
                con.execute('UPDATE users SET last_login=? WHERE id=?', (now, row['id']))
                con.execute('DELETE FROM auth_failures WHERE ip=? OR username=?', (ip, name))
        if failure:
            raise failure
        self.audit(row['id'], 'login', row['id'])
        return self.public_user({**row, 'last_login': now}), token, csrf

    def session(self, token):
        if not token:
            return None
        with self.connect() as con:
            row = con.execute('''SELECT s.csrf_hash,s.expires_at AS session_expires,s.revoked_at,u.* FROM auth_sessions s
                JOIN users u ON u.id=s.user_id WHERE s.token_hash=?''', (digest(token),)).fetchone()
        if not row or row['revoked_at'] or row['session_expires'] <= utc() or not row['active'] or (row['expires_at'] and row['expires_at'] <= utc()):
            return None
        return dict(row)

    def revoke(self, token):
        if token:
            with self.connect() as con:
                con.execute('UPDATE auth_sessions SET revoked_at=? WHERE token_hash=?', (utc(), digest(token)))

    def csrf(self, session, value):
        if not session or not value or not hmac.compare_digest(session['csrf_hash'], digest(value)):
            raise AccessError('会话校验失败，请刷新页面后重试。', 403)

    def issue_csrf(self, token):
        """Rotate a CSRF token for an authenticated page load, including cross-origin hosting."""
        session = self.session(token)
        if not session:
            raise AccessError('请先登录。', 401)
        value = secrets.token_urlsafe(32)
        with self.connect() as con:
            con.execute('UPDATE auth_sessions SET csrf_hash=? WHERE token_hash=? AND revoked_at IS NULL',
                        (digest(value), digest(token)))
        return value

    def users(self):
        with self.connect() as con:
            return [self.public_user(row) for row in con.execute('SELECT * FROM users ORDER BY created_at DESC')]

    def create_judge(self, actor, username, expires_at=None):
        name = self._username(username)
        expiry = self._expiry(expires_at)
        password = secrets.token_urlsafe(20)
        encoded = password_hash(password)
        user_id = uuid.uuid4().hex
        try:
            with self.connect() as con:
                con.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)',
                            (user_id, name, 'judge', encoded, 1, expiry, utc(), None))
        except sqlite3.IntegrityError:
            raise AccessError('用户名已存在，请更换。', 409) from None
        self.audit(actor, 'judge_created', user_id)
        return user_id, password

    def _expiry(self, value):
        if value in (None, ''):
            return None
        if not isinstance(value, str):
            raise ValueError('到期时间格式无效。')
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo is None or parsed <= datetime.now(timezone.utc):
                raise ValueError
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            raise ValueError('请输入将来的 UTC ISO 到期时间。') from None

    def manage_user(self, actor, user_id, action, value=None):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not row or row['role'] != 'judge':
                raise AccessError('评委账号不存在。', 404)
            password = None
            if action == 'reset':
                password = secrets.token_urlsafe(20)
                con.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(password), user_id))
            elif action in ('disable', 'delete', 'enable'):
                con.execute('UPDATE users SET active=? WHERE id=?', (1 if action == 'enable' else 0, user_id))
            elif action == 'expire':
                con.execute('UPDATE users SET expires_at=? WHERE id=?', (self._expiry(value), user_id))
            elif action != 'revoke':
                raise ValueError('账号操作无效。')
            if action in ('reset', 'disable', 'delete', 'revoke'):
                con.execute('UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL', (utc(), user_id))
        self.audit(actor, 'judge_' + action, user_id)
        return {'password': password} if password else {'ok': True}

    def settings(self):
        with self.connect() as con:
            return {row['key']: row['value'] for row in con.execute('SELECT * FROM system_settings')}

    def set_settings(self, actor, values):
        allowed = {'quota_dongba','quota_music','ai_paused'}
        if not isinstance(values, dict) or not values or set(values) - allowed:
            raise ValueError('设置字段无效。')
        cleaned = {}
        for key, value in values.items():
            if key == 'ai_paused':
                if not isinstance(value, bool):
                    raise ValueError('AI 开关无效。')
                cleaned[key] = 'true' if value else 'false'
            else:
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
                    raise ValueError('每日额度须为 0–1000 的整数。')
                cleaned[key] = str(value)
        with self.connect() as con:
            for key, value in cleaned.items():
                con.execute('INSERT OR REPLACE INTO system_settings VALUES (?,?)', (key, value))
        self.audit(actor, 'settings_updated')
        return self.settings()

    def paused(self):
        return self.settings()['ai_paused'] == 'true'

    def quota(self, user_id):
        settings = self.settings()
        today = datetime.now(timezone.utc).date().isoformat()
        output = {}
        with self.connect() as con:
            for agent in ('dongba', 'music'):
                custom = con.execute('SELECT daily_limit FROM user_quotas WHERE user_id=? AND agent=?', (user_id, agent)).fetchone()
                limit = custom['daily_limit'] if custom else int(settings['quota_' + agent])
                held = con.execute('''SELECT COUNT(*) FROM agent_requests WHERE user_id=? AND agent=? AND day_utc=?
                    AND status IN ('reserved','charged','uncertain')''', (user_id, agent, today)).fetchone()[0]
                charged = con.execute('SELECT COUNT(*) FROM agent_usage WHERE user_id=? AND agent=? AND substr(at,1,10)=?',
                                      (user_id, agent, today)).fetchone()[0]
                output[agent] = {'limit': limit, 'used': charged, 'remaining': max(0, limit-held)}
        return output

    def set_user_quota(self, actor, user_id, agent, limit):
        if agent not in ('dongba','music') or isinstance(limit, bool) or not isinstance(limit, int) or not 0 <= limit <= 1000:
            raise ValueError('额度参数无效。')
        with self.connect() as con:
            if not con.execute('SELECT 1 FROM users WHERE id=?', (user_id,)).fetchone():
                raise AccessError('账号不存在。', 404)
            con.execute('INSERT OR REPLACE INTO user_quotas VALUES (?,?,?)', (user_id, agent, limit))
        self.audit(actor, 'quota_updated', user_id)

    def reserve(self, user_id, agent, idem, may_external):
        if not re.fullmatch(r'[A-Za-z0-9_-]{12,100}', idem or ''):
            raise ValueError('缺少有效幂等键。')
        today = datetime.now(timezone.utc).date().isoformat()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute('SELECT * FROM agent_requests WHERE idem=?', (idem,)).fetchone()
            if old:
                if old['user_id'] != user_id or old['agent'] != agent:
                    raise AccessError('该任务键不属于当前账号。', 403)
                return False
            if may_external and con.execute("SELECT value FROM system_settings WHERE key='ai_paused'").fetchone()[0] == 'true':
                raise AccessError('AI 服务已暂停；不会发起新模型请求。', 403)
            if may_external and agent in ('dongba','music'):
                settings = self.settings()
                custom = con.execute('SELECT daily_limit FROM user_quotas WHERE user_id=? AND agent=?', (user_id, agent)).fetchone()
                limit = custom['daily_limit'] if custom else int(settings['quota_' + agent])
                held = con.execute('''SELECT COUNT(*) FROM agent_requests WHERE user_id=? AND agent=? AND day_utc=?
                    AND status IN ('reserved','charged','uncertain')''', (user_id, agent, today)).fetchone()[0]
                if held >= limit:
                    raise AccessError('当前体验额度已用完，可以向管理员申请增加体验次数。', 429)
            con.execute('INSERT INTO agent_requests VALUES (?,?,?,?,?,?,?,?,?)',
                        (uuid.uuid4().hex, user_id, agent, idem, today, 'reserved' if may_external else 'local', utc(), None, None))
        return True

    def finish(self, idem, job=None, *, external=False, uncertain=False):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM agent_requests WHERE idem=?', (idem,)).fetchone()
            if not row:
                return
            status = 'uncertain' if uncertain else 'charged' if external else 'local'
            job_id = job.get('task_id') if job else None
            model = job.get('model') if job else None
            con.execute('UPDATE agent_requests SET status=?,job_id=?,model=? WHERE id=?', (status, job_id, model, row['id']))
            if external:
                con.execute('''INSERT OR IGNORE INTO agent_usage(id,request_id,user_id,agent,at,model,task_id)
                    VALUES (?,?,?,?,?,?,?)''', (uuid.uuid4().hex, row['id'], row['user_id'], row['agent'], utc(), model, job_id))
        if job:
            self.sync_task(job, row['user_id'])

    def sync_task(self, job, user_id):
        result = job.get('result') or {}
        artifact = result.get('video_url') or result.get('wav_url') or result.get('midi_url')
        with self.connect() as con:
            con.execute('INSERT OR REPLACE INTO agent_tasks VALUES (?,?,?,?,?,?)',
                        (job['task_id'], user_id, job['agent'], job['status'], job.get('model'), utc()))
            if job['status'] in ('completed','SUCCEEDED'):
                con.execute('INSERT OR IGNORE INTO works VALUES (?,?,?,?,?)',
                            (job['task_id'], user_id, job['agent'], artifact, utc()))

    def create_dance_request(self, user_id, idem, body, runtime):
        if self.paused():
            raise AccessError('AI 服务已暂停，暂不接受新视频申请。', 403)
        if not re.fullmatch(r'[A-Za-z0-9_-]{12,100}', idem or ''):
            raise ValueError('缺少有效幂等键。')
        with self.connect() as con:
            old = con.execute('SELECT * FROM dance_approval_requests WHERE idem=?', (idem,)).fetchone()
        if old:
            if old['user_id'] != user_id:
                raise AccessError('该申请不属于当前账号。', 403)
            return self.public_approval(old)
        video = decode_media(body.get('video'), MAX_VIDEO)
        portrait = decode_media(body.get('portrait'), MAX_IMAGE)
        video_info = inspect_video(video)
        video_info['size_bytes'] = len(video)
        inspect_image(portrait)
        runtime.dance_asset('outfit', body.get('outfit'))
        runtime.dance_asset('background', body.get('background'))
        if body.get('consent') is not True:
            raise ValueError('请先确认本人素材的使用及后续发送授权。')
        approval_id = uuid.uuid4().hex
        folder = self.private / approval_id
        folder.mkdir(mode=0o700)
        video_path, portrait_path = folder / 'video.mp4', folder / 'portrait.img'
        video_path.write_bytes(video)
        portrait_path.write_bytes(portrait)
        inserted = False
        try:
            with self.connect() as con:
                con.execute('BEGIN IMMEDIATE')
                old = con.execute('SELECT * FROM dance_approval_requests WHERE idem=?', (idem,)).fetchone()
                if old:
                    if old['user_id'] != user_id:
                        raise AccessError('该申请不属于当前账号。', 403)
                    return self.public_approval(old)
                con.execute('''INSERT INTO dance_approval_requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                            (approval_id, user_id, idem, 'pending_approval', utc(), None, None,
                             str(video_path), str(portrait_path), json.dumps(video_info),
                             body['outfit'], body['background'], str(body.get('style','写实'))[:80],
                             str(body.get('description',''))[:500], None))
                inserted = True
        finally:
            if not inserted and folder.parent.resolve() == self.private.resolve():
                shutil.rmtree(folder)
        self.audit(user_id, 'dance_requested', approval_id)
        return self.approval(approval_id, user_id)

    def public_approval(self, row):
        return {key: row[key] for key in ('id','user_id','status','created_at','decided_at','outfit','background','style','description','job_id')} | {
            'video_info': json.loads(row['video_info'])}

    def approval(self, approval_id, user_id=None):
        with self.connect() as con:
            row = con.execute('SELECT * FROM dance_approval_requests WHERE id=?', (approval_id,)).fetchone()
        if not row or (user_id and row['user_id'] != user_id):
            raise AccessError('视频申请不存在或无权查看。', 404)
        return self.public_approval(row)

    def approval_by_key(self, idem, user_id):
        with self.connect() as con:
            row = con.execute('SELECT * FROM dance_approval_requests WHERE idem=?', (idem,)).fetchone()
        if not row or row['user_id'] != user_id:
            raise AccessError('视频申请不存在或无权查看。', 404)
        return self.public_approval(row)

    def approvals(self, user_id=None):
        with self.connect() as con:
            rows = con.execute('SELECT * FROM dance_approval_requests WHERE user_id=? ORDER BY created_at DESC', (user_id,)).fetchall() if user_id else con.execute('SELECT * FROM dance_approval_requests ORDER BY created_at DESC').fetchall()
        return [self.public_approval(row) for row in rows]

    def lock_approval(self, actor, approval_id):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if con.execute("SELECT value FROM system_settings WHERE key='ai_paused'").fetchone()[0] == 'true':
                raise AccessError('AI 服务已暂停，不能批准生成。', 403)
            row = con.execute('SELECT * FROM dance_approval_requests WHERE id=?', (approval_id,)).fetchone()
            if not row or row['status'] != 'pending_approval':
                raise AccessError('申请已处理；不会重复创建 Wan 任务。', 409)
            con.execute("UPDATE dance_approval_requests SET status='approved',decided_at=?,decided_by=? WHERE id=?",
                        (utc(), actor, approval_id))
        self.audit(actor, 'dance_approved', approval_id)
        return dict(row)

    def finish_approval(self, approval_id, job=None):
        status = 'submitted' if job and job['status'] not in ('failed','FAILED') else 'failed'
        with self.connect() as con:
            con.execute('UPDATE dance_approval_requests SET status=?,job_id=? WHERE id=?',
                        (status, job.get('task_id') if job else None, approval_id))
        if job:
            row = self._approval_row(approval_id)
            self.sync_task(job, row['user_id'])

    def update_approval_for_job(self, job):
        state = {'PENDING': 'submitted', 'RUNNING': 'running', 'SUCCEEDED': 'succeeded',
                 'FAILED': 'failed', 'CANCELED': 'cancelled'}.get(job['status'])
        if state:
            with self.connect() as con:
                con.execute('UPDATE dance_approval_requests SET status=? WHERE job_id=?',
                            (state, job['task_id']))
                row = con.execute('SELECT user_id FROM dance_approval_requests WHERE job_id=?',
                                  (job['task_id'],)).fetchone()
            if row:
                self.sync_task(job, row['user_id'])

    def _approval_row(self, approval_id):
        with self.connect() as con:
            return con.execute('SELECT * FROM dance_approval_requests WHERE id=?', (approval_id,)).fetchone()

    def approval_body(self, row):
        def encode(path, mime):
            return 'data:' + mime + ';base64,' + base64.b64encode(Path(path).read_bytes()).decode('ascii')
        return {'video': encode(row['video_path'], 'video/mp4'),
                'portrait': encode(row['portrait_path'], 'image/png'),
                'outfit': row['outfit'], 'background': row['background'],
                'style': row['style'], 'description': row['description']}

    def decide_approval(self, actor, approval_id, action):
        if action not in ('rejected','cancelled'):
            raise ValueError('申请操作无效。')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT status FROM dance_approval_requests WHERE id=?', (approval_id,)).fetchone()
            if not row or row['status'] != 'pending_approval':
                raise AccessError('申请已处理。', 409)
            con.execute('UPDATE dance_approval_requests SET status=?,decided_at=?,decided_by=? WHERE id=?',
                        (action, utc(), actor, approval_id))
        self.audit(actor, 'dance_' + action, approval_id)
        if action == 'cancelled':
            row = self._approval_row(approval_id)
            folder = Path(row['video_path']).parent.resolve()
            if folder.parent == self.private.resolve():
                shutil.rmtree(folder)

    def quota_request(self, user_id, agent):
        if agent not in ('dongba','music'):
            raise ValueError('Agent 类型无效。')
        request_id = uuid.uuid4().hex
        with self.connect() as con:
            existing = con.execute('SELECT id FROM quota_requests WHERE user_id=? AND agent=? AND status=?',
                                   (user_id, agent, 'pending')).fetchone()
            if existing:
                return {'id': existing['id'], 'status': 'pending'}
            con.execute('INSERT INTO quota_requests VALUES (?,?,?,?,?,?,?)',
                        (request_id, user_id, agent, 'pending', utc(), None, None))
        self.audit(user_id, 'quota_requested', request_id)
        return {'id': request_id, 'status': 'pending'}

    def quota_requests(self):
        with self.connect() as con:
            return [dict(row) for row in con.execute('SELECT * FROM quota_requests ORDER BY created_at DESC')]

    def decide_quota(self, actor, request_id, approve):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM quota_requests WHERE id=?', (request_id,)).fetchone()
            if not row or row['status'] != 'pending':
                raise AccessError('额度申请已处理。', 409)
            if approve:
                settings = self.settings()
                custom = con.execute('SELECT daily_limit FROM user_quotas WHERE user_id=? AND agent=?',
                                     (row['user_id'], row['agent'])).fetchone()
                current = custom['daily_limit'] if custom else int(settings['quota_' + row['agent']])
                con.execute('INSERT OR REPLACE INTO user_quotas VALUES (?,?,?)',
                            (row['user_id'], row['agent'], min(1000, current + 5)))
            con.execute('UPDATE quota_requests SET status=?,decided_at=?,decided_by=? WHERE id=?',
                        ('approved' if approve else 'rejected', utc(), actor, request_id))
        self.audit(actor, 'quota_approved' if approve else 'quota_rejected', request_id)

    def usage(self):
        with self.connect() as con:
            return [dict(row) for row in con.execute('''SELECT r.user_id,u.username,r.agent,r.created_at,r.status,
                r.model,r.job_id FROM agent_requests r JOIN users u ON u.id=r.user_id
                ORDER BY r.created_at DESC LIMIT 200''')]


def main():
    from web.tools.agent_runtime import Runtime
    store = AccountStore(Runtime().db)
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'migrate':
        print('数据库迁移完成。')
    elif command == 'init-admin':
        username = input('管理员用户名：').strip()
        password = getpass.getpass('管理员密码（至少 12 位）：')
        confirm = getpass.getpass('再次输入密码：')
        if password != confirm:
            raise SystemExit('两次密码不一致。')
        store.init_admin(username, password)
        print('管理员创建成功；密码未写入日志或文件。')
    else:
        raise SystemExit('用法：python -m web.tools.account_store [migrate|init-admin]')


if __name__ == '__main__':
    main()
