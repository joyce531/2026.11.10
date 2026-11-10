"""五字选择、双输入、目标条件 Agent 评价。"""
import hashlib
import json
import sqlite3
import uuid
import streamlit as st
from components.handwriting_canvas import decode_canvas, handwriting_canvas
from services.glyph_data import GlyphDataService
from services.dongba_evaluator import edit_photo
from services.dongba_vision import EvaluationError, settings, use_real_ai
from services.handwriting_quality import inspect_image
from services.learning_records import LearningRecords
from naxi_agents.dongba_agent import DongbaHandwritingAgent
from tools.upload_validation import prepare_image
from services import qwen_service

st.title("东巴文 AI 临摹评价")
st.write("选择目标字，对照示范书写，比较形态与结构；不识别未知文字。")
st.info("视觉评价基线：模型分数是相似度估计，不是科学标定准确率，也不是东巴文专家结论。专属模型训练仍在开发中。")
try:
    real_enabled = use_real_ai()
except EvaluationError as exc:
    real_enabled = False
    st.warning(str(exc) + ' 已使用 Mock。')
mock = st.toggle("Mock 测试模式（不调用 API）", value=not real_enabled,
                 disabled=not real_enabled, key=f'mock-{real_enabled}')
if not real_enabled:
    st.caption('USE_REAL_AI 未开启；在 .env 中设置 USE_REAL_AI=true 后可优先使用真实 AI。')
if mock:
    st.warning("Mock 模式：仅运行本地形态测量，所有结果均明确标记为测试结果。")
else:
    try:
        if qwen_service.enabled():
            model=qwen_service.configuration('vision')[2]
            st.caption(f"视觉模型配置：{model} · 阿里云百炼 Qwen（提交成功后才产生 AI 结果）")
        else:
            _, model = settings()
            st.caption(f"真实视觉模型：{model} · OpenAI Responses API")
    except EvaluationError as exc:
        st.error(str(exc))
    st.caption("点击提交才发送标准图与本次书写图；一次非流式请求，不重试。Qwen 失败明确报错，不用本地分数替代 AI；原 OpenAI 模式保留明确标记的 Mock 回退。图片以内联方式发送，不另建云端文件库。")
store_record = st.checkbox("保存本次学习记录（仅评价文字与分数，不保存图片）", value=True)
service = GlyphDataService()
catalog = service.read_glyph_catalog()
for message in catalog.messages:
    st.warning(message)
target = None
target_id = 'missing'
st.subheader("1 · 目标字示范")
if catalog.records:
    ids = [row['glyph_id'] for row in catalog.records]
    target_id = st.selectbox("选择本次目标字", ids,
        format_func=lambda gid: next(f"{r['chinese_meaning']} · {r['english_label']} · {gid}" for r in catalog.records if r['glyph_id']==gid))
    entry = next(r for r in catalog.records if r['glyph_id']==target_id)
    loaded = service.load_reference_image(entry)
    target = loaded.image
    for message in loaded.messages:
        st.error(message)
    if target is not None:
        left,right=st.columns([1,1.5])
        left.image(target,caption="本次标准示范（原图保持不变）",width=280)
        right.write("中文释义："+entry['chinese_meaning'])
        right.write("英文名称："+entry['english_label'])
        right.write("学习提示：观察整体轮廓、各部分相对位置与比例，再临摹。")
        right.caption("名称采用当前五字目录；暂无可靠读音和笔顺资料，不作推测。")
else:
    st.error("字形目录不可用或为空；请检查 data/glyphs/glyph_catalog.csv，不会调用 AI 猜测。")
context = target_id + str(mock) + str(qwen_service.enabled()) + (hashlib.sha256(target.tobytes()).hexdigest()[:12] if target else '')
if st.session_state.get('evaluation_target') != context:
    st.session_state['evaluation_target']=context
    st.session_state.pop('dongba_result',None)


def submit(image, mode, token=None, strokes=None, raw=None):
    if target is None:
        st.error('标准图片不可用，未调用模型。')
        return
    token=token or str(uuid.uuid4())
    if st.session_state.get('last_submission')==token:
        return
    st.session_state['last_submission']=token
    st.session_state.pop('dongba_result',None)
    try:
        with st.spinner('正在检查图片并比较结构…'):
            result=DongbaHandwritingAgent(mock=mock).evaluate(target_id,image,mode,submission_id=token)
        st.session_state['dongba_result']={'evaluation':result,'reference':target.copy(),
            'handwriting':image.copy(),'raw':raw,'strokes':strokes or []}
        if store_record:
            try:
                LearningRecords().save(result)
                st.session_state['dongba_result']['saved']=True
            except (OSError,sqlite3.Error,ValueError):
                st.warning('评价已完成，但学习记录保存失败；请下载报告保留结果。')
    except (EvaluationError,ValueError) as exc:
        st.error(str(exc))


