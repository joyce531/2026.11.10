"""舞蹈视频参数与 Wan 2.7 VideoEdit 异步 HTTP 边界。"""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import base64
import re

import cv2
from PIL import Image, ImageOps
import requests

from services.dongba_vision import config_value
from tools.upload_validation import validate_video

STEPS = ["沿用参考视频舞步", "基础动作练习（待教学资料）", "自定义动作描述（待审核）"]


@dataclass(frozen=True)
class DanceRequest:
    step: str
    costume: str
    background: str
    style: str
    duration_seconds: int
    description: str


def validate_request(request: DanceRequest):
    errors = []
    if request.step not in STEPS:
        errors.append("请选择列表中的舞步意向。")
    if not 5 <= request.duration_seconds <= 30:
        errors.append("目标时长必须在 5–30 秒之间。")
    if len(request.description) > 1000:
        errors.append("作品描述不能超过 1000 字。")
    return errors


def generate_dance_video(request: DanceRequest, reference_video: bytes):
    from tools.upload_validation import validate_video
    errors = validate_request(request)
    if errors:
        raise ValueError("；".join(errors))
    validate_video(reference_video, "reference.mp4")
    raise NotImplementedError("同步生成接口未启用；请使用显式异步提交和任务查询流程。")


MODEL = 'wan2.7-videoedit'
ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / 'data/dance/dance_videos'
PORTRAIT_DIR = ROOT / 'data/dance/dance_portrait_of_me'
OUTFIT_DIR = ROOT / 'data/dance/dance_outfits'
BACKGROUND_DIR = ROOT / 'data/dance/dance_backgrounds'
MAX_OUTPUT_BYTES = 100 * 1024 * 1024


class DanceVideoError(ValueError):
    """Safe message for UI; never includes key, URL query or returned media."""


def bundled_video():
    found = sorted(VIDEO_DIR.glob('datiao_01_step_03*.mp4'))
    return found[0] if found else None


def bundled_portrait():
    found = sorted(PORTRAIT_DIR.glob('*.jpg'))
    return found[0] if found else None


def choices(directory):
    """Use reviewed current references when present; retain original files as fallback."""
    names = {}
    for root in (directory, directory / 'current'):
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if path.is_file() and path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                names[path.stem] = path
    return names


def inspect_video(data):
    validate_video(data, 'clip.mp4')
    with TemporaryDirectory(prefix='naxi-dance-check-') as directory:
        source=Path(directory)/'clip.mp4'
        source.write_bytes(data)
        capture = cv2.VideoCapture(str(source))
        try:
            if not capture.isOpened(): raise DanceVideoError('视频无法解码，请上传有效 MP4。')
            width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps, frames = capture.get(cv2.CAP_PROP_FPS), capture.get(cv2.CAP_PROP_FRAME_COUNT)
            fourcc=int(capture.get(cv2.CAP_PROP_FOURCC))
            good, _ = capture.read()
        finally:
            capture.release()
    duration = frames / fps if fps else 0
    if not good or not (2 <= duration <= 10) or not (240 <= width <= 4096 and 240 <= height <= 4096):
        raise DanceVideoError('Wan 2.7 需要可解码、2–10 秒、宽高均为 240–4096 像素的 MP4。')
    if len(data) > 50 * 1024 * 1024:
        raise DanceVideoError('当前页面上传视频上限 50 MB。')
    codec=''.join(chr((fourcc>>(8*i))&255) for i in range(4))
    return {'width':width, 'height':height, 'fps':round(fps,2),
            'duration':round(duration,2),'codec':codec}


