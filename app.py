"""启动入口：统一配置、导航和首页。"""

import streamlit as st

from config.settings import APP_NAME
from ui import apply_style


def home():
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">纳西文化智能学习与创作平台</div>
      <h1>Naxi AI Studio</h1>
      <p>从互动探索到一笔、一声、一段舞。走进文化学习游戏，
      或选择独立的临摹、音乐与视频创作工坊，开启你的学习与创作。</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("四个独立入口 · 三个专业 Agent 逐步接入 · 共享文化知识与基础设施")
    modules = [
        ("01 / 探索", "纳西文化互动学习游戏", "进入已有 Godot 教学游戏，在互动中探索文化内容。平台通过网页入口连接游戏，保留独立游戏体验。", "pages/game.py", "进入文化学习游戏", "已有 Web 导出 · 本机或网址接入"),
        ("02 / 文字", "东巴文临摹评价 Agent", "选择五个基础目标字，在线书写或上传照片，通过双图比较获得结构反馈与修改建议。", "pages/dongba.py", "进入东巴文临摹评价 →", "视觉 Agent 已接入 · 提供免费 Mock 测试"),
        ("03 / 声音", "纳西古乐 AI 创作 Agent", "上传 MIDI / MusicXML 曲谱，选择现有乐器录音与风格参考，试听并下载最长 30 秒的改编作品。", "pages/music.py", "进入古乐创作 →", "曲谱改编 · 真实采样与辅助音源明确标记"),
        ("04 / 动作", "纳西打跳 AI 视频创作 Agent", "上传舞蹈视频与个人照片，选择服饰和背景素材，显式提交 Wan 2.7 异步任务。", "pages/dance.py", "进入打跳视频创作 →", "素材选择可用 · 视频接口待首次真实验证"),
    ]
    for start in (0, 2):
        for column, (number, title, description, path, action, status) in zip(st.columns(2, gap="large"), modules[start:start+2]):
            with column, st.container(border=True):
                st.markdown(f'<div class="module-number">{number}</div>', unsafe_allow_html=True)
                st.subheader(title)
                st.write(description)
                st.caption(status)
                st.page_link(path, label=action)
    st.divider()
    st.subheader("让学习有依据，让创作有边界")
    st.write("三个专业模块独立运行，不设总控 Agent。东巴文提供双图评价，音乐提供曲谱改编与本地合成，视频已接入异步接口代码、尚待真实生成验证。AI 结论与风格实验不是专家文化认证。")
    with st.expander("当前可体验的内容"):
        st.write("鼠标画布、照片旋转裁剪、Mock 评价、音乐本地规则编排与合成、舞蹈素材预览无需密钥。视频生成需本人明确点击提交并使用已配置的百炼 Key；目前只完成离线接口测试。")


st.set_page_config(page_title=APP_NAME, page_icon="✍️", layout="wide")
apply_style()
home_page = st.Page(home, title="首页", icon="🏠", default=True)
page = st.navigation([
    home_page,
    st.Page("pages/game.py", title="互动学习游戏", url_path="game"),
    st.Page("pages/dongba.py", title="东巴文 AI 临摹评价"),
    st.Page("pages/music.py", title="纳西古乐 AI 创作"),
    st.Page("pages/dance.py", title="纳西打跳 AI 视频"),
], position="top")
if page.url_path:
    st.page_link(home_page, label="← 返回首页")
page.run()
st.divider()
st.caption("Naxi AI Studio · 纳西文化智能学习与创作平台 ｜ Milestone 3B · 东巴文双图评价")
