"""Shared Bailian Chat Completions adapter. No retries, guessed models or raw logs."""
import json
import logging
import re
from urllib.parse import urlparse

from openai import DefaultHttpxClient
from jsonschema import validate, ValidationError
from openai import OpenAI, APIConnectionError, APIStatusError
from services.dongba_vision import config_value, image_url, EvaluationError

DIAGNOSTIC_LOG = logging.getLogger('naxi.qwen.diagnostics')


def _diagnostic(event):
    """Development-only metadata. Never include prompts, response text, URLs or keys."""
    try:
        enabled=config_value('QWEN_DEBUG','false').lower()=='true'
    except EvaluationError:
        return  # Diagnostics must never break the product request.
    if enabled:DIAGNOSTIC_LOG.warning('Qwen diagnostic: %s',json.dumps(event,ensure_ascii=False,sort_keys=True))


def note_fallback(*,kind,source):
    _diagnostic({'event':'fallback','kind':kind,'source':source,'mock_fallback':source=='mock'})


def note_business_failure(*,kind,field):
    _diagnostic({'event':'validation','kind':kind,'failure_type':'business_validation',
                 'field':field,'mock_fallback':False})


def _content_text(content):
    if isinstance(content,str):return content
    # Some compatible servers return a single text content part.
    if isinstance(content,list) and len(content)==1 and isinstance(content[0],dict):
        part=content[0]
        if isinstance(part.get('text'),str):return part['text']
    raise EvaluationError('Qwen 返回内容类型不受支持；没有生成可用结果。')


def _schema_path(error):
    path='$'
    for part in error.absolute_path:
        path+=f'[{part}]' if isinstance(part,int) else '.'+str(part)
    if error.validator=='required':
        match=re.fullmatch(r"'([^']+)' is a required property",error.message)
        if match and match.group(1) in error.schema.get('properties',{}):
            path+='.'+match.group(1)
    return path[:160]


def enabled():
    provider=config_value('AI_PROVIDER','qwen').lower()
    if provider not in ('qwen','openai'):
        raise EvaluationError('AI_PROVIDER 只能是 qwen 或 openai。')
    return provider=='qwen'


def configuration(kind):
    if kind not in ('text','vision'):raise EvaluationError('Qwen 模型用途无效。')
    names=('DASHSCOPE_API_KEY','DASHSCOPE_BASE_URL','QWEN_'+kind.upper()+'_MODEL')
    values=[config_value(n) for n in names]
    missing=[n for n,v in zip(names,values) if not v]
    if missing:raise EvaluationError('缺少 Qwen 配置：'+', '.join(missing)+'；请保存根目录 .env。')
    key,url,model=values
    if kind=='vision' and model.lower().startswith('auto-model'):
        raise EvaluationError('QWEN_VISION_MODEL 不能使用文本智能路由；请填写直接支持图片的视觉模型。')
    try:
        parsed=urlparse(url)
        port=parsed.port
    except ValueError:
        raise EvaluationError('DASHSCOPE_BASE_URL 地址格式无效。') from None
    host=parsed.hostname or ''
    beijing=host=='dashscope.aliyuncs.com' or host.endswith('.cn-beijing.maas.aliyuncs.com')
    if (parsed.scheme!='https' or not beijing or parsed.username or parsed.password or
        parsed.query or parsed.fragment or port not in (None,443) or
        parsed.path.rstrip('/')!='/compatible-mode/v1' or '{' in url):
        raise EvaluationError('DASHSCOPE_BASE_URL 须为北京地域官方 HTTPS OpenAI 兼容接口根地址，以 /compatible-mode/v1 结尾。')
    return key,url.rstrip('/'),model


