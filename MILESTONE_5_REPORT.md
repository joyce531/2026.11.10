# Milestone 5 — 曲谱改编与音乐素材库

2026-11-08。范围仅音乐模块，保留其他模块。用户选定首个歌曲为《青花瓷》，随后确认暂时没有 MIDI/MusicXML，因此本轮交付可上传曲谱运行的完整模块和明确标记的 30 秒人工测试旋律，不声称已完成《青花瓷》改编。

## 扫描与数据库

- 指定三处目录共有 13 个实际 MP3，全部完整流式解码成功：白沙目录 2、洞经目录 3、乐器标签 8。
- 5 个合奏文件均为 44100 Hz 双声道；独立目录中 7 个为 48000 Hz 单声道，标签“笛子”为 44100 Hz 双声道。
- 发现 `笛子.mp3` 与 `baisha_01.mp3` 完全相同，禁止当作独立笛子采样。
- 排除该重复后：5 个自动稳定音高候选（人面竹胡琴、十面云锣、曲项琵琶、波伯、碰铃）；2 个自动原录音片段（口弦、苏古笃）。这些名称仅是文件标签，尚未确认单音纯净度和真实乐器身份。
- 数据库：`data/music/music_library.sqlite3`；镜像：`data/music/music_manifest.json`。详见 [扫描报告](docs/MUSIC_ASSET_INVENTORY.md) 和 [数据库说明](docs/MUSIC_DATABASE.md)。没有完整音域采样库；没有上传原录音。

## 已实现

1. 页面取消自由创作；只有曲谱上传、事件预览、乐器组合、洞经/白沙参考、旋律保留程度、生成、播放和下载。
2. MIDI 0/1：音符、速度变化、拍号、标记、多个非打击声部；候选旋律由平均音高最高声部选出。MusicXML/MXL：基础 partwise、时值、休止、和弦、声部回退/前进、延音线、移调、速度与小节。提供明确的解析局限提示。
3. 最长 30 秒片段；按用户比例均匀保留旋律音符，保留音符的音高和时间不变，附加声部单独编排。短谱不伪造补足 30 秒。
4. 真实 OpenAI 方案规划（gpt-6-luna 默认、MUSIC_MODEL 可配置）：一次非流式 Responses 请求，输出经过 Schema 和素材 ID 校验的角色/疏密/解释方案。复用现有 .env 配置读取和安全客户端，不改东巴代码。模型只接收曲谱摘要及声学测量，不接收音频。
5. Python 执行查询、解析、MIDI 编排、采样移调与 WAV 合成。不是语言模型直接生成音频，也不是自主多 Agent 框架。UI 和报告显示实际执行步骤。
6. USE_REAL_AI 非 true 或请求失败时执行明确标记的本地规则方案；音符编排与音频生成仍真实执行，不是随机样例文件。
7. 对有限候选优先用 ±3 半音采样；超音域用通用辅助音；片段型素材加入一次原录音点缀；合奏只参考。逐项报告实际采样音符/辅助音符/片段数。

## 测试结果

- 全部 48 项单元/页面测试通过，包括 8 项新音乐测试；pip check 无冲突。
- 39 个 Python 文件语法检查通过；git diff --check 通过；Streamlit 健康检查 HTTP 200。
- 测试覆盖素材解码、重复文件禁用、MIDI 变速、MusicXML 延音/MXL、格式拒绝、XML 实体安全、选择校验、30 秒合成、音量/时长、MIDI 回读、旋律保留、一次 AI 请求及回退。
- 一次真实 API 规划测试通过，source=`openai_plan`，model=`gpt-6-luna`，30 秒、68 个输出音符：人面竹胡琴标签素材 45 个采样音符 + 15 个辅助音符；曲项琵琶标签轨 8 个辅助音符；口弦标签 1 段原录音。模型与工具职责分离，报告保留真实方案。
- Chrome 无头浏览器测试通过：上传人工 MIDI、生成、HTML audio 播放时间推进、下载 MIDI/WAV 后实际解码、拒绝 PNG 曲谱并清除旧结果。没有把仅显示播放器当作播放成功。
- Streamlit 实际启动成功。测试中出现的沙箱网络限制通过授权真实 API 测试解决；本轮结束无未解决的测试失败。

测试 Demo 文件在 `%TEMP%/naxi-music-m5-demo/`：input.mid、arrangement.mid、arrangement.wav、report.json。report 明确说明是人工测试旋律。没有将临时作品写入原音频目录。

## 文件变更

新增：

- `services/music_library.py`、`services/music_score.py`、`services/music_render.py`
- `naxi_agents/music_agent.py`
- `tools/scan_music_library.py`、`tools/test_music_arrangement.py`
- `tests/test_music.py`
- `data/music/music_library.sqlite3`、`data/music/music_manifest.json`
- `docs/MUSIC_ASSET_INVENTORY.md`、`docs/MUSIC_DATABASE.md`、本报告

修改：`pages/music.py`、`services/music_service.py`（旧契约保留，新增改编入口）、`app.py`（仅音乐能力文案）、`tests/test_app.py`、`tests/browser_smoke.py`、`requirements.txt`、`.env.example`、`README.md`、`AGENTS.md`（音乐定位/说明）。

新增依赖 mido 1.3.3、soundfile 0.14.0、defusedxml 0.7.1；soundfile 自动带入 cffi/pycparser。只安装在现有 .venv，无训练框架，无 ffmpeg 外部服务，无新 Agent SDK。

原音频、东巴文页面/Agent/视觉服务、打跳服务/页面、Godot 服务/页面、.env、.gitignore 等 22 个受保护文件的 SHA-256 与修改前快照比对完全一致。未提交或推送 Git；原 Godot 工程及其资源未触及。

## 待完善与明确未实现

- 《青花瓷》具体改编：等待用户提供曲谱。
- PDF/图片光学识谱：未实现，明确拒绝，不伪造音符。
- 传统调式、曲种规范、真实配器关系和专家听审：未完成；现有声学统计不能证明作品属于洞经或白沙。不能把此基线宣传为正宗纳西古乐生成模型。
- 完整音域/力度/奏法、精准保时移调、乐句音乐学切分、多轨录音分离：未实现。短采样循环可能有机械感或杂音，辅助音不是纳西音色。
- 复杂 MusicXML 反复/跳房/装饰音/无音高谱拒绝，建议导出展开后的 MIDI；MIDI 弯音和踏板控制器未渲染。自动旋律选取可能选错声部。
- 曲谱预览是事件表，不是五线谱排版；MIDI 的 GM 音色不等于 WAV 的真实录音音色。
- 仅本机 Demo，会话保存作品；没有用户账户、云端作品库或模型训练。

## 启动与复验

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
# 浏览器 http://localhost:8501/music
.\.venv\Scripts\python.exe -X utf8 -B tools/scan_music_library.py
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -B tools/test_music_arrangement.py
```

真实方案用现有 .env 的 OPENAI_API_KEY，设置 USE_REAL_AI=true，可选 MUSIC_MODEL=gpt-6-luna。准备曲谱后直接网页上传，或：

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tools/test_music_arrangement.py --score "你的曲谱完整路径.mid" --live
```

`--live` 产生一次模型规划请求，失败明确报告回退，不上传音频。建议试听与确认后手动提交本里程碑，当前未自动提交。
