"""Image recognition and explicit human review before returning MIDI to the music page."""
import hashlib
import json
import pandas as pd
import streamlit as st

from services.score_image import load_score_image, preprocess, classify
from services.score_omr import recognize_jianpu, recognize_staff, audiveris_executable, TONICS
from services.score_omr import recognize_staff_vision
from services import qwen_service
from services.score_review import jianpu_rows, preview_audio, confirm_midi, review_hash, validate_rows


@st.cache_data(show_spinner=False)
def prepare_upload(data,name,crop):
    image=load_score_image(data,name)
    left,top,right,bottom=crop
    if left>=right or top>=bottom:raise ValueError('裁剪范围无效。')
    image=image.crop((round(left*image.width/100),round(top*image.height/100),round(right*image.width/100),round(bottom*image.height/100)))
    processed,ink,meta=preprocess(image)
    return image,processed,meta,classify(ink)


def image_score_review(data,name):
    st.subheader('图片识谱 · 先识别，再校对')
    qwen=qwen_service.enabled()
    st.caption('仅面向清晰印刷谱，单次一页/片段。Qwen 模式使用视觉模型识别两种曲谱；OpenAI 模式保留简谱视觉识别与五线谱 Audiveris。所有结果须人工校对。')
    upload_id=hashlib.sha256(data).hexdigest()[:16]
    with st.expander('裁剪识别范围（建议一至两行；请保留调号）'):
        horizontal=st.slider('识谱水平范围 %',0,100,(0,100),key='omr-x-'+upload_id)
        vertical=st.slider('识谱垂直范围 %',0,100,(0,100),key='omr-y-'+upload_id)
    crop=(horizontal[0],vertical[0],horizontal[1],vertical[1])
    try:
        original,processed,meta,detection=prepare_upload(data,name,crop)
    except ValueError as exc:
        st.error(str(exc));return None
    cols=st.columns(2)
    cols[0].image(original,caption='本次范围（原文件不变）',width='stretch')
    cols[1].image(processed,caption='OpenCV 光照归一与倾斜校正',width='stretch')
    kind=detection['kind']
    if kind=='unknown':
        st.warning('当前图片无法可靠判断简谱或五线谱，请手动指定。')
        selected=st.selectbox('选择识谱类型',['请选择','简谱','五线谱'],key='omr-kind-'+upload_id+str(crop))
        kind={'简谱':'jianpu','五线谱':'staff'}.get(selected)
    else:
        st.success('自动判断：'+{'jianpu':'简谱 → OpenCV + 视觉 AI','staff':'五线谱 → '+('Qwen 视觉 AI' if qwen else 'Audiveris')}[kind])
    with st.expander('自动判别依据'):
        st.json({**detection,**meta})
    identity=hashlib.sha256((upload_id+str(crop)+str(kind)+str(qwen)).encode()).hexdigest()[:20]
    key='omr-doc-'+identity
    if qwen:
        st.caption('点击识谱只将当前裁剪图片发送到已配置的阿里云百炼；一次请求，无 Mock 回退。')
        try:st.caption('Qwen 视觉模型：'+qwen_service.configuration('vision')[2])
        except ValueError as exc:st.warning(str(exc))
    elif kind=='staff':
        try:st.caption('已找到本机 Audiveris：'+audiveris_executable().name)
        except ValueError as exc:st.warning(str(exc))
    elif kind=='jianpu':
        st.caption('点击识别将把当前裁剪图片发送至已配置的 OpenAI，单次请求、无 Mock 回退。使用 MUSIC_OMR_MODEL / OPENAI_API_KEY / USE_REAL_AI。')
    if st.button('开始图片识谱',key='omr-start-'+identity,disabled=not kind or key in st.session_state):
        try:
            with st.spinner('识谱中；尚未生成 MIDI…'):
                doc=(recognize_staff_vision(processed) if qwen else recognize_staff(processed)) if kind=='staff' else recognize_jianpu(processed)
            st.session_state[key]=doc
        except (ValueError,OSError,RuntimeError) as exc:
            st.error(str(exc))
    doc=st.session_state.get(key)
    if not doc:return None
    st.caption('实际识别引擎：'+doc['engine']+'；结果均为待校对草稿，不是识别正确率。')
    if doc.get('structure'):st.write('可见乐曲结构：'+doc['structure'])
    if 'key_signature' in doc:st.write('调号：'+str(doc['key_signature'] or '未知，须人工确认')+'；拍号：'+str(doc.get('meter') or '未知'))
    for warning in doc.get('warnings',[]):st.warning(warning)
    has_limitations=doc['coverage']!='complete' or bool(doc.get('unsupported_symbols'))
    if has_limitations:
        st.warning('当前结果仅覆盖已识别片段或未展开符号；不能当作完整正确歌曲。')
        for item in doc.get('unsupported_symbols',[]):st.warning(item)
    if 'export_bytes' in doc:
        st.download_button('下载 Audiveris 原始 MusicXML（未校对）',doc['export_bytes'],doc['export_name'],key='omr-export-'+identity)
    if kind=='jianpu':
        choices=['未知 / 请补充']+TONICS
        tonic=st.selectbox('调号音名（不能默认 1=C）',choices,index=choices.index(doc['tonic_note']) if doc['tonic_note'] else 0,key='omr-tonic-'+identity)
        degree=st.number_input('调号等号左侧级数（如 1=A 填 1，6=A 填 6）',1,7,doc.get('tonic_degree') or 1,key='omr-degree-'+identity)
        octave=st.number_input('调号所指无点音的参考八度（中央 C 为 C4，请听辨校正）',1,6,4,key='omr-octave-'+identity)
        bpm=st.number_input('速度 BPM（未印速度时 120 仅供校对试听，须确认）',20.,300.,float(doc.get('bpm') or 120),key='omr-bpm-'+identity)
        st.caption('识别拍号：'+str(doc.get('meter') or '未知，需核对')+'；数字级数按自然音阶换算，临时升降记号另加。缺少调号时不生成试听或 MIDI。')
        try:initial=jianpu_rows(doc,tonic,int(degree),int(octave),bpm)
        except ValueError as exc:st.warning(str(exc));return None
        tempos=[{'time':0.,'bpm':bpm}]
    else:
        original_bpm=float(doc['tempos'][0]['bpm'])
        bpm=st.number_input('五线谱校对速度 BPM（请与原图核对）',20.,300.,min(300.,max(20.,original_bpm)),key='omr-staff-bpm-'+identity)
        factor=bpm/original_bpm
        initial=[{**r,'start':None if r['start'] is None else r['start']/factor,'duration':None if r['duration'] is None else r['duration']/factor} for r in doc['rows']]
        tempos=[{'time':t['time']/factor,'bpm':t['bpm']*factor} for t in doc['tempos']]
    revision=hashlib.sha256(json.dumps([initial,tempos],ensure_ascii=False).encode()).hexdigest()[:16]
    st.subheader('识别结果校对')
    st.caption('时间单位：秒；MIDI 音高 60=C4、69=A4。休止不发声但保留时间。可增删行、修改音高/起点/时长；uncertain 标记只读，不会自动变成正确。')
    table=st.data_editor(pd.DataFrame(initial),num_rows='dynamic',hide_index=True,key='omr-editor-'+identity+revision,
        disabled=['symbol','uncertain','issue'],column_config={
            'start':st.column_config.NumberColumn('起点（秒）',min_value=0.,format='%.4f'),
            'duration':st.column_config.NumberColumn('时长（秒）',min_value=.001,format='%.4f'),
            'pitch':st.column_config.NumberColumn('MIDI 音高',min_value=0,max_value=127,step=1),
            'rest':st.column_config.CheckboxColumn('休止'),
            'voice':st.column_config.TextColumn('声部'),
            'symbol':st.column_config.TextColumn('原始符号/位置'),
            'uncertain':st.column_config.CheckboxColumn('识别不确定'),
            'issue':st.column_config.TextColumn('待核对原因'),
            'reviewed':st.column_config.CheckboxColumn('该项已校对')})
    rows=table.astype(object).where(pd.notna(table),None).to_dict('records')
    for r in rows:
        if r.get('uncertain') is None:r['uncertain']=True
        if r.get('voice') is None:r['voice']='melody'
    try:stamp=review_hash(rows,tempos)
    except ValueError:
        st.error('表格包含无效数值，请补正后继续。');return None
    st.caption(f"待检查标记：{sum(bool(r.get('uncertain')) and not r.get('reviewed',False) for r in rows)} 项。")
    if st.button('试听当前草稿（非校对确认）',key='omr-preview-'+identity):
        try:st.session_state['omr-audio-'+identity]=(stamp,preview_audio(rows))
        except ValueError as exc:st.error(str(exc))
    audio=st.session_state.get('omr-audio-'+identity)
    if audio and audio[0]==stamp:st.audio(audio[1],format='audio/wav')
    confirmed=st.checkbox('我已逐项核对全部音符、调号、八度及节奏（同时确认所有标记项）',key='omr-confirm-'+stamp)
    accept=st.checkbox('我已补正或接受当前片段范围；按印刷顺序处理，不展开未支持符号',key='omr-accept-'+stamp) if has_limitations else True
    if st.button('确认校对并生成 MIDI',type='primary',disabled=not confirmed or not accept,key='omr-final-'+identity):
        try:
            checked=[{**r,'reviewed':True} for r in rows]  # Explicit user's all-note acknowledgement above.
            midi=confirm_midi(checked,tempos,confirmed=confirmed,limitations_accepted=accept,has_limitations=has_limitations)
            st.session_state['omr-midi-'+identity]=(stamp,midi)
        except ValueError as exc:st.error(str(exc))
    result=st.session_state.get('omr-midi-'+identity)
    if result and result[0]==stamp and confirmed and accept:
        st.success('当前校对版本已生成 MIDI，可继续下方纳西古乐改编。修改草稿后须重新确认。')
        st.download_button('下载校对 MIDI',result[1],'reviewed-score.mid','audio/midi',key='omr-midi-download-'+identity)
        st.download_button('下载识别与校对记录',json.dumps({'engine':doc['engine'],'coverage':doc['coverage'],
            'warnings':doc.get('warnings',[]),'unsupported_symbols':doc.get('unsupported_symbols',[]),
            'rows':rows,'all_notes_confirmed':True,'tempos':tempos},ensure_ascii=False,indent=2),
            'score-review.json','application/json',key='omr-review-download-'+identity)
        return result[1]
    return None