def request_json(*,kind,instructions,schema,text='',images=(),client=None):
    """Exactly one JSON-mode request; schema validated locally, no API fallback."""
    if kind=='text' and images:
        raise EvaluationError('文本智能路由只接受文本，图片必须调用 QWEN_VISION_MODEL。')
    if kind=='vision' and not images:
        raise EvaluationError('视觉识别请求必须包含图片。')
    key,url,model=configuration(kind)
    for name in ('openai','httpx','httpcore','httpx2','httpcore2','dotenv.main'):
        logging.getLogger(name).disabled=True
    owned=client is None
    diagnostic={'event':'request','kind':kind,'model':model,'http_status':None,
                'finish_reason':None,'input_tokens':None,'output_tokens':None,
                'content_type':None,'json_parsed':False,'schema_valid':False,
                'schema_error_path':None,'mock_fallback':False,'failure_type':None}
    try:
        if owned:
            client=OpenAI(api_key=key,base_url=url,max_retries=0,timeout=120,
                          http_client=DefaultHttpxClient(follow_redirects=False,timeout=120))
        # The auto-model route accepts text-only Chat Completions. Use a plain
        # string there; image content is constructed only for the vision route.
        content=text or '按要求分析并返回 JSON。'
        if images:
            content=[{'type':'text','text':content}]
            for im in images:content.append({'type':'image_url','image_url':{'url':image_url(im)}})
        kwargs=dict(model=model,stream=False,extra_body={'enable_thinking':False},
            response_format={'type':'json_object'},messages=[
                {'role':'system','content':instructions+'\n请以 JSON 格式严格输出指定字段，不增加额外字段；未知内容依 Schema 使用 null，不猜测。\n'+json.dumps(schema,ensure_ascii=False)},
                {'role':'user','content':content}])
        # The official structured-output guidance warns that max_tokens can cut
        # JSON mid-object. Do not pass it, even for long music-score results.
        if owned:
            raw=client.chat.completions.with_raw_response.create(**kwargs)
            diagnostic['http_status']=raw.status_code
            response=raw.parse()
        else:
            response=client.chat.completions.create(**kwargs)
        usage=getattr(response,'usage',None)
        if usage is not None:
            diagnostic['input_tokens']=getattr(usage,'prompt_tokens',None) or getattr(usage,'input_tokens',None)
            diagnostic['output_tokens']=getattr(usage,'completion_tokens',None) or getattr(usage,'output_tokens',None)
        if not response.choices:
            diagnostic['failure_type']='empty_choices'
            raise EvaluationError('Qwen API 请求成功，但响应没有 choices；没有生成可用结果。')
        choice=response.choices[0]
        diagnostic['finish_reason']=choice.finish_reason
        content=getattr(choice.message,'content',None)
        diagnostic['content_type']=type(content).__name__
        if choice.finish_reason!='stop':
            diagnostic['failure_type']='incomplete_response'
            reason='输出长度受限或被截断' if choice.finish_reason=='length' else '输出被过滤或未正常结束'
            raise EvaluationError('Qwen '+reason+'（finish_reason='+str(choice.finish_reason) + '）；没有生成可用结果。')
        if content is None:
            diagnostic['failure_type']='empty_content'
            raise EvaluationError('Qwen 返回空内容；没有生成可用结果。')
        try:content=_content_text(content)
        except EvaluationError:
            diagnostic['failure_type']='unsupported_content_type'
            raise
        if not content.strip():
            diagnostic['failure_type']='empty_content'
            raise EvaluationError('Qwen 返回空内容；没有生成可用结果。')
        stripped=content.strip()
        fence=re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```',stripped,flags=re.IGNORECASE)
        if fence:stripped=fence.group(1).strip()
        try:
            result=json.loads(stripped)
        except json.JSONDecodeError as exc:
            diagnostic['failure_type']='json_parse'
            raise EvaluationError(f'Qwen 返回内容不是合法 JSON（解析位置 {exc.pos}）；没有生成可用结果。') from None
        diagnostic['json_parsed']=True
        try:
            validate(result,schema)
        except ValidationError as exc:
            diagnostic['failure_type']='schema_validation'
            diagnostic['schema_error_path']=_schema_path(exc)
            raise EvaluationError('Qwen JSON 字段校验失败：'+diagnostic['schema_error_path']+
                                  '（'+str(exc.validator)+'）；没有生成可用结果。') from None
        # JSON decoder accepts NaN; refuse non-finite values even for nullable fields.
        try:json.dumps(result,allow_nan=False)
        except (ValueError,TypeError):
            diagnostic['failure_type']='invalid_json_value'
            raise EvaluationError('Qwen JSON 含无效数值或类型；没有生成可用结果。') from None
        diagnostic['schema_valid']=True
        return result,model
    except EvaluationError:raise
    except APIConnectionError:
        diagnostic['failure_type']='api_connection'
        raise EvaluationError('Qwen 网络连接失败或超时；未重试、未切换模型。') from None
    except APIStatusError as exc:
        diagnostic['failure_type']='api_status'
        diagnostic['http_status']=exc.status_code
        message={401:'Qwen 密钥认证失败，请检查北京地域密钥。',403:'Qwen 无权限或模型未开通。',
                 404:'Qwen 模型或接口地址不可用，请核对控制台配置。',429:'Qwen 配额不足或请求限流，请检查账户。'}.get(exc.status_code,
                 'Qwen 服务拒绝请求；请检查模型是否支持图片、非思考和 JSON 模式。')
        raise EvaluationError(message) from None
    except Exception:
        diagnostic['failure_type']='client_error'
        raise EvaluationError('Qwen 调用失败；为保护密钥不显示原始异常。') from None
    finally:
        _diagnostic(diagnostic)
        if owned and client is not None:client.close()
