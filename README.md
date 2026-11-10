# Naxi AI Studio

> Public repository note: original glyph images, music, dance videos, costume and background references, personal photos, game media copies, and presentation screenshots remain local until public redistribution rights are confirmed. The music SQLite index contains machine-specific absolute paths and is also excluded. A fresh clone can build, but media playback and some AI workflows require legally provisioned assets in the documented paths.

纳西文化智能学习与创作平台。Milestone 3B 已接通 **Dongba Handwriting Evaluation Agent**：指定目标字 → 在线临摹或照片 → 双图视觉比较 → 中文结构反馈 → 本机学习记录。保留统一首页、Godot 游戏、古乐与打跳入口。Milestone 5 音乐模块已提供曲谱改编、MIDI/WAV 合成；舞蹈视频已完成异步接口代码及离线测试，尚未真实生成验证。不设置总控 Agent。

## Milestone 5B：舞蹈视频生成（离线接入阶段）

`/dance` 现在默认读取项目现有的 `datiao_01_step_03` MP4（约 8.93 秒）和已上传的个人正面照片，也可在页面上传自己的 MP4 与 JPEG/PNG 照片。服饰直接从 `data/dance/dance_outfits/` 的 4 张图片选择，背景从 `data/dance/dance_backgrounds/` 的 6 张图片选择；页面会预览原素材。项目示范视频有多人，不能保证生成者与照片是同一人；正式体验建议使用本人单人舞蹈视频。

只有勾选素材使用与云端处理确认、点击「提交生成任务」时，程序才将视频私有上传至百炼临时空间并创建 **一次** `wan2.7-videoedit` 异步任务。点击「刷新生成状态」查询已有任务，不会重复创建；成功后下载返回的 MP4 到当前 Streamlit 会话供播放与下载。未接入完整自主 Agent，也尚未进行真实视频生成测试。结果要人工检查人脸、动作、服饰和场景。服饰原图带文字/手机边框，可能影响生成效果，且来源与文化描述仍待核实。

