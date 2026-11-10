"""平台页面共享的展示组件。"""

import json
from html import escape

import streamlit as st


def apply_style():
    st.markdown("""
    <style>
    .block-container {max-width: 1140px; padding-top: 2.5rem; padding-bottom: 3rem;}
    h1, h2, h3 {font-family: 'Noto Serif SC', 'Songti SC', SimSun, serif;}
    h1 {letter-spacing: .035em;}
    p {line-height: 1.8;}
    .eyebrow {color: #AD4939; font-size: .8rem; letter-spacing: .16em; font-weight: 700;}
    .hero {border-top: 3px solid #233D4A; border-bottom: 1px solid #C6CDC9;
           padding: 2rem 0 1.5rem; margin-bottom: 1.5rem;}
    .hero h1 {font-size: clamp(2rem, 5vw, 3.6rem); line-height: 1.3; margin: .4rem 0;}
    .hero p {max-width: 48rem; font-size: 1.05rem;}
    .module-number {font: 1.2rem Georgia, serif; color: #AD4939; border-bottom: 1px solid #C6CDC9; padding-bottom: .7rem;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-radius: 12px;}
    [data-testid="stButton"] button, [data-testid="stPageLink"] a {
        transition: background-color 180ms ease, transform 180ms ease;}
    [data-testid="stButton"] button:active {transform: scale(.98);}
    [data-testid="stPageLink"] a:hover {background-color: #E4E8E4;}
    details {transition: background-color 180ms ease;}
    details[open] {background-color: #EEEDE7;}
    @media (max-width: 640px) {.block-container {padding-top: 1rem;} .hero {padding-top: 1rem;}}
    @media (prefers-reduced-motion: reduce) {*, *::before, *::after {animation: none !important; transition: none !important;}}
    </style>
    """, unsafe_allow_html=True)


def heading(number, title, description, *, show_placeholder=True):
    st.markdown(f'<div class="eyebrow">创作工坊 / {escape(number)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.write(description)
    if show_placeholder:
        st.info("开发中 · AI 服务尚未接入。当前可体验素材准备与参数设置，不会产生 AI 结果。")


def download_plan(module, parameters, filename):
    """导出当前参数，不宣称已执行任务，也不持久化上传素材。"""
    data = {"模块": module, "状态": "未执行；AI 服务尚未接入", "参数": parameters}
    st.download_button(
        "下载当前创作参数（JSON）",
        json.dumps(data, ensure_ascii=False, indent=2),
        file_name=filename,
        mime="application/json",
    )
    st.caption("下载文件只包含参数，不包含上传素材；应用不保存创作历史。")
