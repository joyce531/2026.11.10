# Milestone 4B：阿里云百炼 Qwen 接入

日期：2026-11-08。已阅读现有项目与历史 `MILESTONE_3A_AUDIT.md`，复用当前五字目录、画布、照片预处理、OpenCV 路由、校对表、音乐素材库和本地渲染。下文“初次接入”记录保留当时状态；文末“真实路由复查”是最新结果。

## 当前结论

Qwen 请求线路已接入三处业务：东巴文双图比较、简谱/五线谱图片转录、音乐编排规划。**本轮按要求没有真实 API 测试调用**，所以仅能确认离线请求契约、数据处理与页面运行，不能确认账户配额、模型权限、远端响应兼容性或识别准确率。

现有 `services/qwen_service.py` 与两个 Agent 已有部分预留改动，本轮在其基础上完善；修正乱码的双图提示、当前 SDK HTTP 客户端导入，以及页面无法识别 Qwen 结果来源的问题。未重建 Agent 框架。

## 配置检查

只检查配置存在性，没有打印密钥或修改 `.env`：

| 变量 | 当前状态/用途 |
|---|---|
| DASHSCOPE_API_KEY | 已配置；是否有效未在线验证 |
| DASHSCOPE_BASE_URL | 已配置；服务要求北京官方 HTTPS 兼容根地址 |
| QWEN_TEXT_MODEL | 缺少；请填控制台已开通的准确文本模型 ID |
| QWEN_VISION_MODEL | 缺少；请填支持图片与 JSON 模式的准确视觉模型 ID |
| USE_REAL_AI | 未设置；需设 true 才启用真实调用 |
| AI_PROVIDER | 未设置时默认 qwen；可显式填 qwen，或 openai 使用原路线 |