def inspect_image(data):
    if not data or len(data)>20*1024*1024: raise DanceVideoError('参考图必须非空且不超过 20 MB。')
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format not in ('JPEG','PNG','WEBP','BMP'):
                raise DanceVideoError('参考图只支持 JPEG、PNG、WEBP 或 BMP。')
            fmt=im.format
            width,height=ImageOps.exif_transpose(im).size
            im.verify()
    except (OSError,ValueError) as exc:
        if isinstance(exc,DanceVideoError): raise
        raise DanceVideoError('参考图片无法读取。') from None
    if not (240<=width<=8000 and 240<=height<=8000 and 1/8<=width/height<=8):
        raise DanceVideoError('参考图尺寸或长宽比不符合 Wan 2.7 要求。')
    return {'width':width,'height':height,'format':fmt}


def _settings():
    key=config_value('DASHSCOPE_API_KEY')
    raw=config_value('DANCE_API_BASE_URL') or config_value('DASHSCOPE_BASE_URL')
    if not key: raise DanceVideoError('缺少 DASHSCOPE_API_KEY；未提交视频任务。')
    parsed=urlparse(raw)
    host=parsed.hostname or ''
    if (parsed.scheme!='https' or not (host=='dashscope.aliyuncs.com' or host.endswith('.cn-beijing.maas.aliyuncs.com'))
        or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.query or parsed.fragment
        or parsed.path.rstrip('/') not in ('/api/v1','/compatible-mode/v1')):
        raise DanceVideoError('视频 API 地址必须是北京百炼 HTTPS 根地址。')
    return key, f'https://{host}/api/v1'


def _json_response(response, action):
    if response.status_code != 200:
        raise DanceVideoError(f'{action}失败（HTTP {response.status_code}），请检查模型权限或网络。')
    try: value=response.json()
    except ValueError: raise DanceVideoError(f'{action}响应不是 JSON。') from None
    if not isinstance(value,dict): raise DanceVideoError(f'{action}响应结构无效。')
    return value


def _upload_video(session,key,data):
    # The official Beijing upload-credential endpoint is global, while the
    # video task itself may use a workspace-scoped Beijing host.
    policy=_json_response(session.get('https://dashscope.aliyuncs.com/api/v1/uploads',headers={'Authorization':'Bearer '+key},
        params={'action':'getPolicy','model':MODEL},timeout=30),'获取临时上传凭证').get('data')
    if not isinstance(policy,dict): raise DanceVideoError('临时上传凭证缺少 data。')
    needed=('policy','signature','upload_dir','upload_host','oss_access_key_id','x_oss_object_acl','x_oss_forbid_overwrite')
    if any(not policy.get(k) for k in needed): raise DanceVideoError('临时上传凭证字段不完整。')
    host=urlparse(policy['upload_host'])
    if host.scheme!='https' or not (host.hostname or '').endswith('.oss-cn-beijing.aliyuncs.com') or host.username or host.password:
        raise DanceVideoError('临时上传地址不是北京 OSS 官方域名。')
    if policy['x_oss_object_acl']!='private': raise DanceVideoError('临时上传未声明私有访问，已停止。')
    object_key=policy['upload_dir'].rstrip('/')+'/naxi-dance-input.mp4'
    form=[('OSSAccessKeyId',(None,policy['oss_access_key_id'])),('Signature',(None,policy['signature'])),
          ('policy',(None,policy['policy'])),('x-oss-object-acl',(None,policy['x_oss_object_acl'])),
          ('x-oss-forbid-overwrite',(None,policy['x_oss_forbid_overwrite'])),
          ('key',(None,object_key)),('success_action_status',(None,'200')),
          ('file',('naxi-dance-input.mp4',BytesIO(data),'video/mp4'))]
    result=session.post(policy['upload_host'],files=form,timeout=90,allow_redirects=False)
    if result.status_code!=200: raise DanceVideoError(f'视频临时上传失败（HTTP {result.status_code}）。')
    return 'oss://'+object_key


def _image_item(data):
    fmt=inspect_image(data)['format']
    mime={'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp','BMP':'image/bmp'}[fmt]
    return {'type':'reference_image','url':'data:'+mime+';base64,'+base64.b64encode(data).decode('ascii')}


