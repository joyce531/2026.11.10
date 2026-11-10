"""可选 Windows 浏览器验收；使用已有 Chrome 和 websockets，不下载浏览器。

先启动 Streamlit，再运行 python tests/browser_smoke.py http://127.0.0.1:8501
只使用临时浏览器配置及非文字图片；不修改个人浏览器配置。
"""
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from PIL import Image, ImageDraw
from websockets.sync.client import connect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.dongba_tools import get_reference_character


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8501"
    browser = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    if not browser.exists():
        raise RuntimeError("未找到本机 Chrome；此脚本不会自动安装浏览器。")
    with tempfile.TemporaryDirectory(prefix="naxi-browser-") as directory:
        root = Path(directory)
        fixture = root / "reference.png"
        get_reference_character('dongba_01')[1].save(fixture)
        wrong = Image.new("RGB", (480, 480), "white")
        ImageDraw.Draw(wrong).line((50, 240, 430, 240), fill="black", width=12)
        wrong.save(root / "wrong.png")
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([str(browser), "--headless=new", "--disable-gpu", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required", "--no-first-run",
            "--no-default-browser-check", "--remote-debugging-port=0", f"--user-data-dir={root / 'profile'}",
            "--window-size=1440,1100", "about:blank"], startupinfo=startup,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 20
            portfile = root / "profile" / "DevToolsActivePort"
            while not portfile.exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("浏览器未就绪")
                time.sleep(.1)
            port = portfile.read_text().splitlines()[0]
            with urlopen(f"http://127.0.0.1:{port}/json") as response:
                target = next(x for x in json.load(response) if x["type"] == "page")
            with connect(target["webSocketDebuggerUrl"], max_size=20_000_000) as socket:
                serial = 0
                def call(method, **params):
                    nonlocal serial
                    serial += 1
                    socket.send(json.dumps({"id": serial, "method": method, "params": params}))
                    while True:
                        message = json.loads(socket.recv(timeout=25))
                        if message.get("method") == "Runtime.exceptionThrown":
                            print(message, flush=True)
                        if message.get("method") == "Runtime.consoleAPICalled":
                            values = [str(x.get("value", "")) for x in message["params"].get("args", [])]
                            if any("Godot Engine" in value for value in values):
                                print(" ".join(values), flush=True)
                        if message.get("id") == serial:
                            if "error" in message:
                                raise RuntimeError(message["error"])
                            return message.get("result", {})
                def js(expression):
                    result = call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
                    if "exceptionDetails" in result:
                        raise RuntimeError(result["exceptionDetails"])
                    return result["result"].get("value")
                def wait(expression, timeout=25):
                    deadline = time.monotonic() + timeout
                    while not js(expression):
                        if time.monotonic() > deadline:
                            raise TimeoutError(expression + "\n" + str(js("document.body.innerText"))[-1500:])
                        time.sleep(.15)
                def button(text):
                    expression = f"Array.from(document.querySelectorAll('button')).find(x=>x.textContent.includes({json.dumps(text)}))"
                    wait(f"!!({expression}) && !({expression}).disabled && !({expression}).closest('[data-stale=true]')")
                    js(expression + ".click()")
                def upload(path):
                    doc = call("DOM.getDocument")["root"]["nodeId"]
                    node = call("DOM.querySelector", nodeId=doc, selector="input[type=file]")["nodeId"]
                    call("DOM.setFileInputFiles", nodeId=node, files=[str(path)])
                def link(text):
                    expression = f"Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes({json.dumps(text)}))"
                    wait(f"!!({expression})")
                    js(expression + ".click()")
                def screenshot(name):
                    shot = call("Page.captureScreenshot", format="png", captureBeyondViewport=True)
                    output = Path(tempfile.gettempdir()) / name
                    output.write_bytes(base64.b64decode(shot["data"]))
                    print(f"Screenshot: {output}", flush=True)
                call("Page.enable")
                call("Runtime.enable")
                call("Page.navigate", url=url)
                wait("!!Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes('进入东巴文临摹评价'))")
                wait("!document.querySelector('[data-testid=stStatusWidget]')")
                screenshot("naxi-platform-home.png")
                if '--omr' in sys.argv:
                    # Real local Audiveris; confirmation is a UI test, not musical validation.
                    from services.music_score import parse_score
                    score_path=next(Path('data/music').rglob('青花瓷五线谱/p1.jpg')).resolve()
                    call('Page.navigate',url=url+'/music')
                    wait("!!document.querySelector('input[type=file]')")
                    upload(score_path)
                    wait("document.body.innerText.includes('五线谱 → Audiveris')",60)
                    button('开始图片识谱')
                    wait("document.body.innerText.includes('识别结果校对')",210)
                    wait("!document.querySelector('[data-testid=stStatusWidget]')")
                    assert js("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.includes('确认校对并生成 MIDI')).disabled")
                    button('试听当前草稿')
                    wait("!!document.querySelector('audio')")
                    js("document.querySelector('audio').play().then(()=>true)")
                    wait("document.querySelector('audio').currentTime > 0.1")
                    js("document.querySelector('audio').pause()")
                    js("Array.from(document.querySelectorAll('[data-testid=stCheckbox]')).find(x=>x.textContent.includes('我已逐项')).querySelector('input').click()")
                    wait("!document.querySelector('[data-testid=stStatusWidget]')")
                    time.sleep(.5)
                    js("Array.from(document.querySelectorAll('[data-testid=stCheckbox]')).find(x=>x.textContent.includes('我已补正'))?.querySelector('input').click()")
                    button('确认校对并生成 MIDI')
                    wait("document.body.innerText.includes('当前校对版本已生成 MIDI')")
                    call('Browser.setDownloadBehavior',behavior='allow',downloadPath=str(root))
                    button('下载校对 MIDI')
                    deadline=time.monotonic()+20
                    while not (root/'reviewed-score.mid').exists():
                        if time.monotonic()>deadline:raise TimeoutError('review MIDI download')
                        time.sleep(.1)
                    assert parse_score((root/'reviewed-score.mid').read_bytes(),'review.mid')['note_count']>0
                    button('生成改编 MIDI 与音频')
                    wait("document.body.innerText.includes('本地规则编排 + 本地音频合成')",60)
                    screenshot('naxi-music-omr.png')
                    print('PASS: real staff upload/OMR, review gate, audio playback, MIDI download, downstream arrangement; no claim of note accuracy',flush=True)
                    return
                if '--music' in sys.argv:
                    from services.music_score import write_midi, parse_score
                    import soundfile as sf
                    call('Page.navigate',url=url+'/music')
                    wait("document.body.innerText.includes('本地规则模式')")
                    wait("!!document.querySelector('input[type=file]')")
                    notes=[dict(start=i*.5,duration=.5,pitch=[64,67,69,67][i%4],velocity=80,track=0) for i in range(60)]
                    midi_path=root/'synthetic-test.mid'
                    midi_path.write_bytes(write_midi(notes,30,['synthetic-test']))
                    upload(midi_path)
                    wait("document.body.innerText.includes('60 个音符')")
                    button('生成改编 MIDI 与音频')
                    wait("!!document.querySelector('audio')")
                    wait("document.body.innerText.includes('本地规则编排 + 本地音频合成')")
                    js("document.querySelector('audio').scrollIntoView({block:'center'})")
                    js("document.querySelector('audio').play().then(()=>true)")
                    wait("document.querySelector('audio').currentTime > 0.1")
                    js("document.querySelector('audio').pause()")
                    call('Browser.setDownloadBehavior',behavior='allow',downloadPath=str(root))
                    button('下载改编 MIDI')
                    button('下载试听 WAV')
                    deadline=time.monotonic()+20
                    while not ((root/'naxi-arrangement.mid').exists() and (root/'naxi-arrangement.wav').exists()):
                        if time.monotonic()>deadline:raise TimeoutError('MIDI/WAV download')
                        time.sleep(.1)
                    assert parse_score((root/'naxi-arrangement.mid').read_bytes(),'download.mid')['note_count']>0
                    wave,rate=sf.read(root/'naxi-arrangement.wav')
                    assert len(wave)/rate>29 and abs(wave).max()>0
                    screenshot('naxi-music-m5.png')
                    upload(fixture)
                    wait("document.body.innerText.includes('图片识谱 · 先识别，再校对')")
                    wait("!document.querySelector('audio')")
                    print('PASS: score upload, arrangement, HTML audio playback, MIDI/WAV downloads, image review routing',flush=True)
                    return
                link("进入文化学习游戏")
                wait("document.body.innerText.includes('游戏在新标签页打开')")
                wait("!!Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes('进入文化学习游戏'))")
                game_url = js("Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes('进入文化学习游戏')).href")
                link("返回首页")
                link("进入古乐创作")
                wait("document.body.innerText.includes('音乐播放') && document.body.innerText.includes('曲谱改编')")
                link("返回首页")
                link("进入打跳视频创作")
                wait("document.body.innerText.includes('生成作品预览') && document.body.innerText.includes('舞步选择')")
                link("返回首页")
                print("PASS: game/music/dance home entries and return navigation", flush=True)
                wait("!!Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes('进入东巴文临摹评价'))")
                js("Array.from(document.querySelectorAll('a')).find(x=>x.textContent.includes('进入东巴文临摹评价')).click()")
                wait("document.body.innerText.includes('Mock 模式')")
                wait("!!document.querySelector('[role=switch]')")
                # Avoid saving test sessions in the user's real learning history.
                js("window.saveCheckbox=()=>Array.from(document.querySelectorAll('[data-testid=stCheckbox]')).find(x=>x.textContent.includes('保存本次学习记录'))?.querySelector('input')")
                wait("!!saveCheckbox()")
                js("if(saveCheckbox().checked)saveCheckbox().click()")
                wait("!saveCheckbox().checked")
                time.sleep(.5)  # Wait for checkbox-triggered Streamlit rerun to finish mounting the canvas.
                wait("!document.querySelector('[data-testid=stStatusWidget]')")
                wait("document.body.innerText.includes('Mock 模式：')")
                wait("document.body.innerText.includes('本次标准示范')")
                js("window.findCanvas=()=>{const scan=r=>{const c=r.querySelector('canvas[aria-label]'); if(c)return c; for(const e of r.querySelectorAll('*'))if(e.shadowRoot){const v=scan(e.shadowRoot); if(v)return v;}return null;}; return scan(document);}")
                wait("!!findCanvas()?.naxiState && !findCanvas().getRootNode().querySelector('.submit').disabled")
                js("findCanvas().scrollIntoView({block:'center'})")
                # Real pointer events draw a deliberately wrong horizontal stroke.
                rect = js("(()=>{const r=findCanvas().getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};})()")
                x, y = rect["x"] + rect["w"]*.15, rect["y"] + rect["h"]*.5
                call("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", buttons=1, clickCount=1)
                for i in range(1, 10):
                    call("Input.dispatchMouseEvent", type="mouseMoved", x=x+rect["w"]*.07*i, y=y, buttons=1)
                call("Input.dispatchMouseEvent", type="mouseReleased", x=x+rect["w"]*.63, y=y, button="left", buttons=0, clickCount=1)
                assert js("findCanvas().naxiState.strokes.length") == 1
                js("findCanvas().getRootNode().querySelector('.submit').click()")
                wait("document.body.innerText.includes('当前书写与目标字差异较大')")
                # Rerun must preserve the drawn stroke and undo must clear it.
                wait("findCanvas().naxiState.strokes.length === 1")
                js("findCanvas().getRootNode().querySelector('.undo').click()")
                assert js("findCanvas().naxiState.strokes.length") == 0
                js("findCanvas().getRootNode().querySelector('.clear').click();findCanvas().getRootNode().querySelector('.submit').click()")
                wait("document.body.innerText.includes('没有检测到足够笔迹')")
                print("PASS: pointer drawing, submission, mismatch, retained strokes, undo, clear, blank rejection", flush=True)
                js("Array.from(document.querySelectorAll('[role=tab]')).find(x=>x.textContent.includes('模式 B')).click()")
                wait("!!document.querySelector('input[type=file]')")
                upload(fixture)
                wait("document.body.innerText.includes('模型比较用 ROI 副本')")
                wait("!document.querySelector('[data-testid=stStatusWidget]')")
                button("提交照片评价")
                wait("document.body.innerText.includes('100 / 100') || document.body.innerText.includes('100.0 / 100')")
                assert js("document.body.innerText.includes('形态较接近')")
                upload(root / "wrong.png")
                wait("document.body.innerText.includes('当前照片：wrong.png')")
                wait("!document.querySelector('[data-testid=stStatusWidget]')")
                button("提交照片评价")
                wait("document.body.innerText.includes('当前书写与目标字差异较大')")
                print("PASS: file upload, preprocessing preview, matching photo, wrong photo rejection", flush=True)
                js("Array.from(document.querySelectorAll('h3')).find(x=>x.textContent.includes('评价结果')).scrollIntoView({block:'start'})")
                wait("!document.querySelector('[data-testid=stStatusWidget]')")
                evaluation_shot = call("Page.captureScreenshot", format="png", captureBeyondViewport=True)
                output = Path(tempfile.gettempdir()) / "naxi-evaluation-browser.png"
                output.write_bytes(base64.b64decode(evaluation_shot["data"]))
                print(f"Screenshot: {output}", flush=True)
                js("document.querySelector('[data-testid=stSelectbox] [role=combobox]').scrollIntoView({block:'center'})")
                box = js("(()=>{const r=document.querySelector('[data-testid=stSelectbox] [role=combobox]').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()")
                call("Input.dispatchMouseEvent",type="mousePressed",x=box['x'],y=box['y'],button="left",clickCount=1)
                call("Input.dispatchMouseEvent",type="mouseReleased",x=box['x'],y=box['y'],button="left",clickCount=1)
                js("document.querySelector('[data-testid=stSelectbox] [role=combobox]').focus()")
                for key in ('ArrowDown','ArrowDown','Enter'):
                    call('Input.dispatchKeyEvent',type='keyDown',key=key,code=key,windowsVirtualKeyCode={'ArrowDown':40,'Enter':13}[key])
                    call('Input.dispatchKeyEvent',type='keyUp',key=key,code=key,windowsVirtualKeyCode={'ArrowDown':40,'Enter':13}[key])
                wait("document.body.innerText.includes('中文释义：水')")
                wait("!document.body.innerText.includes('上次提交快照')")
                print("PASS: target change clears previous evaluation", flush=True)
                # A fresh deep link must retain the common platform navigation.
                call("Page.navigate", url=url + "/dongba")
                wait("document.body.innerText.includes('东巴文 AI 临摹评价') && document.body.innerText.includes('返回首页')")
                print("PASS: independent /dongba access", flush=True)
                if "--game" in sys.argv and game_url.startswith("http://127.0.0.1:"):
                    call("Page.navigate", url=game_url)
                    wait("document.title === 'naxi_game'")
                    wait("!!document.querySelector('#canvas') && !document.querySelector('#status')")
                    js("new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
                    screenshot("naxi-godot-web.png")
                    print("PASS: existing Godot Web export finished engine startup", flush=True)
        finally:
            # Stop only the browser process started above, not the user's browser.
            process.terminate()
            process.wait(timeout=15)


if __name__ == "__main__":
    main()
