import streamlit as st

from config.settings import game_settings
from services.game_service import start_local_game

st.title("纳西文化互动学习游戏")
st.write("进入原有 Godot 教学游戏，体验纳西文化互动学习。游戏与三个专业 Agent 入口独立，学习进度暂未与平台互通。")


@st.cache_resource(show_spinner=False)
def local_game(directory):
    return start_local_game(directory)


try:
    url, directory = game_settings()
    if url:
        st.info("已配置游戏网页地址；链接可用性以打开后的实际页面为准。")
    elif directory:
        server = local_game(directory)
        url = f"http://127.0.0.1:{server.server_port}/index.html"
        st.info("已启动本机游戏文件服务。点击下方入口后，浏览器将加载现有 Godot 网页版。")
        st.caption("首次加载约 121 MB。仅适用于在这台电脑浏览器中演示；远程访问平台时需另行配置可访问的游戏网址。")
    else:
        st.warning("游戏网页尚未接入，请配置 GODOT_WEB_URL 或本机导出目录 GODOT_WEB_DIR。")
    if url:
        st.link_button("进入文化学习游戏", url, type="primary")
        st.caption("游戏在新标签页打开。返回本标签页即可继续使用平台，或点击上方“返回首页”。")
except (ValueError, OSError) as exc:
    st.warning(str(exc))
    st.button("进入文化学习游戏", disabled=True)
    st.caption("平台其他模块仍可使用；游戏资源不会被自动复制或重新导出。")

with st.expander("运行与资料说明"):
    st.write("请使用支持 WebAssembly 与 WebGL 2.0 的浏览器。若没有声音，先点击游戏画面；若无法加载，检查游戏文件是否完整及浏览器图形支持。")
    st.write("平台直接读取已有 Web 导出，不修改原 Godot 工程。网页游戏的文化内容沿用原游戏；这不等于已将这些内容核验并导入 Agent 的共享知识库。")