API 沿用根 `.env` 中的 `DASHSCOPE_API_KEY` 和 `DASHSCOPE_BASE_URL`；不必另填 `DANCE_API_KEY`。可选 `DANCE_API_BASE_URL` 指向同一北京工作空间的原生 `/api/v1` 根地址。现有兼容接口 `/compatible-mode/v1` 会在服务中转换为同域名 `/api/v1`，但该 Key 的视频模型权限仍须在百炼控制台核对。**本里程碑只做离线测试，没有调用生成 API，也没有费用。**

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
# 免费离线检查
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_dance_video tests.test_app -v
```

第一次真实生成：打开 `/dance`，优先上传获本人授权的 2–10 秒单人 MP4 和清晰个人照，选服饰/背景，核对预览并勾选确认，然后点击一次「提交生成任务」。等待约 1–5 分钟，间隔至少 15 秒点击「刷新生成状态」；出现作品后试听/检查并下载 MP4。真实生成按百炼视频模型规则计费，请先确认账户配额与模型权限。[Wan 2.7 VideoEdit 官方接口](https://help.aliyun.com/en/model-studio/wan-video-editing-api-reference)、[百炼临时文件上传说明](https://help.aliyun.com/en/model-studio/get-temporary-file-url)。

## Milestone 4B：阿里云百炼 Qwen 接入

视觉 JSON 诊断：图片请求使用百炼 `json_object`，不设置 `max_tokens`，并在提示中明确要求 JSON；本地再校验字段。开发时可在启动 Streamlit 的 PowerShell 会话中设置 `$env:QWEN_DEBUG='true'`，查看模型 ID、HTTP 状态、`finish_reason`、输入/输出 Token、内容类型和 JSON/Schema 校验状态。诊断不记录密钥、图片或模型回复全文；关闭时设置 `$env:QWEN_DEBUG='false'`。东巴文失败会显示明确标记的 Mock 回退，曲谱识别失败不会生成虚构音符。修复记录见 [Qwen 视觉 JSON 修复报告](MILESTONE_4B_JSON_FIX_REPORT.md)。

当前默认提供方为 `qwen`。共享服务 `services/qwen_service.py` 复用已安装 SDK 的百炼兼容 Chat Completions 接口，一次非流式请求、无重试/自动换模型，JSON 模式加本地 Schema 校验。2026-11-08 已分别实测文本智能路由、东巴双图视觉比较和简谱片段识别；这些调用成功不代表音符识别准确率或东巴文专家认可。

根 `.env` 保留已有 `DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`，另配置：

```dotenv
AI_PROVIDER=qwen
USE_REAL_AI=true
QWEN_TEXT_MODEL=
QWEN_VISION_MODEL=
```

模型变量必须填入百炼控制台已开通的准确模型 ID，代码不设默认值、不猜名称。文本模型用于编曲规划；视觉模型用于双图评价和曲谱识别。需支持非思考模式 JSON 输出，视觉模型还需支持图片。当前 `.env` 已配置 `QWEN_TEXT_MODEL=auto-model-9e5f7930` 与 `QWEN_VISION_MODEL=qwen3.8-flash`；本轮补充 `USE_REAL_AI=true`，页面默认真实 AI 优先。`.env` 被 Git 忽略，密钥未写入示例或报告。

北京 Base URL 为官方 HTTPS 兼容根地址，以 `/compatible-mode/v1` 结尾，不能加 `/chat/completions`。支持 `dashscope.aliyuncs.com` 和北京业务空间域名。依据：[百炼视觉接口](https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai)、[JSON 与模型支持范围](https://help.aliyun.com/zh/model-studio/qwen-structured-output)。

- 东巴文复用画布/拍照，双图比较输出接近正确、部分正确、明显错误、无法判断。模型分数标为视觉估计。Qwen 失败时自动回退到明确标记的 Mock 本地测量，并显示回退原因；手动 Mock 仍可用。
- 曲谱由 OpenCV 自动分类，Qwen 模式两类图片都交给视觉模型；不确定时手选。低置信与未知音高/节奏保留待校对标记；简谱缺调号不默认 C。确认后才生成 MIDI。
- 编曲只把曲谱摘要和可分配乐器元数据发给文本智能路由，随后 Python 执行 MIDI 与本地采样合成，录音不上传。Qwen 失败时使用明确标记的本地规则方案；页面显示回退原因。
- 仅点击提交按钮才调用。单次识谱最多 128 事件，建议裁剪清晰一至两行；复杂反复、换调、装饰等仍需人工校正。

文本智能路由仅支持纯文本请求；共享服务拒绝把图片送给它。图片直接发给 `QWEN_VISION_MODEL`。简谱视觉识谱失败时不自动编造音符；五线谱本地 Audiveris 路线仍可通过 `AI_PROVIDER=openai` 使用。

原 OpenAI/Audiveris 路线保留，须明确设 `AI_PROVIDER=openai`；下文历史 OpenAI 配置只适用于该路线。完整文件和测试清单见 [Milestone 4B 报告](MILESTONE_4B_REPORT.md)。

## 启动与体验

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

打开 http://localhost:8501 ，进入“东巴文 AI 临摹评价”（独立地址 `/dongba`）。其他入口是 `/game`、`/music`、`/dance`。

1. 从五个基础字形中选择目标：人、山、水、火、太阳。名称采用用户提供的目录映射，不编造读音或专家审核。
2. `USE_REAL_AI=true` 时优先真实 AI；未配置或其他值时只用 Mock，不收费。页面仍保留 Mock 开关，可临时选择本地测试。
3. 在根目录 `.env` 中配置下面变量，保存后刷新页面，默认启用真实视觉评价（也可手动开启 Mock）。每次提交读取配置，无需把 Key 写入代码。
4. 在线画布可用鼠标或触屏，支持粗细、颜色、撤销和清空；点击“提交画布评价”。或在照片页上传 PNG/JPG/JPEG，确认裁剪预览后点击“提交照片评价”。
5. 查看标准图与作品对照、中文状态、结构分析、差异和建议；可下载报告及画布笔画坐标。

```dotenv
USE_REAL_AI=true
OPENAI_API_KEY=在你本机填写真实密钥
DONGBA_VISION_MODEL=gpt-6-luna
```

不要把上述占位文字当作密钥。`.env` 已被 Git 忽略；示例文件只保留变量名。进程环境变量优先于 `.env`。默认模型 gpt-6-luna 已通过真实双图基线测试，模型须支持图片和结构化输出。API 不可用自动回退本地 Mock，显示回退原因；不重试、不自动换模型、不把 Mock 冒充真实 AI。

## 真正执行的 Agent 流程

`naxi_agents/dongba_agent.py` 使用现有 OpenAI Python SDK **Responses API**。本环境没有安装 openai-agents；旧顶层 `agents/` 也与其导入名潜在冲突，因此项目实现放在 naxi_agents，旧 Protocol 文件保留。

- 通过 `character_id` 查询现有 CSV 的 `glyph_id`，二者在当前五字 Demo 中取相同值；没有修改七字段 CSV。
- 强制读取并检查标准图；缺失或无效时停止，绝不让模型猜测。
- Pillow/NumPy 检查空白、过暗、过小、明显模糊；不合格时返回 `uncertain` 并明确标记“未调用模型”。没有新增 OpenCV 依赖。
- 生成带留白的 512×512 ROI 副本，保留长宽比与方向，不改原图、不补笔、不镜像。上传原始字节保留在会话中。
- 一次请求同时发送**标准图和玩家图两张 PNG**，只比较像不像目标，不识别未知字。
- 使用严格 JSON Schema 返回六字段：status、similarity_score、overall_feedback、differences、improvement_suggestions、confidence；后端校验取值及非空反馈/建议。
- 每次点击提交最多一次 API 请求，非流式，45 秒超时，关闭自动重试，`store=False`；无工具调用循环或额外模型。标准缺失、空白等无效输入在本地停止，不收费。
- API Key 缺失、网络/模型失败、响应不完整或 JSON 不合法时自动调用原 Mock 算法，页面和保存记录标记 source=mock、mock_mode=true、fallback_reason。模型正常返回 uncertain 时保留真实结果，不触发回退。

保留原 Agent 类入口以兼容页面，但当前是单次视觉服务，不宣称模型自主调用工具。在线画布 submission_id 防止 Streamlit 重绘重复请求；修改控件/下载报告不会自动调用 API，再次明确点击提交才开始新评价。图片以内联请求发送，不上传 Files API、不建立云端图片库；store=False 不等于服务商零日志保留承诺。结构化输出参数参照 [OpenAI 官方文档](https://developers.openai.com/api/docs/guides/structured-outputs)。

| JSON status | 页面显示 |
| --- | --- |
| match | 基本掌握 |
| close | 接近正确 |
| incorrect | 需要重新练习 |
| uncertain | 图片质量不足，建议重新提交 |

模型输出使用上述六字段；原 Mock 的 structure_analysis 保留兼容展示。真实模型的 similarity_score 是**视觉估计，不是科学标定准确率**；Mock 分是本地图像计算，二者不混用。uncertain 的 0 是不可评分占位，界面不展示分数。confidence 也未经校准。模型低置信度的正面结论会降为 uncertain。API 超时、密钥错误等会显示原因并回退 Mock，不包装为真实评价。

## 输入与学习记录

图片限 10 MB、1600 万像素，验证真实格式与扩展名；支持 EXIF 方向、透明底合成、手动旋转和百分比裁剪。ROI 是副本，复杂阴影、透视、格线和遮挡仍可能干扰判断，必要时请手动紧贴完整字形裁剪。模糊阈值为工程启发式，不能保证覆盖所有劣质照片。

画布提交包含 PNG 和每笔 width/color/points，保留笔画顺序与坐标；后端限制点数与坐标范围，当前没有时间戳/压力，也不评价规范笔顺。可显式下载轨迹 JSON。切换目标或 Mock/真实模式会清除旧评价，修改图片后须重新提交，避免把上次结果误认为本次结果。

勾选“保存本次学习记录”后自动保存元数据到：

```text
%LOCALAPPDATA%\NaxiAIStudio\learning.sqlite3
```

保存 character_id、输入方式、UTC 提交时间、状态、相似度、结构反馈及修改建议，并记录 source、mock_mode、model、工具轨迹和质量测量。submission_id 防止重复写入。**不自动保存原图、上传字节或笔画坐标**；原始数据只保留当前会话。保存失败会提示但不丢失页面结果，可下载报告。历史记录按 Mock/真实/质量检查区分，质量检查的 0 不代表不相似。取消勾选可只体验不保存。

数据库默认位于 Git 仓库之外，不修改 .gitignore。当前是本机单用户 Demo，历史记录不做用户账户隔离；没有自动收集训练集或训练模型。真实模式提交会向 OpenAI 发送两张图；Mock 模式不会上传第三方。

## 字形目录和接口

`data/glyphs/glyph_catalog.csv` 只含：glyph_id、chinese_meaning、english_label、image_file、image_path、image_width、image_height。`glyph_manifest.json` 同步保存七字段、实际格式、SHA-256 与非空白检查信息。五张 original 图片保持原样，详细预览见 [建档报告](docs/DONGBA_GLYPH_INVENTORY.md)。

新增字形时放置原图、填写明确提供的名称，读取真实尺寸与哈希，同步 CSV/JSON；不根据图片猜释义。说明见 [数据指南](docs/DONGBA_DATA_COLLECTION_GUIDE.md)。

```python
from services.glyph_data import GlyphDataService
service = GlyphDataService()
result = service.find_glyphs("dongba_01")
if result.records:
    image_result = service.load_reference_image(result.records[0])
    print(image_result.messages)
    reference = image_result.image  # Pillow 图像或 None