没有代选模型。当前接口使用非思考模式 `enable_thinking=false` 与 `json_object`，需选择支持这些参数的模型。模型不支持、无权限或结构错误会报错，不重试、不自动换模型。官方依据：[视觉兼容接口](https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai)、[结构化输出支持范围](https://help.aliyun.com/zh/model-studio/qwen-structured-output)。

## 业务行为

### 东巴文

同一次请求按顺序发送标准字形与用户作品，两张图片都来自现有预处理。只比较轮廓、比例、相对位置、方向、缺失/多余结构，不做未知文字 OCR，也不推断文化知识或笔顺。

沿用六字段 JSON 与 match/close/incorrect/uncertain 状态，页面显示接近正确/部分正确/明显错误/无法可靠判断。Qwen 来源记录为 `qwen_vision`，模型分数只显示为视觉相似度估计，不是准确率或本地测量。低质量图片仍可由本地质量检查拒绝，并标记未调用模型。

Qwen 失败直接停止并给安全错误提示；只有用户明确选择 Mock 或未启用真实模式时才运行标记清楚的本地测试。原 OpenAI 路线的显式 Mock 回退保留。

### 图片识谱

OpenCV 判别和上传组件不重复开发。Qwen 路线对简谱和五线谱分别使用专用提示词及 Schema，同一次识谱只调用视觉模型一次。

简谱保留数字级数、上下点、临时升降、时值、附点、休止、小节线、简单延音与调号；不默认 1=C。五线谱转录谱号/调号作用后的绝对音高、拍长、声部、位置、休止、结构说明及置信标记。两者接入原有音符校对表。

未知时值/音高保持空值并阻止生成，低置信内容标记待校对。速度缺失时 120 BPM 仅供试听且明确提示，不冒充识别值。确认后生成 MIDI，再交现有编曲流程。原 `AI_PROVIDER=openai` 路线继续使用 Audiveris 五线谱导入。

### 古乐改编

使用 Qwen 文本模型检查曲谱摘要、所选乐器标签与现有采样映射，生成声部分配/疏密等受限计划。计划通过原有校验后，由 Python 生成 MIDI 与 WAV，继续展示真实采样/辅助音源用量。模型不合成音频，录音不发送到云端。

保留旋律保留程度控制，不新增自由创作。风格仍是素材参考实验，不声称实现正宗洞经/白沙规则。Qwen 失败不自动产生规则作品；关闭真实模式可明确使用本地规则。

## 文件与验证

完善/修改：

- `services/qwen_service.py`：共享调用、北京端点检查、配置验证、安全错误、单次 JSON 请求。
- `naxi_agents/dongba_agent.py`：复用已有 Qwen 分支，修复双图提示。
- `services/score_omr.py`：Qwen 简谱与五线谱适配，保留 OpenAI/Audiveris。
- `components/score_review.py`：提供方路由、配置提示、结构展示及空值安全校对。
- `pages/dongba.py`、`pages/music.py`：正确显示 Qwen 来源、分数和错误，避免与本地结果混淆。
- `.env.example`、`README.md`：配置和边界说明。
- `tests/test_dongba_agent.py`、`tests/test_music.py`、`tests/test_score_omr.py`：旧路线测试明确固定提供方，防止读取个人配置后误走新路线。
- 新增 `tests/test_qwen.py` 与本报告。

现有 `naxi_agents/music_agent.py` 的 Qwen 规划分支经检查和离线测试复用，本轮没有重新改写。无需新增依赖，`pip check` 正常。

全部 65 项测试通过，新增 Qwen 测试 8 项。运行时另外禁止 HTTP SDK 网络发送，避免意外消耗额度。覆盖：缺模型/错误端点、单次双图请求、无流式、JSON/截断/网络错误、Qwen 失败不转 Mock、两类曲谱转录契约、未知音符不补造、Qwen 编排计划与实际本地 WAV/MIDI、页面加载不调用 API，以及既有模块回归。假客户端仅用于单元测试，不作为产品识谱结果。

44 个相关 Python 文件语法检查通过；Streamlit 在临时测试端口启动且健康检查返回 ok。50 个受保护文件哈希未改变，包括数据、音乐库、曲谱、舞蹈/游戏模块、`.env` 和 `.gitignore`。没有提交 Git。修改前代码备份位于系统临时目录 `naxi-before-4b.zip`，不含 `.env`。

## 体验与限制

补齐模型 ID、开启真实模式后运行：

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

进入东巴文页，关闭 Mock 后提交；或进入音乐页上传清晰曲谱，识别、校对、确认 MIDI，再点击改编。只有明确点击按钮才产生请求，识谱和编曲是两次独立操作。

现有五字和录音可复用，无需为了接入 Qwen 重新补素材。建议用清晰、含调号/拍号/速度的一至两行印刷谱试用；单次最多 128 事件，复杂反复/跳房、换调、多声部、装饰音和手写仍需人工校对，不承诺完整准确转录。文化风格、采样身份及模型质量仍需要后续人工评估。

## 真实路由复查（同日后续）

`.env` 现在已配置北京业务空间 Base URL、同一份 `DASHSCOPE_API_KEY`、文本智能路由 `auto-model-9e5f7930` 和直接视觉模型 `qwen3.8-flash`。没有输出密钥内容。`AI_PROVIDER` 未设置，代码默认 Qwen；本轮只向 `.env` 追加 `USE_REAL_AI=true`，页面默认真实 AI 优先。该文件已被 Git 忽略，未写入示例或日志。

阿里云官方[智能路由说明](https://help.aliyun.com/zh/model-studio/model-routing)明确其只支持文本 Chat Completions，不支持图片。官方[视觉模型说明](https://help.aliyun.com/zh/model-studio/vision-model/)将 `qwen3.8-flash` 列为支持图像和结构化输出的模型。共享服务现已强制拒绝 `kind=text` 携带图片，并拒绝把 `auto-model*` 配成视觉模型；文本请求使用纯字符串，视觉请求仅送 `QWEN_VISION_MODEL`。两者复用同一 Key 与 Base URL。

真实调用记录：

| 场景 | 实际结果 |
|---|---|
| 文本智能路由最小 JSON 请求 | `auto-model-9e5f7930` 成功返回 `{ok: true}` |
| 视觉模型最小线条图 | 首次把 `max_tokens` 人为设为 64 时结构校验失败；使用 256 Token 检查时返回有效 `{"ok":true}`。这是测试参数过低的诊断，业务默认值未被降至 64 |
| 东巴文双图 | 标准字形与人工画的无关线条同时发送给 `qwen3.8-flash`，返回 `source=qwen_vision`、`status=incorrect`、`mock=False`；无关书写未被判正确 |
| 简谱图片 | 《青花瓷》顶部印刷片段自动路由简谱，`qwen3.8-flash` 输出 32 个待校对事件，调号 `1=A`、速度 60 BPM；结果保存在系统临时目录，未生成 MIDI，尚无逐音人工准确率评估 |
| 音乐编曲 | 初次响应结构合法但把“合奏参考”误列为可分配乐器，原有业务校验拒绝并标记本地规则回退。收紧可分配 ID 和提示后，用人工测试旋律重测返回 `mode=qwen_plan`、无回退，Python 本地生成有效 MIDI/WAV；未上传录音 |

失败回退：东巴文 Qwen 请求/校验失败后调用原本地图形评价，结果明确为 `source=mock`、`mock_mode=true`，显示 `fallback_reason`；视觉模型输出 `uncertain` 时保留其真实来源。音乐智能路由失败后只用本地规则编排，结果为 `mode=local_rules` 且显示原因，不标为 AI 规划。简谱识谱失败没有可靠的本地音符转录替代，继续明确报错，不制造假音符；这是安全边界，不是漏掉回退。

本次修改：`services/qwen_service.py`、`naxi_agents/dongba_agent.py`、`naxi_agents/music_agent.py`、`tests/test_qwen.py`、`README.md`、仅追加启用开关的 `.env` 和本报告。页面 UI、Godot、舞蹈、东巴字形及音乐素材数据库未修改；未提交 Git。

最终回归：67 项测试通过（测试期间禁止 SDK 网络发送）；44 个 Python 文件语法检查通过，`pip check` 无依赖冲突。先前受保护的 49 个非配置文件哈希未变。`.env` 只追加 `USE_REAL_AI=true`；`git check-ignore .env` 确认它不会被常规 Git 添加。
