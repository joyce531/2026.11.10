# Milestone 3A：Godot 接入与东巴文 Agent 前置审计

检查日期：2026-11-07。项目：`D:\Projects\Naxi_AI_Demo`。

## 1. 结论与检查边界

现有平台导航、Godot 本机文件服务、画布 PNG 提交、照片预处理和本地图形评价可以复用。真正的 Dongba Handwriting Evaluation Agent 尚未实现。首要前置工作是审核已有游戏中的五张候选字形、建立正式 character_id 映射，再接入视觉模型及工具调用循环。

本轮只新增本报告，没有修改 AGENTS.md、页面、业务代码、依赖、原游戏或已有 Web 导出；没有安装软件、重新导出、复制游戏资源、提交、推送或切换分支。未执行游戏编辑器导入，避免改写 `.godot` 缓存。Godot 仅执行无项目参数的 `--version`。

检查前 Git 状态：`AGENTS.md` 已有修改；`.env.example`、`.streamlit/`、`ARCHITECTURE.md`、`README.md`、`agents/`、`app.py`、`components/`、`config/`、`data/`、`pages/`、`requirements.txt`、`services/`、`tests/`、`tools/`、`ui.py` 为已有未跟踪内容。这些均不属于本轮新建文件，必须保留。

证据等级：本轮做文件、代码、资源引用、模板 ZIP 完整性和 Python 测试检查；没有重新通关游戏，没有调用模型。上一里程碑验证过网页引擎启动和主菜单，但不能据此宣称所有关卡与音视频已经验收。

## 2. Godot 工程定位与版本

递归检查 `D:\dachuang` 与 `D:\Projects`，发现以下三个 `project.godot`；后者未发现额外工程。以下是磁盘现状，不指定最终版本。

| 工程准确路径 | 主场景与内容 | 语言、插件 | 导出状态 |
| --- | --- | --- | --- |
| `D:\dachuang\naxi-game\project.godot` | `Scenes/MainMenu.tscn`；包含文字、音乐、舞蹈教学流程 | 自有 14 个 GDScript；未找到 C# 或 GDExtension；Dialogic 2.0-Alpha-19 (Godot 4.4+) | 有 Web preset，指向 `D:\livingnaxi-web2\index.html` |
| `D:\dachuang\naxi-ancient-music\project.godot` | `uid://djvxmro8arjwu` 对应 `Scenes/first_project.tscn`；另有 main_menu、hud、puzzle_minigame、rope_clue 场景，脚本为对话、线索和拼图流程 | 自有 8 个 GDScript；未找到 C# 或 GDExtension；同版本 Dialogic | 无 export_presets.cfg；未见与 naxi-game 同样的三模块教学结构，不能认定为最终整合版 |
| `D:\dachuang\新建游戏项目\project.godot` | 未设置主场景，仅有 `scene/node_2d.tscn` | 未找到自有 GDScript/C# 或 GDExtension；未配置 Dialogic | 无导出配置，三模块不完整 |

三个项目均声明 `config/features` 的版本为 4.6，项目文件本身不能证明精确补丁版本。实际执行 `D:\dachuang\Godot_v4.6.1-stable_win64_console.exe --version` 返回 `4.6.1.stable.official.14d19694e`。旁边也存在非 console 可执行文件。

### naxi-game 的模块完整性

`Core/GameManager.gd` 明确串联 opening → 东巴文化书/答题/完成页 → 音乐对话/文化书/答题/完成页 → 舞蹈对话/文化书/学习/完成页 → end。主要场景还有 `VNStage.tscn`、`CultureBook.tscn`、`DongbaQuiz.tscn`、`MusicQuiz.tscn`、`DanceLearning.tscn`、`CompletionPage.tscn`、`EndScreen.tscn`。旧 `ResultScreen` 已在脚本中注明不再使用，不能把旧文件存在当成活动入口。

