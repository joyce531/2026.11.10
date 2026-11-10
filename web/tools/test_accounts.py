"""Milestone 8 targeted offline tests: provider calls are replaced with fakes."""
import base64
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from web.tools.account_store import AccountStore
from web.tools.agent_runtime import Runtime
from web.tools import mock_api


class AccountApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(self.temp.name)
        self.store = AccountStore(self.runtime.db)
        self.admin_id = self.store.init_admin('owner', 'strong owner password 123')
        self.patch_runtime = patch.object(mock_api, '_runtime', self.runtime)
        self.patch_accounts = patch.object(mock_api, '_accounts', self.store)
        self.patch_real_flag = patch.object(mock_api, 'config_value', return_value='true')
        self.patch_runtime.start(); self.patch_accounts.start(); self.patch_real_flag.start()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), mock_api.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.patch_real_flag.stop(); self.patch_accounts.stop(); self.patch_runtime.stop()
        self.temp.cleanup()

    def call(self, path, body=None, auth=None, key=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {'Origin': 'http://127.0.0.1:5174', 'Content-Type': 'application/json'}
        if auth:
            headers['Cookie'] = auth[0]
            headers['X-CSRF-Token'] = auth[1]
        if key:
            headers['Idempotency-Key'] = key
        request = Request(self.base + path, data, headers)
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response), response.headers

    def login(self, username, password):
        code, data, headers = self.call('/api/auth/login', {'username': username, 'password': password})
        self.assertEqual(code, 200)
        cookies = SimpleCookie()
        for value in headers.get_all('Set-Cookie'):
            cookies.load(value)
        return f"naxi_session={cookies['naxi_session'].value}; naxi_csrf={cookies['naxi_csrf'].value}", cookies['naxi_csrf'].value

    def judge(self, admin):
        code, response, _ = self.call('/api/admin/users', {'username': 'judge1'}, admin)
        self.assertEqual(code, 200)
        return response['user_id'], response['initial_password']

    def test_login_role_disable_and_password_hash(self):
        code, _, _ = self.call('/api/agents/dongba/evaluate', {}, key='guest_key_123456')
        self.assertEqual(code, 401)
        admin = self.login('owner', 'strong owner password 123')
        user_id, password = self.judge(admin)
        with self.store.connect() as con:
            stored = con.execute('SELECT password_hash FROM users WHERE id=?', (user_id,)).fetchone()[0]
            self.assertNotEqual(stored, password)
            self.assertTrue(stored.startswith('scrypt$'))
            token_row = con.execute('SELECT token_hash FROM auth_sessions').fetchone()[0]
            self.assertNotIn('naxi_session=', token_row)
        judge = self.login('judge1', password)
        code, _, _ = self.call('/api/admin/users', auth=judge)
        self.assertEqual(code, 403)
        code, _, _ = self.call('/api/admin/users/' + user_id + '/disable', {}, admin)
        self.assertEqual(code, 200)
        code, _, _ = self.call('/api/works', auth=judge)
        self.assertEqual(code, 401)
        code, _, _ = self.call('/api/admin/settings', {'ai_paused':True}, (admin[0], 'wrong-csrf'))
        self.assertEqual(code, 403)

    def test_session_refresh_and_origin_rules(self):
        admin = self.login('owner', 'strong owner password 123')
        code, profile, _ = self.call('/api/auth/me', auth=admin)
        self.assertEqual(code, 200)
        self.assertTrue(profile['csrf_token'])
        code, _, _ = self.call('/api/admin/settings', {'quota_music': 4},
                               (admin[0], profile['csrf_token']))
        self.assertEqual(code, 200)
        code, _, _ = self.call('/api/admin/settings', {'quota_music': 5}, admin)
        self.assertEqual(code, 403)
        self.assertTrue(mock_api.allowed_request('api.example.test', 'https://web.example.test', None,
                        production=True, configured_origins='https://web.example.test',
                        configured_hosts='api.example.test'))
        self.assertFalse(mock_api.allowed_request('api.example.test', 'https://evil.example.test', None,
                         production=True, configured_origins='https://web.example.test',
                         configured_hosts='api.example.test'))
        self.assertFalse(mock_api.allowed_request('evil.example.test', 'https://web.example.test', None,
                         production=True, configured_origins='https://web.example.test',
                         configured_hosts='api.example.test'))

    def test_quota_pause_and_works_isolation(self):
        admin = self.login('owner', 'strong owner password 123')
        first_id, first_password = self.judge(admin)
        second_id, second_password = self.store.create_judge(self.admin_id, 'judge2')
        first, second = self.login('judge1', first_password), self.login('judge2', second_password)
        self.call('/api/admin/settings', {'quota_dongba':1}, admin)
        fake = {'task_id':'a'*32,'agent':'dongba','status':'completed','model':'configured-vision',
                'result':{'source':'qwen_vision'}}
        with patch.object(self.runtime, 'dongba', return_value=fake) as provider:
            code, _, _ = self.call('/api/agents/dongba/evaluate', {}, first, 'quota_key_123456')
            self.assertEqual(code, 200)
            code, _, _ = self.call('/api/agents/dongba/evaluate', {}, first, 'quota_key_789012')
            self.assertEqual(code, 429)
            provider.assert_called_once()
        job_id, _ = self.runtime._start('music_arrange', 'owned_work_key_123', first_id)
        self.runtime._set(job_id, status='completed', result_json=json.dumps({'wav_url':'/api/artifacts/'+job_id+'/wav'}))
        code, own, _ = self.call('/api/works', auth=first)
        self.assertEqual(code, 200)
        self.assertEqual(len(own['works']), 1)
        code, other, _ = self.call('/api/works', auth=second)
        self.assertEqual(code, 200)
        self.assertEqual(other['works'], [])
        code, _, _ = self.call('/api/artifacts/'+job_id+'/wav', auth=second)
        self.assertEqual(code, 400)
        self.call('/api/admin/settings', {'ai_paused':True}, admin)
        with patch.object(self.runtime, 'dongba') as provider:
            code, _, _ = self.call('/api/agents/dongba/evaluate', {}, second, 'paused_key_123456')
            self.assertEqual(code, 403)
            provider.assert_not_called()

    def test_dance_application_is_free_and_approval_is_once(self):
        admin = self.login('owner', 'strong owner password 123')
        user_id, password = self.judge(admin)
        judge = self.login('judge1', password)
        blob = lambda raw: 'data:application/octet-stream;base64,' + base64.b64encode(raw).decode()
        body = {'video':blob(b'fake-video'), 'portrait':blob(b'fake-photo'),
                'outfit':'女1', 'background':'雪山', 'style':'写实', 'consent':True}
        with patch('web.tools.account_store.inspect_video', return_value={'duration':6.0,'width':720,'height':720}), \
             patch('web.tools.account_store.inspect_image'), patch.object(self.runtime, 'dance_submit') as provider:
            code, approval, _ = self.call('/api/agents/dance/requests', body, judge, 'approval_key_123456')
            self.assertEqual(code, 200)
            self.assertEqual(approval['status'], 'pending_approval')
            provider.assert_not_called()
            code, _, _ = self.call('/api/agents/dance/jobs', body, judge, 'direct_key_123456')
            self.assertEqual(code, 403)
            provider.assert_not_called()
            approval_path = '/api/admin/approvals/' + approval['id'] + '/approve'
            code, _, _ = self.call(approval_path, {'confirm':False}, admin)
            self.assertEqual(code, 400)
            provider.return_value = {'task_id':'b'*32,'agent':'dance','status':'PENDING',
                                     'model':'wan2.7-videoedit','result':None}
            code, done, _ = self.call(approval_path, {'confirm':True}, admin)
            self.assertEqual(code, 200)
            self.assertEqual(done['status'], 'submitted')
            code, _, _ = self.call(approval_path, {'confirm':True}, admin)
            self.assertEqual(code, 409)
            provider.assert_called_once()


if __name__ == '__main__':
    unittest.main()