def submit_videoedit(video,portrait,outfit,background,request,session=None):
    """Explicit click only: one private temporary upload, one async creation request."""
    errors=validate_request(request)
    if errors: raise DanceVideoError('；'.join(errors))
    inspect_video(video)
    for image in (portrait,outfit,background): inspect_image(image)
    key,base=_settings()
    session=session or requests.Session()
    prompt=('仅编辑输入舞蹈视频。保持舞蹈动作、节奏和镜头，尽量保持原人物身份与面部特征；'
            '参考图1是人物身份，参考图2是服饰样式，参考图3是背景。'
            '按服饰参考调整服装，按背景参考调整场景。不要复制参考图中的文字、边框或其他人的脸。'
            '若参考视频人物并非身份照本人，身份保持无法保证。'
            f'画面风格：{request.style}。补充说明：{request.description[:500]}')
    phase='upload'
    try:
        video_url=_upload_video(session,key,video)
        phase='create'
        payload={'model':MODEL,'input':{'prompt':prompt,'media':[{'type':'video','url':video_url},
                 _image_item(portrait),_image_item(outfit),_image_item(background)]},
                 'parameters':{'resolution':'720P','duration':0,'audio_setting':'origin',
                               'prompt_extend':False,'watermark':True}}
        response=session.post(base+'/services/aigc/video-generation/video-synthesis',
            headers={'Authorization':'Bearer '+key,'X-DashScope-Async':'enable',
                     'X-DashScope-OssResourceResolve':'enable'},json=payload,timeout=60,allow_redirects=False)
        output=_json_response(response,'创建视频任务').get('output')
        task_id=output.get('task_id') if isinstance(output,dict) else None
        if not isinstance(task_id,str) or not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',task_id):
            raise DanceVideoError('视频任务响应缺少有效 task_id。')
        return {'task_id':task_id,'status':output.get('task_status','PENDING'),'model':MODEL}
    except requests.RequestException:
        if phase=='create':
            raise DanceVideoError('创建任务网络响应未确认；可能已创建任务，请先在百炼控制台核对后再提交，避免重复计费。') from None
        raise DanceVideoError('临时上传网络失败；未提交视频生成任务。') from None


def query_videoedit(task_id,session=None):
    if not isinstance(task_id,str) or not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',task_id):
        raise DanceVideoError('任务 ID 无效。')
    key,base=_settings();session=session or requests.Session()
    try:
        response=session.get(base+'/tasks/'+task_id,headers={'Authorization':'Bearer '+key},timeout=30)
        output=_json_response(response,'查询视频任务').get('output')
    except requests.RequestException:
        raise DanceVideoError('查询视频任务网络失败。') from None
    if not isinstance(output,dict): raise DanceVideoError('任务状态响应缺少 output。')
    status=output.get('task_status')
    if status not in ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELED','UNKNOWN'):
        raise DanceVideoError('视频任务状态无效。')
    result={'task_id':task_id,'status':status}
    if status=='SUCCEEDED':
        url=output.get('video_url')
        parsed=urlparse(url or '')
        if parsed.scheme!='https' or not (parsed.hostname or '').endswith('.aliyuncs.com'):
            raise DanceVideoError('生成结果地址无效，未下载视频。')
        result['video_url']=url
    if status=='FAILED': result['error']='视频生成失败，请在百炼控制台检查任务状态。'
    return result


def download_videoedit(url,session=None):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not (parsed.hostname or '').endswith('.aliyuncs.com'):
        raise DanceVideoError('生成结果地址无效。')
    session=session or requests.Session()
    try:
        response=session.get(url,stream=True,timeout=120,allow_redirects=False)
        if response.status_code!=200: raise DanceVideoError(f'下载生成视频失败（HTTP {response.status_code}）。')
        data=bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data)>MAX_OUTPUT_BYTES: raise DanceVideoError('生成视频超过 100 MB，已停止下载。')
        result=bytes(data)
        inspect_video(result)
        return result
    except requests.RequestException:
        raise DanceVideoError('下载生成视频网络失败。') from None