```

页面现在直接读五字 CSV，不自动改写旧 `data/dongba/characters.json`。旧 JSON 加载器、训练记录 Schema 与几何测试图形保留用于兼容和算法测试，不再是页面的目标来源。`data/handwriting_samples/` 仍是未来人工样本目录，没有自动写入。

## 文件职责

| 文件 | 职责 |
| --- | --- |
| app.py、ui.py | 原有首页、导航与样式；仅更新能力说明 |
| pages/dongba.py | 目标选择、双输入、Mock 开关、对照结果和学习记录 |
| components/handwriting_canvas.js/.py | Canvas、PNG/轨迹提交、校验 |
| naxi_agents/dongba_agent.py | 目标读取、质量门槛、一次双图请求、Mock 回退 |
| tools/dongba_tools.py | 受控目标获取和本地形态测量 |
| services/dongba_vision.py | 密钥/模型配置、图片编码、API 错误与结构化输出校验 |
| services/handwriting_quality.py | 质量检查与不破坏原图的 ROI 副本 |
| services/learning_records.py | 用户目录 SQLite 元数据及幂等保存 |
| services/dongba_evaluator.py | 保留原有形态原型：覆盖、比例、重心、区域分布 |
| services/glyph_data.py | 七字段 CSV 查询与图片安全读取 |
| tools/test_dongba_agent.py | 默认 Mock、显式 --live 的双图基线测试 |
| tests/test_dongba_agent.py | 不联网的 Agent、质量、异常与学习记录测试 |

原有 Godot 和打跳服务/页面不改动；古乐按 Milestone 5 升级为曲谱改编。游戏仍默认从 `D:/livingnaxi-web2` 按需启动只读本机文件服务，新标签页打开；无需复制资源。首载约 121 MB，浏览器需 WebAssembly/WebGL 2.0。本机服务不能供远程观众通过 127.0.0.1 访问，部署时配置 GODOT_WEB_URL；也可通过 GODOT_WEB_DIR 改本机导出目录。游戏配置仍使用环境变量或 Streamlit secrets，不从 .env 读取。未修改原 Godot 工程或导出。

## 测试

使用当前 `.venv`，未新增依赖；openai 3.46.0、python-dotenv 1.2.4 已安装并记录在 requirements.txt。

```powershell
# 不消耗 API 费用
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B tools/test_dongba_agent.py
.\.venv\Scripts\python.exe -m pip check
# 启动 Streamlit 后，用已有 Chrome 做 Mock 浏览器回归
.\.venv\Scripts\python.exe tests/browser_smoke.py http://127.0.0.1:8501
# 显式真实测试：两组图片，最多两次计费请求
.\.venv\Scripts\python.exe -X utf8 tools/test_dongba_agent.py --live
```

单元/页面测试覆盖清晰图、PNG 画布载荷、空白/模糊/过暗/过小、不同图形、缺标准图、缺 Key、请求失败、JSON 校验、单次双图请求、自动回退与幂等保存。测试使用临时图片和数据库，不污染真实学习记录。

历史两轮版本的真实双图基线（本轮为省额度未重新调用真实 API）：标准图缩放副本返回 close/92，无关矩形返回 incorrect/2，两组实际调用了测量工具。这不是玩家手写数据集准确率；同图缩放仍被模型提出细微差异，说明视觉判断需要更多真实样本验证。

## 当前限制

仅五字、没有专属训练、没有专家标定。模型可能误判细节、镜像或近似结构；本地阈值也会受分辨率与背景影响。当前不做透视矫正、自动笔顺评分或文化解释，不声称能够替代教师。真实评价可能比 Mock 慢；API 故障自动回退且显式标记。当前单次版本使用模拟 API 验证，请在真实模式只提交一张清晰作品进行低成本现场检查。

原 Milestone 3B 的历史交付与验证记录见 [MILESTONE_3B_REPORT.md](MILESTONE_3B_REPORT.md)。历史 MILESTONE_3A_AUDIT.md 保留为当时状态审计，不代表当前能力。


## Milestone 5：纳西古乐曲谱改编

音乐入口 `/music` 只提供 **上传曲谱 → 选择乐器组合/风格参考/旋律保留程度 → 生成 → 试听与下载**，已取消自由创作。支持 MIDI 0/1、基础 partwise MusicXML 与 MXL，以及需要人工校对的印刷曲谱图片（PNG/JPG/JPEG/WEBP）。PDF 暂不支持。复杂反复/跳房/装饰音建议先在制谱软件展开并导出 MIDI。

原录音已扫描：13 个 MP3 均完整解码。**笛子.mp3 与 baisha_01.mp3 是同一文件**，已禁止将其当作独立笛子音源。其余素材提取有限音高候选或真实片段；±3 半音之外使用明确标记的通用辅助音。候选未做内容/乐器身份听审，不是完整音域乐器库。详见 [素材清单](docs/MUSIC_ASSET_INVENTORY.md) 与 [数据库说明](docs/MUSIC_DATABASE.md)。

- `USE_REAL_AI=true`：复用现有 OPENAI_API_KEY，一次 Responses 请求规划声部分配与疏密，然后 Python 实际编排 MIDI 和合成 WAV。可选 `MUSIC_MODEL=gpt-6-luna`。模型只接收曲谱摘要/音频测量元数据，**不上传任何录音**。
- 否则：本地规则规划，明确标为非 AI 方案；解析和合成均真实执行。API 失败也明确显示回退原因。
- 旋律保留程度控制音符保留比例；保留音符音高/起点/时值不变。合奏目录的测量仅作风格参考，不等于传统曲种规范。最长输出 30 秒；短谱保留实际时长。
- 页面说明真实采样音符、辅助音符和片段的实际数量。WAV 含真实声音；MIDI 只保存音符/速度，普通播放器使用自己的 GM 音色，不能复现录音片段。
- 作品保存在会话供下载，不自动写入原素材目录或云端。改变输入后清除旧作品，重新点击才生成。

三个新增小型依赖已装入当前 .venv 并写入 requirements：mido、soundfile、defusedxml。无需数据库服务器、ffmpeg 或模型训练。

```powershell
# 重新扫描当前素材目录，更新 SQLite / JSON / 报告；不修改原录音
.\.venv\Scripts\python.exe -X utf8 -B tools/scan_music_library.py
# 免费：生成明确标记的人工测试旋律（非歌曲），输出到系统 TEMP/naxi-music-m5-demo
.\.venv\Scripts\python.exe -X utf8 -B tools/test_music_arrangement.py
# 自己的 MIDI / MusicXML：不加 --live 即本地规则；加 --live 是一次计费模型规划
.\.venv\Scripts\python.exe -X utf8 -B tools/test_music_arrangement.py --score "你的曲谱路径.mid" --live
# 音乐浏览器验收：先用 USE_REAL_AI=false 启动测试服务器，防止测试产生 API 费用
.\.venv\Scripts\python.exe -X utf8 -B tests/browser_smoke.py http://127.0.0.1:8501 --music
```

此前 Milestone 5 的 48 项自动测试、浏览器音乐播放下载和一次真实音乐方案调用通过；30 秒人工测试输出包含真实采样和辅助音。现已收到《青花瓷》和《兰亭序》图片曲谱，新增识谱与校对流程；真实识谱草稿仍须人工核对，不宣称已经完成准确的整曲转录。

当前是纳西古乐素材参考改编实验，不是经专家验证的洞经/白沙生成模型。传统调式、乐器配合分析、乐句切分、完整采样库和复杂照片/PDF 识谱仍待完善。完整范围、文件清单和测试记录见 [Milestone 5 报告](MILESTONE_5_REPORT.md)。

### 图片识谱与校对

1. 上传清晰印刷谱，必要时裁剪到一至两行并保留调号。OpenCV 校正光照和轻微倾斜，自动识别简谱/五线谱；证据不足时才出现手动选择。
2. 点击「开始图片识谱」。五线谱在本机调用 Audiveris 导出 MusicXML；简谱通过真实 OpenAI Responses API 获取音符草稿，不提供 Mock 识谱。普通重绘、修改控件不重复调用 API。
3. 核对调号（支持 `1=A`、`6=A` 等，缺少调号不会默认 C）、参考八度、速度，再修改音符表的音高、起点、时长、休止和声部。可增删音符，试听使用明确标注的辅助音源。
4. 所有低/中置信度事件及全部 Audiveris 音符均标记待核对。逐项检查后勾选全曲校对确认；若有未支持符号，还须明确接受片段范围/印刷顺序。此后才生成 MIDI 并启用原有改编流程。修改草稿会使旧 MIDI 失效。

当前 `.venv` 已安装 `opencv-python-headless==5.0.0.93`。Audiveris 5.11.0 官方 Windows Console 包已解压到用户工具目录，附带 Java，不修改系统 Java。新电脑可运行 `tools/setup_audiveris.py`（联网下载并验证 SHA-256），或安装官方包后在 `.env` 配置 `AUDIVERIS_EXE` 为完整 exe 路径。

简谱启用配置（保留现有密钥，不要提交 `.env`）：

```dotenv
USE_REAL_AI=true
MUSIC_OMR_MODEL=gpt-6-luna
# OPENAI_API_KEY 使用现有配置
# AUDIVERIS_EXE 留空可自动查找当前用户工具目录
```

简谱只在明确点击识别时发送当前裁剪图片，一次非流式请求、不自动重试、不上传音频；后续点击改编是独立的音乐规划步骤。识谱失败明确报错，不生成模拟音符。

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
# 无 API 费用：相关回归测试
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_score_omr -v
# 只检测类型；加 --recognize 才调用真实引擎（简谱会产生 API 费用）
.\.venv\Scripts\python.exe -X utf8 -B tools/test_score_omr.py "data/music/曲谱/青花瓷简谱.jpg"
```

详细实测与限制见 [图片识谱报告](docs/MUSIC_OMR_REPORT.md)。暂不承诺手写、PDF、多页自动拼接、复杂简谱多声部、换调、反复展开、装饰音、三连音和演奏法还原。建议补充高分辨率原谱或正确 MIDI/MusicXML，供逐音比较验证；低分辨率小点、减时线仍可能误识。
