"""Responses API 客户端、结构化输出及固定错误提示；不记录请求原文。"""
import base64
from io import BytesIO
import json
import logging
import os
from pathlib import Path

from dotenv import dotenv_values
from jsonschema import validate, ValidationError
from openai import OpenAI, APIConnectionError, APIStatusError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {
    'type':'object', 'additionalProperties':False,
    'properties': {
        'status': {'type':'string','enum':['match','close','incorrect','uncertain']},
        'similarity_score': {'type':'number','minimum':0,'maximum':100},
        'overall_feedback': {'type':'string'},
        'differences': {'type':'array','items':{'type':'string'}},
        'improvement_suggestions': {'type':'array','items':{'type':'string'}},
        'confidence': {'type':'string','enum':['high','medium','low']},
    },
    'required':['status','similarity_score','overall_feedback',
                'differences','improvement_suggestions','confidence'],
}


class EvaluationError(ValueError):
    pass


def config_value(name, default=''):
    try:
        values = dotenv_values(ROOT/'.env', encoding='utf-8-sig', interpolate=False)
    except (OSError, UnicodeError):
        raise EvaluationError('无法读取根目录 .env，请检查文件权限和 UTF-8 编码。') from None
    return (os.environ.get(name, values.get(name)) or default).strip()


def use_real_ai():
    return config_value('USE_REAL_AI', 'false').lower() == 'true'


def settings():
    return config_value('OPENAI_API_KEY'), config_value('DONGBA_VISION_MODEL','gpt-6-luna')


def create_client():
    key, model = settings()
    if not key:
        raise EvaluationError('缺少 OPENAI_API_KEY：请在项目根目录 .env 配置，或选择 Mock 测试模式。')
    for name in ('openai','httpx','httpcore','dotenv.main'):
        logging.getLogger(name).disabled = True
    try:
        client = OpenAI(api_key=key, base_url='https://api.openai.com/v1', timeout=45, max_retries=0)
    except Exception:
        raise EvaluationError('无法初始化 OpenAI 客户端，请检查本地配置。') from None
    return client, model


def image_url(image):
    buffer = BytesIO()
    image.convert('RGB').save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def request(client, **kwargs):
    try:
        return client.responses.create(store=False, stream=False, max_output_tokens=1600, **kwargs)
    except APIConnectionError:
        raise EvaluationError('视觉 API 网络连接失败或超时，请检查网络/代理后重新提交；未生成评价。') from None
    except APIStatusError as exc:
        body = exc.body if isinstance(exc.body,dict) else {}
        detail = body.get('error',body)
        detail = detail if isinstance(detail,dict) else {}
        code = detail.get('code') or getattr(exc,'code',None)
        if exc.status_code == 401:
            message = 'API 密钥认证失败，请检查 OPENAI_API_KEY。'
        elif code in ('insufficient_quota','billing_hard_limit_reached','billing_not_active'):
            message = 'API 余额或配额不足，请检查账户计费与项目预算。'
        elif exc.status_code in (403,404) or code in ('model_not_found','unsupported_model'):
            message = '模型不可用或无访问权限，请检查 DONGBA_VISION_MODEL 和账户权限。'
        elif exc.status_code == 429:
            message = 'API 请求限流，请稍后重新提交。'
        else:
            message = '视觉 API 拒绝请求或服务异常，请检查模型是否支持图片、工具调用和结构化输出。'
        raise EvaluationError(message) from None
    except Exception:
        raise EvaluationError('视觉请求失败，未生成评价；为保护密钥不显示原始异常。') from None


def parse_result(text):
    try:
        result = json.loads(text)
    except (ValueError,TypeError):
        raise EvaluationError('东巴评价内容不是合法 JSON；未保存虚假结果。') from None
    try:
        validate(result, SCHEMA)
    except ValidationError as exc:
        path='.'.join(str(x) for x in exc.absolute_path) or '$'
        raise EvaluationError('东巴评价字段校验失败：'+path[:80]+'；未保存虚假结果。') from None
    if not result['overall_feedback'].strip():
        raise EvaluationError('东巴评价业务校验失败：overall_feedback 为空。')
    if not result['improvement_suggestions'] or not all(x.strip() for x in result['improvement_suggestions']):
        raise EvaluationError('东巴评价业务校验失败：improvement_suggestions 为空或含空项。')
    if result['status'] in ('match','close') and result['confidence'] == 'low':
        result['status'] = 'uncertain'
        result['overall_feedback'] = '模型把握不足，无法可靠判断，请提供更清晰的完整字形后重试。'
    return result
