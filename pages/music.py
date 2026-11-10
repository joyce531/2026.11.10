"""Milestone 5: score upload -> arrangement -> locally rendered MIDI/WAV."""
import hashlib
import json
from pathlib import Path
import streamlit as st
from components.score_review import image_score_review
from ui import heading
from services.music_library import list_assets
from services.music_score import parse_score
from services.music_service import arrange_music
from services.dongba_vision import config_value, EvaluationError
from naxi_agents.music_agent import STYLES
from services import qwen_service

heading("03 / 声音", "纳西古乐 AI 曲谱改编", "上传 MIDI / MusicXML 或印刷曲谱图片，校对后制作最长 30 秒的改编试听。", show_placeholder=False)
st.info("这是纳西古乐素材参考改编实验，不是传统曲种认证复原。印刷图片识谱需人工校对；PDF / 手写谱仍在开发中。")
try:
    real = config_value('USE_REAL_AI','false').lower() == 'true'
except EvaluationError:
    real = False
st.caption("AI 规划已启用：点击生成时仅向已配置的模型服务发送曲谱摘要和素材元数据，不上传任何录音。" if real else "本地规则模式：真实解析、编排与音频合成，不调用 AI。设置 USE_REAL_AI=true 可启用 AI 编排规划。")
if real and qwen_service.enabled():
    try:st.caption('Qwen 编曲文本模型：'+qwen_service.configuration('text')[2])
    except EvaluationError as exc:st.warning(str(exc))
assets=[a for a in list_assets() if a['material_type']=='instrument' and a['analysis_status'].startswith('decoded')]
lookup={a['asset_id']:a for a in assets}
if not assets:
    st.warning('暂无可读取的素材数据库，请先运行 tools/scan_music_library.py。')
uploaded=st.file_uploader('上传流行歌曲曲谱',type=['mid','midi','musicxml','xml','mxl','pdf','png','jpg','jpeg','webp'],max_upload_size=10)
st.caption('图片限 10 MB / 1600 万像素，MIDI/MusicXML 限 2 MB；图片先自动判别简谱/五线谱，再识别与校对。PDF 暂不支持。')
score=None;raw=None;score_name='reviewed.mid'
if uploaded:
    raw=uploaded.getvalue()
    score_name=uploaded.name
    if Path(uploaded.name).suffix.lower() in ('.png','.jpg','.jpeg','.webp'):
        raw=image_score_review(raw,uploaded.name)
        score_name='reviewed.mid'
    try:
        score=parse_score(raw,score_name) if raw else None
    except ValueError as exc:st.error(str(exc))
    if score:
        st.subheader('曲谱预览')
        st.write(f"{score['format']} · {score['note_count']} 个音符 · {score['duration_seconds']:.1f} 秒 · 旋律候选声部 {score['melody_part']}")
        st.dataframe(score['melody'][:100],hide_index=True)
        st.caption('预览为实际音符事件表，不是 PDF 识谱或五线谱排版。')
        with st.expander('速度、拍号与结构标记'):
            st.json({k:score[k] for k in ('tempos','meters','markers')})
        for warning in score['warnings']:st.warning(warning)
def label(gid):
    a=lookup[gid];m=a.get('sample_mapping')
    mode='有限音域候选' if m and m['mode']=='limited_pitch' else '真实片段' if m else '仅辅助音源'
    return a['label']+' · '+mode
selected=st.multiselect('纳西乐器组合（录音标签，身份待核实）',list(lookup),default=list(lookup)[:2],format_func=label)
style=st.selectbox('改编风格参考',STYLES)
preservation=st.slider('原曲旋律保留程度（音符比例 %）',50,100,100,5)
st.caption('保留音符的音高、起点与时值不改动；降低比例会稀疏旋律。伴奏单独添加，不代表曲种专属作曲规则。')
with st.expander('当前真实素材与辅助音源',expanded=True):
    for gid in selected:
        a=lookup[gid];m=a.get('sample_mapping')
        st.write(a['label']+'：'+(m['note'] if m else '无独立可用采样，使用明确标记的通用辅助音源。'))
        st.caption(a['identity_status'])
    st.caption('有限采样只允许基准音高上下 3 半音；超范围使用通用合成音。稳定音高候选可能仍含其他声音，需听审。合奏录音不充当单件乐器。')
context=hashlib.sha256((raw or b'')+json.dumps([selected,style,preservation,real,qwen_service.enabled()]).encode()).hexdigest()
if st.session_state.get('music_context')!=context:
    st.session_state['music_context']=context
    st.session_state.pop('music_result',None)
if st.button('生成改编 MIDI 与音频',type='primary',disabled=score is None or not selected):
    try:
        with st.spinner('检查曲谱、生成编排方案并本地合成…'):
            result=arrange_music(raw,score_name,selected,style,preservation,real=real)
        st.session_state['music_result']=result
    except EvaluationError as exc:
        st.error(str(exc))
    except (ValueError,OSError,RuntimeError):
        st.error('改编未完成，请检查曲谱和本地素材。没有生成虚假作品；可运行测试工具定位格式问题。')
st.subheader('音乐播放')
result=st.session_state.get('music_result')
if result:
    st.success('Qwen AI 编排方案 + 本地音频合成' if result['mode']=='qwen_plan' else '真实 AI 编排方案 + 本地音频合成' if result['mode']=='openai_plan' else '本地规则编排 + 本地音频合成（非 AI 方案）')
    if result['fallback_reason']:st.warning(result['fallback_reason'])
    st.write(result['plan']['explanation'])
    st.caption(result['cultural_status'])
    st.audio(result['wav'],format='audio/wav')
    st.write(f"试听时长 {result['duration_seconds']:.2f} 秒；{result['note_count']} 个编排音符。")
    st.dataframe([{'录音标签':u['label'],'真实采样音符':u['sample_notes'],
                   '辅助音源音符':u['auxiliary_notes'],'真实录音片段':u['phrases'],
                   '内容核实情况':u['identity_status']} for u in result['usage']],hide_index=True)
    for limitation in result['plan']['limitations']:
        st.caption(limitation)
    st.subheader('作品保存')
    st.download_button('下载改编 MIDI',result['midi'],'naxi-arrangement.mid','audio/midi')
    st.download_button('下载试听 WAV',result['wav'],'naxi-arrangement.wav','audio/wav')
    report={k:v for k,v in result.items() if k not in ('midi','wav')}
    st.download_button('下载改编说明',json.dumps(report,ensure_ascii=False,indent=2),'naxi-arrangement.json','application/json')
    st.caption(result['midi_note'])
else:
    st.caption('上传曲谱并点击生成后，才提供真实音频试听与 MIDI/WAV 下载。作品只保存在本次会话，不自动写入云端或素材目录。')