- 文字：`Data/content.json` 中有 16 道题（五个单字的图文、听音、选图题及一句子题）；五张单字图和五段对应音频存在。
- 音乐：5 道辨识题，引用的 5 个 `.ogv` 文件存在。`Scenes/QuizCard.gd` 会区分视频路径并用 VideoStreamPlayer 播放，不是把 .ogv 当普通音频解码。
- 舞蹈：`datiao_01` 有完整视频和三个分步视频，引用文件均存在。`scripts/dance/DanceLearning.gd` 有总览、分步学习、口诀排列、完成阶段；没有真人动作识别，不把键盘操作当舞蹈评分。
- 尚不能称资源完全齐备：内容清单引用的 `Assets/dongba/sentence/dongba_sentence_01.ogg`、`Assets/culture_book/audio/page_turn.ogg` 缺失；`Assets/culture_book/illustrations/test_missing.png` 也缺失，但它是 test_book 明示的缺图测试条目，不能等同正式关卡故障。
- `ContentDB.gd` 对缺图返回 null、对缺音频尝试静音占位，因此页面能运行不意味着资料齐全。文化文字、读音、视频授权还需独立核验。

## 3. Web 导出与兼容性

### 已有可复用的导出

`D:\livingnaxi-web2` 含 index.html、index.js、index.wasm、index.pck、index.png、index.audio.worklet.js、index.audio.position.worklet.js。PCK 为 85,373,700 字节，WASM 为 35,739,700 字节，两者合计约 121.1 MB（十进制）。无需先重新导出才能继续平台接入。

`naxi-game/export_presets.cfg` 配置：Web、all_resources、`include_filter="*.json"`、`variant/thread_support=false`、`variant/extensions_support=false`、PWA 关闭。JSON include 对运行时读取 `Data/content.json` 很重要，后续导出不能漏掉。

虽然 features 标签仍有 Forward Plus，实际 `renderer/rendering_method` 与 mobile 设置均为 `gl_compatibility`。另外两个项目没有此覆盖，若选择它们导出，需要另行评估并在获准的开发副本中切换 Compatibility。

模板目录：`C:\Users\Lenovo\AppData\Roaming\Godot\export_templates\4.6.1.stable`。存在 web_debug/release、web_nothreads_debug/release，以及四个 web_dlink 变体 ZIP；八个 ZIP 均通过 CRC 检查。模板已安装，不需本轮下载。未执行实际重新导出，因此不保证任何未测工程都能直接构建成功。

### 兼容问题与建议

Godot 4.6 Web 要求 WebAssembly/WebGL 2.0，使用 Compatibility；Godot 4 的 C# 项目不能直接 Web 导出。单线程是官方推荐默认方式。Sample 音频模式不支持部分效果和程序化音频；Stream 模式可能增加延迟。以上依据 [Godot 4.6 Web 导出文档](https://docs.godotengine.org/en/4.6/tutorials/export/exporting_for_web.html)。

本项目适合先保留单线程：已使用该配置，核心教学脚本未发现 Thread.new、OS.execute、TCP/UDP 或程序化音频依赖，也未发现原生扩展。Dialogic 的 Thread.new 命中位于 Editor 工具脚本，不应直接当成游戏运行时阻断问题。不能仅凭插件版本宣布全兼容；需实测对话推进、存档、换场景、播放与暂停。

重点验收：

1. 音频需用户交互解锁；检查首次播放、重播、静音、页面失焦后恢复。先测现有 OGG/OGV，不预先改插件或转码。
2. `.ogv` 的 VideoStreamPlayer 播放与同步可能成为单线程性能瓶颈。应逐段检查舞蹈和音乐视频，而不是只看菜单；若卡顿再在独立副本中优化码率、分辨率或播放方案。
3. 存档 `user://savegame.json` 和 Dialogic 存档属于浏览器侧存储，不是 Python 学习数据库。现有文件服务随机端口会改变浏览器 origin，重启后存档可能不可见；正式演示需固定地址/端口并验证持久化、隐私模式与清缓存行为。
4. 本机服务绑定 127.0.0.1；远程观众不能通过该地址访问演示机的游戏。部署时需实际可达的静态站点 URL、HTTPS 和对应 MIME。当前服务已有 wasm MIME、COOP/COEP 与路径边界检查，但不是生产服务器。
5. 若未来使用多线程，需另测跨源隔离和 iframe 权限/响应头；当前新标签页方案较简单。不要直接用 Streamlit HTML 拼接导出源码，WASM/PCK 必须由静态服务提供。

