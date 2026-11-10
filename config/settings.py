"""应用公共限制与部署配置；不在此保存任何密钥。"""

import os
from urllib.parse import urlsplit

import streamlit as st

APP_NAME = "Naxi AI Studio"
IMAGE_MAX_MB = 10
VIDEO_MAX_MB = 50
IMAGE_MAX_PIXELS = 16_000_000


def setting(name, default=""):
    """环境变量优先，其次 Streamlit secrets；不自动读取 .env。"""
    if name in os.environ:
        return os.environ[name].strip()
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def game_settings():
    url = setting("GODOT_WEB_URL")
    if url:
        try:
            parsed = urlsplit(url)
            if (parsed.scheme not in ("http", "https") or not parsed.hostname
                    or parsed.username or parsed.password or any(c.isspace() for c in url)):
                raise ValueError
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("GODOT_WEB_URL 必须是无用户名、密码的有效 HTTP(S) 地址。") from exc
    return url, setting("GODOT_WEB_DIR", "D:/livingnaxi-web2")