st.subheader('2 · 书写与提交')
online,photo=st.tabs(['模式 A · 在线临摹','模式 B · 拍照上传'])
with online:
    st.caption('640 × 480 画布，支持鼠标与触屏。提交保留 PNG 和有序笔画坐标；当前不评价笔顺。')
    drawing=handwriting_canvas('canvas-'+context,target is not None)
    if drawing.submission:
        try:
            payload=drawing.submission
            image=decode_canvas(payload)
            submit(image,'online_canvas',payload.get('submission_id') if isinstance(payload,dict) else None,
                   payload.get('strokes') if isinstance(payload,dict) else None)
        except ValueError as exc:
            st.session_state.pop('dongba_result',None)
            st.error(str(exc))
with photo:
    uploaded=st.file_uploader('选择纸面书写照片（PNG / JPG / JPEG）',type=['png','jpg','jpeg'],max_upload_size=10)
    st.caption('最大 10 MB、1600 万像素；原文件字节保留在本次会话。处理仅生成副本，可手动调整裁剪，避免损伤笔画。')
    processed=None
    raw=None
    if uploaded:
        try:
            raw=uploaded.getvalue()
            original,_=prepare_image(raw,uploaded.name)
            st.text(f'当前照片：{uploaded.name}')
            left,right=st.columns(2)
            with left:
                rotation=st.selectbox('逆时针旋转',[0,90,180,270],format_func=lambda a:f'{a}°')
                horizontal=st.slider('水平裁剪范围（%）',0,100,(0,100))
                vertical=st.slider('垂直裁剪范围（%）',0,100,(0,100))
                processed=edit_photo(original,rotation,(horizontal[0],vertical[0],horizontal[1],vertical[1]))
                st.image(processed,caption='旋转 / 裁剪副本',width='stretch')
            with right:
                quality,preview=inspect_image(processed)
                st.image(preview,caption='模型比较用 ROI 副本（保留方向和长宽比）',width='stretch')
                if not quality['usable']:
                    st.warning(quality['reason'])
            with st.expander('原始照片预览（已应用 EXIF 方向）'):
                st.image(original,width='stretch')
        except ValueError as exc:
            processed=None
            st.error(str(exc))
    if st.button('提交照片评价',type='primary',disabled=target is None or processed is None):
        submit(processed,'photo_upload',raw=raw)

st.subheader('3 · 评价结果')
snapshot=st.session_state.get('dongba_result')
if snapshot:
    result=snapshot['evaluation']
    st.caption('上次提交快照；修改画布或照片后请重新提交。')
    cols=st.columns(2)
    cols[0].image(snapshot['reference'],caption='本次目标示范',width='stretch')
    cols[1].image(snapshot['handwriting'],caption='本次提交的书写',width='stretch')
    labels={'match':'接近正确','close':'部分正确，仍需修改','incorrect':'明显错误，需要重新练习','uncertain':'无法可靠判断，建议重新提交'}
    source={'mock':'Mock 本地测试','quality_check':'本地质量检查（未调用模型）','openai_responses':'OpenAI 真实视觉 API','qwen_vision':'阿里云百炼 Qwen 视觉 AI'}[result['source']]
    st.caption('结果来源：'+source)
    if result.get('fallback_reason'):
        st.warning('真实 AI 不可用，已自动回退到 Mock 本地评价：'+result['fallback_reason'])
    st.subheader(labels[result['status']])
    if result['status']=='incorrect':
        st.error(result['overall_feedback'])
    else:
        st.warning(result['overall_feedback'])
    if result['status']!='uncertain':
        st.metric('视觉相似度估计（非准确率）' if result['source'] in ('openai_responses','qwen_vision') else 'Mock 本地形态计算分',f"{result['similarity_score']} / 100")
    st.write('评价置信度（未标定）：'+{'high':'高','medium':'中','low':'低'}[result['confidence']])
    if result.get('structure_analysis'):
        st.write('结构分析：'+result['structure_analysis'])
    st.markdown('**具体差异**')
    for item in result['differences'] or ['未报告明显差异，仍需自行对照示范。']:
        st.write('• '+item)
    st.markdown('**下次怎样修改**')
    for item in result['improvement_suggestions']:
        st.write('• '+item)
    with st.expander('查看工具执行记录'):
        st.write(result['tool_trace'])
        st.json(result['quality'])
    st.download_button('下载本次评价报告（不含图片）',json.dumps(result,ensure_ascii=False,indent=2),'dongba-evaluation.json','application/json')
    if snapshot['strokes']:
        st.download_button('下载本次笔画轨迹',json.dumps({'version':1,'character_id':result['character_id'],'width':640,'height':480,'strokes':snapshot['strokes']},ensure_ascii=False),'dongba-strokes.json','application/json')
    if snapshot.get('saved'):
        st.caption('学习记录已保存到本机用户数据目录；Mock/质量检查与真实 AI 来源分开标记，不保存原图或轨迹。')
else:
    st.caption('选择目标后，通过画布或照片提交，才会显示评价。')
with st.expander('本机最近学习记录'):
    try:
        records=LearningRecords().recent()
        st.caption('仅供本机单用户 Demo；未建立多用户账户隔离。')
        st.dataframe([{k:r[k] for k in ('character_id','input_method','submitted_at','status','similarity_score','source')} for r in records],hide_index=True)
    except (OSError,sqlite3.Error,ValueError,KeyError):
        st.warning('暂时无法读取学习记录。')
