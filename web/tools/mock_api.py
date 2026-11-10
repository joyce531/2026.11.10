"""Single loopback Web API for existing Python agents; legacy Mock route retained."""
from __future__ import annotations

import base64
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from naxi_agents.dongba_agent import DongbaHandwritingAgent  # noqa: E402
from web.tools.agent_runtime import Runtime  # noqa: E402
from web.tools.account_store import AccountStore, AccessError  # noqa: E402
from services.dongba_vision import config_value  # noqa: E402
from services.dance_service import inspect_image  # noqa: E402

MAX_BODY = 85 * 1024 * 1024
_runtime = None
_accounts = None
LOOPBACK_HOSTS = frozenset(('127.0.0.1', 'localhost'))


def request_origin(value, *, referer=False):
    """Return a normalized HTTP origin, rejecting malformed or opaque origins."""
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        return None
    if not referer and (parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        return None
    if port is None:
        return f'{parsed.scheme}://{parsed.hostname.lower()}'
    return f'{parsed.scheme}://{parsed.hostname.lower()}:{port}'


def allowed_request(host, origin, referer, *, production=False, configured_origins='', configured_hosts=''):
    """Dev accepts loopback origins on changing Vite ports; production uses exact origins."""
    host_origin = request_origin('http://' + host)
    if not host_origin:
        return False
    host_name = urlsplit(host_origin).hostname
    if production:
        allowed = {normalized for item in configured_origins.split(',')
                   if (normalized := request_origin(item.strip()))}
        if not allowed or (not origin and not referer):
            return False
        if origin and request_origin(origin) not in allowed:
            return False
        hosts = {item.strip().lower() for item in configured_hosts.split(',') if item.strip()}
        if host_name not in hosts:
            return False
        return not referer or request_origin(referer, referer=True) in allowed
    if host_name not in LOOPBACK_HOSTS:
        return False
    for value, is_referer in ((origin, False), (referer, True)):
        if value:
            normalized = request_origin(value, referer=is_referer)
            if not normalized or urlsplit(normalized).scheme != 'http' or urlsplit(normalized).hostname not in LOOPBACK_HOSTS:
                return False
    return True


def runtime():
    global _runtime
    if _runtime is None:
        _runtime = Runtime()
    return _runtime


def accounts():
    global _accounts
    if _accounts is None:
        _accounts = AccountStore(runtime().db)
    return _accounts


def evaluate_request(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("请求格式无效。")
    image_data = payload.get("image", "")
    if not isinstance(image_data, str) or not image_data.startswith("data:image/png;base64,"):
        raise ValueError("请提交在线画布或图片转换后的 PNG。")
    raw = base64.b64decode(image_data.split(",", 1)[1], validate=True)
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("图片不能超过 5 MB。")
    method = payload.get("input_method")
    if method not in ("online_canvas", "photo_upload"):
        raise ValueError("输入方式无效。")
    with Image.open(io.BytesIO(raw)) as image:
        prepared = image.copy()
    result = DongbaHandwritingAgent(mock=True).evaluate(payload.get("character_id"), prepared, method)
    return {k: result[k] for k in ("character_id", "status", "similarity_score", "overall_feedback", "differences", "improvement_suggestions", "confidence", "source", "input_method")}


class Handler(BaseHTTPRequestHandler):
    def allowed_local_request(self):
        if len(self.headers.get_all('Host', [])) != 1:
            return False
        return allowed_request(
            self.headers.get('Host', ''), self.headers.get('Origin'), self.headers.get('Referer'),
            production=os.environ.get('NAXI_API_ENV', '').lower() == 'production',
            configured_origins=os.environ.get('NAXI_WEB_ALLOWED_ORIGINS', ''),
            configured_hosts=os.environ.get('NAXI_API_ALLOWED_HOSTS', ''),
        )

    def cors_origin(self):
        origin = self.headers.get('Origin')
        return origin if origin and self.allowed_local_request() else None

    def send_cors(self):
        origin = self.cors_origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Vary', 'Origin')

    def cookie_headers(self, token=None, csrf=None, clear=False):
        secure = '; Secure' if os.environ.get('NAXI_API_ENV', '').lower() == 'production' else ''
        same_site = os.environ.get('NAXI_COOKIE_SAMESITE', 'Lax')
        if same_site not in ('Strict', 'Lax', 'None') or (same_site == 'None' and not secure):
            same_site = 'Lax'
        age = 0 if clear else 28800
        suffix = f'; Path=/; SameSite={same_site}; Max-Age={age}{secure}'
        return [('Set-Cookie', 'naxi_session=' + (token or '') + suffix + '; HttpOnly'),
                ('Set-Cookie', 'naxi_csrf=' + (csrf or '') + suffix)]

    def session_token(self):
        try:
            cookie = SimpleCookie()
            cookie.load(self.headers.get('Cookie', ''))
            return cookie['naxi_session'].value if 'naxi_session' in cookie else None
        except Exception:
            return None

    def require_user(self, admin=False):
        user = accounts().session(self.session_token())
        if not user:
            raise AccessError('请先登录后再使用 AI 服务。', 401)
        if admin and user['role'] != 'admin':
            raise AccessError('仅管理员可以执行此操作。', 403)
        return user

    def require_csrf(self, user):
        accounts().csrf(user, self.headers.get('X-CSRF-Token'))

    def read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length <= 0 or length > MAX_BODY:
            raise ValueError('请求太大或为空。')
        body = json.loads(self.rfile.read(length))
        if not isinstance(body, dict):
            raise ValueError('请求必须是 JSON 对象。')
        return body

    def safe_error(self, exc):
        message = str(exc)[:500]
        message = re.sub(r'\bsk-[A-Za-z0-9_-]{8,}\b', '[已隐藏密钥]', message)
        message = re.sub(r'data:[^\s;]+;base64,[A-Za-z0-9+/=]+', '[已隐藏媒体]', message)
        return message

    def agent_result(self, user, kind, body, key):
        store = accounts()
        real = config_value('USE_REAL_AI', 'false').lower() == 'true'
        if kind == 'dongba':
            may_external = real
            call = lambda: runtime().dongba(body, key, user['id'])
        elif kind == 'music_recognize':
            filename = str(body.get('filename', '')).lower()
            may_external = filename.endswith(('.png', '.jpg', '.jpeg', '.webp'))
            call = lambda: runtime().recognize(body, key, user['id'])
        elif kind == 'music_arrange':
            may_external = real
            call = lambda: runtime().arrange(body, key, user['id'])
        else:
            raise ValueError('Agent 类型无效。')
        quota_kind = 'dongba' if kind == 'dongba' else 'music'
        created = store.reserve(user['id'], quota_kind, key, may_external)
        if not created:
            try:
                return runtime().by_key(key, user['id'])
            except ValueError:
                raise AccessError('任务正在处理，请等待原提交结果；不会重复调用模型。', 409) from None
        try:
            job = call()
            result = job.get('result') or {}
            external = (result.get('source') in ('qwen_vision', 'openai_responses') or
                        result.get('mode') in ('qwen_plan', 'openai_plan') or
                        (result.get('document') or {}).get('engine') in ('qwen_vision', 'openai_vision'))
            # A labelled fallback can follow a provider timeout. Keep its slot for
            # review without claiming that a model response was successfully billed.
            ambiguous = bool(may_external and not external and result.get('fallback_reason'))
            store.finish(key, job, external=external, uncertain=ambiguous)
            return job
        except Exception:
            # A provider timeout may have reached the model; hold the slot for review,
            # but never claim a billable call without a validated real-model result.
            store.finish(key, uncertain=may_external)
            raise

    def do_OPTIONS(self):
        if not self.allowed_local_request():
            self.send_json({'error': '请求来源未获允许。'}, 403)
            return
        self.send_response(204)
        self.send_cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-CSRF-Token, Idempotency-Key')
        self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()

    def send_json(self, data, status=200, extra_headers=()):
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors()
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(encoded)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)

    def send_media(self, data, media_type, filename=None):
        start, end = 0, len(data) - 1
        requested = self.headers.get('Range', '')
        if requested:
            import re
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
            if not match or (not match[1] and not match[2]):
                self.send_json({'error': '无效的媒体范围。'}, 416)
                return
            if match[1]:
                start = int(match[1])
                end = int(match[2]) if match[2] else end
            else:
                start = max(0, len(data) - int(match[2]))
            end = min(end, len(data) - 1)
            if start > end or start >= len(data):
                self.send_json({'error': '媒体范围超出文件大小。'}, 416)
                return
        self.send_response(206 if requested else 200)
        self.send_header('Content-Type', media_type)
        self.send_cors()
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if requested:
            self.send_header('Content-Range', f'bytes {start}-{end}/{len(data)}')
        if filename:
            self.send_header('Content-Disposition', f'inline; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data[start:end + 1])

    def do_POST(self):
        if not self.allowed_local_request():
            self.send_json({'error': '请求来源未获允许；请检查本地前端地址或生产来源配置。'}, 403)
            return
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            self.send_json({'error': '仅接受 application/json 请求。'}, 415)
            return
        path = urlsplit(self.path).path
        try:
            body = self.read_json()
            key = self.headers.get('Idempotency-Key', '')
            if path == '/api/auth/login':
                user, token, csrf = accounts().login(body.get('username'), body.get('password'), self.client_address[0])
                self.send_json({'user': user, 'quota': accounts().quota(user['id']), 'csrf_token': csrf},
                               extra_headers=self.cookie_headers(token, csrf))
                return
            if path == '/api/dongba/mock':
                self.send_json(evaluate_request(body))
                return
            user = self.require_user(admin=path.startswith('/api/admin/'))
            self.require_csrf(user)
            if path == '/api/auth/logout':
                accounts().revoke(self.session_token())
                self.send_json({'ok': True}, extra_headers=self.cookie_headers(clear=True))
                return
            if path == '/api/agents/dongba/evaluate':
                result = self.agent_result(user, 'dongba', body, key)
            elif path == '/api/agents/music/recognize':
                result = self.agent_result(user, 'music_recognize', body, key)
            elif path == '/api/agents/music/review':
                result = runtime().review(body)
            elif path == '/api/agents/music/arrange':
                result = self.agent_result(user, 'music_arrange', body, key)
            elif path == '/api/agents/dance/jobs':
                raise AccessError('视频生成须先由评委申请、管理员审批；不会直接提交 Wan。', 403)
            elif path == '/api/agents/dance/requests':
                result = accounts().create_dance_request(user['id'], key, body, runtime())
            elif path == '/api/quotas/requests':
                result = accounts().quota_request(user['id'], body.get('agent'))
            elif path == '/api/admin/users':
                user_id, password = accounts().create_judge(user['id'], body.get('username'), body.get('expires_at'))
                result = {'user_id': user_id, 'initial_password': password}
            elif path == '/api/admin/settings':
                result = accounts().set_settings(user['id'], body)
            elif re.fullmatch(r'/api/admin/users/[0-9a-f]{32}/(reset|disable|enable|delete|revoke|expire)', path):
                _, _, _, _, target, action = path.split('/')
                result = accounts().manage_user(user['id'], target, action, body.get('expires_at'))
            elif re.fullmatch(r'/api/admin/users/[0-9a-f]{32}/quota', path):
                target = path.split('/')[4]
                accounts().set_user_quota(user['id'], target, body.get('agent'), body.get('limit'))
                result = {'ok': True}
            elif re.fullmatch(r'/api/admin/approvals/[0-9a-f]{32}/approve', path):
                if body.get('confirm') is not True:
                    raise ValueError('批准前必须二次确认可能产生实际费用。')
                approval_id = path.split('/')[4]
                row = accounts().lock_approval(user['id'], approval_id)
                dance_key = 'dance_approval_' + approval_id
                try:
                    if not accounts().reserve(row['user_id'], 'dance', dance_key, True):
                        raise AccessError('该视频申请已有生成记录，不会重复提交。', 409)
                    job = runtime().dance_submit(accounts().approval_body(row), dance_key, row['user_id'])
                    accounts().finish(dance_key, job, external=job['status'] in ('PENDING','RUNNING','SUCCEEDED'))
                    accounts().finish_approval(approval_id, job)
                except Exception:
                    accounts().finish(dance_key, uncertain=True)
                    accounts().finish_approval(approval_id)
                    raise
                result = accounts().approval(approval_id)
            elif re.fullmatch(r'/api/admin/approvals/[0-9a-f]{32}/(reject|delete)', path):
                approval_id, action = path.split('/')[4:6]
                accounts().decide_approval(user['id'], approval_id, 'rejected' if action == 'reject' else 'cancelled')
                result = accounts().approval(approval_id)
            elif re.fullmatch(r'/api/admin/quotas/requests/[0-9a-f]{32}/(approve|reject)', path):
                request_id, action = path.split('/')[5:7]
                accounts().decide_quota(user['id'], request_id, action == 'approve')
                result = {'ok': True}
            else:
                self.send_json({'error': '接口不存在。'}, 404)
                return
            self.send_json(result)
        except AccessError as exc:
            self.send_json({'error': self.safe_error(exc)}, exc.status)
        except (ValueError, KeyError, TypeError) as exc:
            self.send_json({'error': self.safe_error(exc)}, 400)
        except Exception:
            self.send_json({'error': '服务执行失败，请检查本地后端日志与配置；未自动重试。'}, 500)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path != '/api/health' and not self.allowed_local_request():
            self.send_json({'error': '仅允许本机访问。'}, 403)
            return
        try:
            if path == '/api/health':
                self.send_json({'status': 'ok'})
            elif path == '/api/auth/me':
                user = accounts().session(self.session_token())
                self.send_json({'user': accounts().public_user(user), 'quota': accounts().quota(user['id']),
                                'csrf_token': accounts().issue_csrf(self.session_token())} if user else {'user': None})
            elif path == '/api/agents/music/assets':
                self.send_json({'assets': runtime().music_assets()})
            elif path == '/api/agents/dance/options':
                self.send_json(runtime().dance_options())
            elif path.startswith('/api/agents/dance/assets/'):
                parts = path.split('/')
                if len(parts) != 7:
                    raise ValueError('素材地址无效。')
                kind, name = parts[5], parts[6]
                data = runtime().dance_asset(kind, name)
                media_type = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp', 'BMP': 'image/bmp'}[inspect_image(data)['format']]
                self.send_media(data, media_type)
            elif path == '/api/quotas/me':
                user = self.require_user()
                self.send_json(accounts().quota(user['id']))
            elif path == '/api/works':
                user = self.require_user()
                self.send_json({'works': runtime().works(user['id'], admin=user['role']=='admin')})
            elif path == '/api/agents/dance/requests':
                user = self.require_user()
                self.send_json({'requests': accounts().approvals(user['id'])})
            elif path.startswith('/api/agents/dance/requests/by-key/'):
                user = self.require_user()
                self.send_json(accounts().approval_by_key(path.rsplit('/', 1)[-1], user['id']))
            elif re.fullmatch(r'/api/agents/dance/requests/[0-9a-f]{32}', path):
                user = self.require_user()
                self.send_json(accounts().approval(path.rsplit('/', 1)[-1], user['id']))
            elif path.startswith('/api/admin/'):
                self.require_user(admin=True)
                if path == '/api/admin/users':
                    self.send_json({'users': accounts().users()})
                elif path == '/api/admin/settings':
                    self.send_json(accounts().settings())
                elif path == '/api/admin/approvals':
                    self.send_json({'approvals': accounts().approvals()})
                elif path == '/api/admin/usage':
                    self.send_json({'usage': accounts().usage()})
                elif path == '/api/admin/quotas/requests':
                    self.send_json({'requests': accounts().quota_requests()})
                else:
                    self.send_json({'error': '接口不存在。'}, 404)
            elif path.startswith('/api/agents/dance/jobs/by-key/'):
                user = self.require_user()
                self.send_json(runtime().by_key(path.rsplit('/', 1)[-1], user['id'], user['role']=='admin'))
            elif path.startswith('/api/agents/dance/jobs/'):
                user = self.require_user()
                parts = path.split('/')
                job_id = parts[5] if len(parts) > 5 else ''
                if len(parts) == 7 and parts[6] == 'result':
                    self.send_media(runtime().artifact(job_id, 'mp4', user['id'], user['role']=='admin'), 'video/mp4', job_id + '.mp4')
                elif len(parts) == 6:
                    job = runtime().dance_status(job_id, user['id'], user['role']=='admin')
                    accounts().update_approval_for_job(job)
                    self.send_json(job)
                else:
                    self.send_json({'error': '接口不存在。'}, 404)
            elif path.startswith('/api/artifacts/'):
                user = self.require_user()
                parts = path.split('/')
                if len(parts) != 5:
                    raise ValueError('作品地址无效。')
                job_id, kind = parts[3], parts[4]
                mime = {'midi': 'audio/midi', 'wav': 'audio/wav', 'mp4': 'video/mp4'}
                if kind not in mime:
                    raise ValueError('作品格式无效。')
                self.send_media(runtime().artifact(job_id, kind, user['id'], user['role']=='admin'), mime[kind], job_id + ('.mid' if kind == 'midi' else '.' + kind))
            else:
                self.send_json({'error': '接口不存在。'}, 404)
        except AccessError as exc:
            self.send_json({'error': self.safe_error(exc)}, exc.status)
        except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
            self.send_json({'error': self.safe_error(exc)}, 400)
        except Exception:
            self.send_json({'error': '服务查询失败。'}, 500)

    def log_message(self, format, *args):
        # Do not log player images or request bodies.
        return


if __name__ == "__main__":
    if os.environ.get('NAXI_API_ENV', '').lower() == 'production' and not os.environ.get('NAXI_DATA_DIR'):
        raise SystemExit('生产模式必须配置持久化 NAXI_DATA_DIR。')
    if os.environ.get('NAXI_API_ENV', '').lower() == 'production' and not os.environ.get('NAXI_WEB_ALLOWED_ORIGINS'):
        raise SystemExit('生产模式必须配置精确 NAXI_WEB_ALLOWED_ORIGINS。')
    if os.environ.get('NAXI_API_ENV', '').lower() == 'production' and not os.environ.get('NAXI_API_ALLOWED_HOSTS'):
        raise SystemExit('生产模式必须配置精确 NAXI_API_ALLOWED_HOSTS。')
    accounts()
    bind = os.environ.get('NAXI_API_BIND') or ('0.0.0.0' if os.environ.get('NAXI_API_ENV', '').lower() == 'production' else '127.0.0.1')
    port = int(os.environ.get('PORT', '8765'))
    print(f'Naxi AI Studio API 已启动：{bind}:{port}；只有授权操作才调用模型。')
    ThreadingHTTPServer((bind, port), Handler).serve_forever()