### 将导出放入 game_web 的下一阶段方案（本轮未执行）

当前 `game_web/` 不存在，也不是现有运行的必要条件。保持原工程及 `D:\livingnaxi-web2` 不变；未来确需随平台交付时，把经授权的**导出制品**完整复制到新的 `Naxi_AI_Demo/game_web/`，保留 index 文件族名称及相对路径，先核对文件校验和，再将 `GODOT_WEB_DIR` 指向该目录。不要复制原项目 Assets/.godot，也不要覆盖已有导出目录。当前 AGENTS.md 的集成规则禁止自动复制资源，因此这是待下一阶段明确调整范围后执行的方案。

现有 `pages/game.py` + `services/game_service.py` 可以直接服务新目录；远程部署优先设置 `GODOT_WEB_URL`。大制品是否入 Git 应另行确定，不应直接加入当前未跟踪内容。iframe 只是未来可选 UI，不是本轮必需；学习进度/目标字传递还需受控 character_id 协议，不能把 API Key 放进 Godot 网页。

## 4. 东巴文代码结构与实际能力

入口：`app.py` 的 st.Page 注册 `pages/dongba.py`，独立 URL 为 `/dongba`。

| 文件 | 实际职责与复用方式 |
| --- | --- |
| `pages/dongba.py` | 加载目标、两种输入、提交快照、并排对照、结构结果与 JSON 报告下载；可保留 UI，后续替换服务调用边界 |
| `components/handwriting_canvas.js` | 640×480 Canvas；笔粗、颜色、撤销、清空；提交 data:image/png;base64 PNG |
| `components/handwriting_canvas.py` | Streamlit v2 包装、Base64 格式/长度校验、decode_canvas 到 Pillow 图像 |
| `tools/upload_validation.py` | PNG/JPEG 真实解码、扩展名匹配、10 MB/1600 万像素限制、EXIF 方向、白底透明合成、最长边缩至 1600 |
| `services/dongba_evaluator.py` | Pillow/NumPy 预处理、归一化形态测量、规则反馈；VisionReviewer 只是 Protocol |
| `services/dongba_data.py` | Schema、ID 唯一性、路径边界及审核授权过滤；工程图形自测 |
| `agents/dongba_agent.py` | DongbaAgent Protocol，无模型、工具注册、Runner 或持久化实现 |

画布内部 `state.strokes` 保存每笔 width/color/points[x,y]，按输入顺序排列，最多 300 笔、每笔 5000 点；它用于撤销和重绘。目前只发送 PNG，轨迹不传到 Python、不持久化，没有时间戳、压力或规范笔顺数据。下一阶段可扩展提交为 PNG + 带版本的轨迹快照，记录画布尺寸、点坐标、时间、笔状态与提交 ID，后端限制总点数/大小并校验范围。当前点列不能支持速度分析；照片无法推断笔顺。未来即使有轨迹，也需可靠教学标准才能评价规范运笔。

照片流程可直接复用：手动 0/90/180/270 度旋转、百分比裁剪、40–230 阈值及可选背景亮度归一化。当前没有 OpenCV，没有模糊/反光检测或透视矫正；复杂纸面照片仍可能误分割。

本地算法：字形保留宽高比居中归一至 160×160；膨胀容差约 3 像素，双向形态覆盖 F1；总分为 65% 覆盖 + 15% 宽高比 + 10% 重心 + 10% 上中下分布。主轴、密度辅助生成问题和拒绝规则。返回 close/review/mismatch/invalid，未输出置信度，不能把 similarity 当准确率。它消除了整体平移/缩放，位置指字形内分布，不是纸面布局。上下三带也不是经过语义标注的真实构件。

