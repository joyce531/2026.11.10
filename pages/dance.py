"""Wan 2.7 VideoEdit demo: explicit submit, manual status refresh, local preview."""
import hashlib
from time import monotonic

import streamlit as st

from config.settings import VIDEO_MAX_MB
from ui import download_plan, heading
from services.dance_service import (BACKGROUND_DIR, OUTFIT_DIR, DanceRequest,
    DanceVideoError, bundled_portrait, bundled_video, choices, inspect_image,
    inspect_video, submit_videoedit, query_videoedit, download_videoedit)

heading('04 / 动作', '纳西打跳 AI 视频创作',
        '上传舞蹈视频与个人照片，选择服饰和场景。生成使用 Wan 2.7 VideoEdit；结果须人工检查身份与动作。')
st.caption('仅点击“提交生成任务”会上传素材并创建计费任务；刷新页面、修改选项和查看预览不会调用视频生成 API。')

video_path=bundled_video()
portrait_path=bundled_portrait()
outfits=choices(OUTFIT_DIR)
backgrounds=choices(BACKGROUND_DIR)

left,right=st.columns([1.1,1],gap='large')
with left:
    st.subheader('舞蹈视频与身份照片')
    video_mode=st.radio('视频来源',['项目测试片段','上传自己的 MP4'],horizontal=True)
    uploaded_video=st.file_uploader('上传本人舞蹈 MP4',type=['mp4'],
        max_upload_size=VIDEO_MAX_MB,key='dance-video-upload') if video_mode=='上传自己的 MP4' else None
    video=(uploaded_video.getvalue() if uploaded_video else
           video_path.read_bytes() if video_mode=='项目测试片段' and video_path else None)
    video_meta=None
    if video:
        try:
            video_meta=inspect_video(video)
            st.video(video,format='video/mp4')
            st.caption(f"原始视频 · {video_meta['width']}×{video_meta['height']} · {video_meta['duration']} 秒；不是生成结果。")
        except ValueError as exc:st.error(str(exc))
    else:st.info('请选择或上传 2–10 秒 MP4。')
    if video_mode=='项目测试片段':
        st.warning('项目测试片段含多人，照片中的人不一定在视频中；模型无法保证生成视频保留该照片的身份。正式体验请上传本人单人舞蹈视频。')

    photo_mode=st.radio('身份照片来源',['项目测试照片','上传个人照片'],horizontal=True)
    uploaded_photo=st.file_uploader('上传本人清晰照片',type=['jpg','jpeg','png'],
        max_upload_size=20,key='dance-photo-upload') if photo_mode=='上传个人照片' else None
    portrait=(uploaded_photo.getvalue() if uploaded_photo else
              portrait_path.read_bytes() if photo_mode=='项目测试照片' and portrait_path else None)
    photo_ok=False
    if portrait:
        try:
            inspect_image(portrait);photo_ok=True
            st.image(portrait,caption='身份参考照片 · 并非生成结果',width=230)
        except DanceVideoError as exc:st.error(str(exc))
    else:st.info('请选择或上传身份参考照片。')

with right:
    st.subheader('服饰与背景参考')
    outfit_name=st.selectbox('服饰参考',list(outfits) if outfits else ['暂无素材'])
    background_name=st.selectbox('背景参考',list(backgrounds) if backgrounds else ['暂无素材'])
    outfit=outfits[outfit_name].read_bytes() if outfit_name in outfits else None
    background=backgrounds[background_name].read_bytes() if background_name in backgrounds else None
    if outfit:st.image(outfit,caption=f'服饰参考：{outfit_name}（原图含文字和边框）',width=230)
    if background:st.image(background,caption=f'背景参考：{background_name}',width=300)
    style=st.selectbox('视觉风格',['自然写实','水彩画感','舞台光影'])
    description=st.text_area('补充说明',placeholder='例如：保持原有舞蹈节奏、尽量保留人物脸部特征。',max_chars=500)
    st.caption('服饰和背景图片的文化说明、来源与授权仍需人工核实。模型可能无法同时准确保留身份、动作、服饰和场景。')
    consent=st.checkbox('我确认有权使用所选视频和人物照片，并同意将本次素材发送给阿里云百炼处理。')

request=DanceRequest('沿用参考视频舞步',outfit_name,background_name,style,
                     round(video_meta['duration']) if video_meta else 9,description)
ready=bool(video_meta and photo_ok and outfit and background)
fingerprint=(hashlib.sha256(video+portrait+outfit+background+
             (outfit_name+background_name+style+description).encode('utf-8')).hexdigest()
             if ready else None)
job=st.session_state.get('dance_video_job')
pending=bool(job and job['status'] in ('PENDING','RUNNING'))
download_plan('纳西打跳 AI 视频',{'视频来源':video_mode,'照片来源':photo_mode,
    '服饰':outfit_name,'背景':background_name,'风格':style,'描述':description},'naxi-dance-plan.json')

if st.button('提交生成任务',type='primary',disabled=not (ready and consent) or pending):
    try:
        with st.spinner('正在私有上传视频并创建 Wan 2.7 任务…'):
            created=submit_videoedit(video,portrait,outfit,background,request)
        st.session_state['dance_video_job']={**created,'fingerprint':fingerprint,
                                              'last_poll':0.0,'video':None}
        st.success('任务已创建。生成通常需要数分钟；点击下方按钮刷新状态。')
    except (DanceVideoError,ValueError) as exc:st.error(str(exc))

job=st.session_state.get('dance_video_job')
st.subheader('生成作品')
if not job:
    st.info('尚无生成任务。上方预览仅为原始素材。')
else:
    st.write(f"任务状态：{job['status']} · 模型：{job.get('model','wan2.7-videoedit')}")
    if job['fingerprint']!=fingerprint:
        st.warning('当前素材或参数已改变；下方任务对应上一次提交。')
    if job['status'] in ('PENDING','RUNNING') or (job['status']=='SUCCEEDED' and not job.get('video')):
        if st.button('刷新生成状态'):
            if monotonic()-job['last_poll']<15:
                st.info('请至少间隔 15 秒再查询。')
            else:
                try:
                    outcome=query_videoedit(job['task_id'])
                    job['last_poll']=monotonic()
                    job['status']=outcome['status']
                    if job['status']=='SUCCEEDED':
                        job['video']=download_videoedit(outcome['video_url'])
                    elif job['status']=='FAILED':job['error']=outcome.get('error')
                    st.rerun()
                except DanceVideoError as exc:st.error(str(exc))
    if job['status']=='SUCCEEDED' and job.get('video'):
        st.video(job['video'],format='video/mp4')
        st.download_button('下载生成 MP4',job['video'],file_name='naxi-dance-video.mp4',mime='video/mp4')
        st.caption('Wan 2.7 生成结果；请人工检查人物身份、动作、服饰和背景。')
    elif job['status']=='SUCCEEDED':st.warning('任务成功，但视频尚未下载。请重新查询该任务。')
    elif job['status'] in ('FAILED','CANCELED','UNKNOWN'):
        st.error(job.get('error','任务未生成可用视频；请检查百炼任务状态。'))

st.caption('原素材保持只读；项目不持久保存玩家上传文件。点击提交后，视频和参考图会发送给百炼临时空间及视频服务；云端保留遵循服务商政策。')