为什么还不能进行真实视觉 AI 评价：正式字库为空；无视觉 SDK/API 配置；页面直接调用本地 evaluate；Agent 仅为接口；没有工具调用循环、模型结果校验或学习记录存储。开启工程自测能验证交互与算法，不等于正式东巴学习可用。

## 5. 字形数据清单与导入缺口

平台 `data/dongba/characters.json` 为 `[]`，没有正式标准字形图片。已有 characters.schema.json、training_record.schema.json 和导入说明；geometry_reference 是明确标注的非文字测试图形。

但原游戏存在以下**候选教学图片**，均已真实解码并目视检查为白底深色线条图。下表中文是原游戏题目关联标签，仅记录现有数据，不构成文化正确性确认。路径前缀为 `D:\dachuang\naxi-game\Assets\dongba\glyphs\`。

| 图片文件/可提取资源 ID | 游戏标签 | 尺寸 | 状态 |
| --- | --- | --- | --- |
| dongba_01_person.png | 人 | 112×75 | 待来源与授权审核 |
| dongba_02_mountain.png | 山 | 324×216 | 同上 |
| dongba_03_water.png | 水 | 134×90 | 同上 |
| dongba_04_fire.png | 火 | 143×96 | 同上 |
| dongba_05_sun.png | 太阳 | 155×103 | 同上 |

另有 `Assets/dongba/sentence/dongba_sentence_01.png`（2160×1229 RGBA），它是句子组合图，不应直接当单字参考。五个单字在 `Assets/dongba/audio/` 有同名 .ogg 音频，但来源和读音准确性尚未审核。

`Data/content.json` 已通过题目 id、prompt/options 图片路径和 answer_index 建立关联，例如 `dongba_t1_person` 的图形关联游戏标签“人”。这是题目 ID，不是平台标准 character_id；同一个字有 t1/t2/t3 三道题，导入须去重。可拟用资源基名作为稳定字符 ID，保留原题目 ID 映射，但本轮未建立记录。

需要补充：每张图的出处（教材/机构/作者/页码等）、使用授权、审核人和日期、经核验中文含义、构形说明、学习提示；读音仅在有可靠来源时加入。未核实的现有游戏解释不能直接写入 RAG。小图清晰度有限，优先索取原始高分辨率示范，不能用生成式补画伪造标准。导入先 pending/unknown，经审核再 verified/authorized；现有加载器可以继续使用。

## 6. API、环境与依赖

本轮使用 `.venv\Scripts\python.exe`，实际 Python 3.14.3。

| 包 | 本环境安装状态/版本 |
| --- | --- |
| openai | 未安装 |
| openai-agents | 未安装 |
| opencv-python | 未安装 |
| opencv-python-headless | 未安装 |
| python-dotenv | 未安装 |
| streamlit | 1.67.0 |
| Pillow | 13.0.0 |
| numpy | 2.5.4 |
| jsonschema | 4.26.0 |

项目 `.env`、项目 `.streamlit/secrets.toml` 均不存在，当前进程 `OPENAI_API_KEY` 未配置。未输出任何密钥，未发起认证/计费请求；未检查系统其他位置的凭据，因此不推断机器上绝无其他配置。

`config/settings.py` 当前读取环境变量与 Streamlit secrets，**不自动加载 .env**。未来若选择 .env，需明确增加 dotenv 加载；也可继续沿用环境变量/secrets，不强制新增 python-dotenv。API 需要可用的 OpenAI Key、支持图像和工具调用的模型配置、超时及预算限制；具体模型待账户可用性和真实样本评测后选定。

后续可安装 openai-agents 及其依赖；视觉适配器若直接导入 openai，应在依赖文件明确表达。OpenCV 只选 opencv-python 或 opencv-python-headless 之一；Streamlit 服务无需 OpenCV 桌面 GUI 时优先评估 headless。Python 3.14 对应 wheel/完整依赖链尚未安装验证，不把理论兼容当运行成功，不改原虚拟环境配置来规避问题。

## 7. 第一个 Agent 的建议架构（未实现）

名称：**Dongba Handwriting Evaluation Agent**。目标是指定字形下的比较，不做未知字 OCR，不负责音乐或舞蹈调度。

官方 Python 示例支持 Agent、function_tool、Runner.run 及 Pydantic output_type；适合在现有 Python 服务之上增加工具循环与结构化输出。[OpenAI Agent definitions](https://developers.openai.com/api/docs/guides/agents/define-agents)

视觉接口可以同时传入参考图和用户图，例如用多个 input_image 和 Base64 数据 URL；服务端本地文件路径本身不能被模型读取。[OpenAI Images and vision](https://developers.openai.com/api/docs/guides/images-vision)

建议流程：页面提交 → 本地强制输入校验/审核目标检查 → Agent 工具循环 → 两图视觉分析与本地测量 → 强制结果校验 → 展示 → 按用户选择保存学习记录。强制的安全检查不能由模型选择跳过。

| 工具 | 输入/职责 | 边界 |
| --- | --- | --- |
| get_reference_character | character_id → 审核元数据、参考图受控 ID/摘要 | 不允许模型传任意文件路径；目标不存在则停止 |
| inspect_handwriting_quality | 受控图片 ID → 清晰度、曝光、笔迹区域、裁切风险 | OpenCV 模糊/连通域等测量需样本标定；低质量转 unreadable |
| preprocess_handwriting | 输入 ID + 白名单参数 → 派生图 ID、处理记录 | 复用 Pillow，必要时 OpenCV 自适应阈值/透视辅助；保留原图，不镜像或旋转掩盖方向错误 |
| measure_shape_similarity | 参考图/处理图 ID → 当前本地分数、结构指标 | 原型分数只来自代码，不让 LLM改写或当概率 |
| compare_reference_and_handwriting | 两图 ID + 实测结果 → 视觉结构证据 | 独立 vision_service 适配器发两图给视觉模型；只分析形状，不猜文化与笔顺 |
| save_learning_record | 已校验结果 ID + 会话授权 → 记录 ID | 工具检查同意、所属会话、幂等键；不得由模型代替用户同意 |

Agent 应实际调用上述工具，依据质量结果停止或继续，必要时在限定次数内重试分析，再形成最终输出。视觉调用是工具之一，而非页面直接一次请求后原样显示。工具真实执行日志可展示脱敏摘要；没有执行成功的工具不得声称完成。初期不需要 RAG/向量库才能比较两张图，只检索审核字库；不引入总控 Agent。

建议结果字段：character_id、input_mode、status、measured_similarity、similarity_method、structure_errors[{region,issue,evidence}]、suggestions、confidence、confidence_basis、quality_flags、reference_source、model/algorithm_version、record_id。confidence 是未标定的模型/规则可信程度，明确不等于正确率；无模型或质量不足时可为 null。文化解释与来源另外保留。

四类状态：close（形态接近但不保证教师认可）、partial（部分结构正确）、mismatch（清晰可见且差异明显）、unreadable（图片不足以可靠判断）。当前 review→partial、invalid→unreadable 只能作为迁移起点，需保持错误原因；网络超时、缺目标和无密钥是执行错误，不能冒充 unreadable 或 mismatch。

若 mismatch，必须显示：“当前书写与目标字差异较大，无法判定为正确临摹，请重新观察示范字。”模型与形态证据冲突时降置信并提示人工复核，不强行 close。现有阈值尚未用真实样本标定，不应作为不可推翻的文化判定。

学习记录建议 SQLite 元数据 + 仓库外私有图片目录；保存前用户选择，训练使用另行同意。保留参考图版本/哈希、输入来源、预处理参数、轨迹版本、测量结果、模型信息、时间与人工复核标签。训练 Schema 的 similarity_label 仍只接受人工真值；不要把模型分数塞进去。记录 ID 由服务生成，事务/幂等防 Streamlit rerun 重复保存，约定删除与保留期限。数据库和图片不进入 Git。

## 8. 下一阶段文件计划

以下仅为建议，均未修改/创建：

| 文件 | 下一阶段工作 |
| --- | --- |
| data/dongba/characters.json、references/ | 获准后导入五个候选单字及审核信息；保持来源可追溯 |
| services/dongba_data.py | 增加按 character_id 获取及版本/哈希；复用已有审核与目录边界 |
| components/handwriting_canvas.js/.py | PNG+轨迹联合提交、时间戳、负载校验和稳定提交 ID |
| services/dongba_evaluator.py | 保留本地原型；增加统一状态适配，不覆盖已有测试语义 |
| services/image_quality.py（新） | OpenCV 质量检查与受控预处理 |
| services/vision_service.py（新） | 双图输入、结构化分析、错误/超时/预算与可替换模型适配 |
| tools/dongba_tools.py（新） | Agent 可调用的工具包装，受控图片上下文与执行证据 |
| agents/dongba_agent.py（现有契约） | 迁移为真实 SDK 实现前先解决包命名冲突，见下节 |
| database/db.py、schema.sql（新） | 同意后学习记录保存、版本、幂等与删除 |
| pages/dongba.py | 复用双输入与对照，增加本地/视觉模式、状态、置信说明与保存选择 |
| config/settings.py、.env.example、requirements.txt | 仅在 API 方案确定后配置/安装，密钥不入代码 |
| tests/、README.md、ARCHITECTURE.md | 回归、假客户端错误测试、真实样本验收与运行说明 |

Godot 下一阶段如只沿用已导出版本，平台游戏页面无需重写。只有独立部署、内嵌、固定端口或学习数据互通时才调整 game_service/settings/game 页；原工程仍保持只读。

## 9. 风险、验收与建议顺序

1. **SDK 命名冲突**：本项目已有顶层 `agents/`（当前无 __init__.py），OpenAI Agents SDK 同样使用 `agents` 导入名。安装后 SDK 常规包可能遮蔽本地命名空间；添加 __init__.py 反而可能遮蔽 SDK。建议下一阶段把项目 Agent 实现迁到明确命名的 `naxi_agents/` 或项目包下，同时保持现有文件兼容/不删除，先加导入测试。本轮没有改目录。
2. **文化/授权缺口**：有图片不代表已审核；低分辨率、异体字、教材变体会影响评分。补来源和审核后再开启正式学习模式。
3. **质量与误判**：阴影、反光、透视、彩笔、涂满、陌生几何图形都可能影响指标。应覆盖同字自然变体、错误目标、缺部件、镜像/旋转、额外笔迹及不可读照片，并用人工标签标定。
4. **模型幻觉**：图像或用户描述中的指令当作不可信内容；不让模型猜文化解释、笔顺、百分比准确率。数值测量、视觉结论和人工标签分开显示与存储。
5. **隐私与成本**：上传到视觉 API 前说明用途；API trace/log 不记录 Base64、真实 Key 或用户原图；限制工具轮数、视觉请求次数和超时。网络失败保留本地原型结果并标明来源，不伪造视觉成功。
6. **运行性能**：121 MB 首载、OGV 解码、随机端口存档、Dialogic alpha 插件及浏览器音频策略都需演示机实测；不能把本地首屏成功视为联网部署完成。

本轮验收：

- `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_*.py`：19 项通过（包含形态一致/错误/空白/缺结构、上传、字库边界、页面和游戏服务）。Streamlit bare-mode 的 ScriptRunContext 警告未导致失败。
- 使用 ast.parse 只读检查 21 个项目 Python 文件：全部通过；`-B` 避免写入字节码。
- 八个 Web 模板 ZIP CRC 检查通过；五张候选单字图与一句子图真实解码成功；核对内容清单中的资源路径。
- `git diff --check` 无错误。测试只使用临时数据，不导入正式字库。没有重新执行浏览器通关、模型 API 测试或 Web 导出。

建议先完成候选字形的来源/授权/构形审核，再确定模型账户配置和 Python 3.14 依赖可用性，解决 agents 包名冲突，随后落地工具循环、四态输出与按需学习记录。画布和本地测量保持为可运行基础与故障回退。

现有启动命令不变：

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

默认预览 `http://localhost:8501`；`/game` 为游戏入口，`/dongba` 为临摹页。本报告不意味着已接入视觉模型。
