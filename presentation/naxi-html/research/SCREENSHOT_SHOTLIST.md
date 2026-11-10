# 真实证据截图清单（19 张）

19 个截图位中新增了 3 张从当前 Web 游戏实际截取的学习画面。缺少的仍显示“真实资料／待插入”。把实际截图放到 `assets/evidence/` 后运行 `scripts/enable_evidence.py`。幻灯片中统一显示在 4:3 框内，允许裁切缩放；点击可查看未裁切原图，原文件不改。允许裁切、拼接同一功能的代码窗，但不得改写数字、状态、来源标记或生成一张“看起来像结果”的图片。建议 PNG、宽度至少 1200 px；实地照片可用 JPEG。录屏链接仍按 [DEMO_VIDEO_SHOTLIST.md](DEMO_VIDEO_SHOTLIST.md) 单独准备。

| 页 | 文件名 | 要截什么 | 特别注意 |
| --- | --- | --- | --- |
| 2 | `source-glyph-catalog.png` | 打开 `data/glyphs/glyph_catalog.csv`，显示真实列名、五条登记及图片路径。 | 避免把文件名当成已获专家审核。 |
| 2 | `source-music-library.png` | 用 SQLite 查看器打开 `data/music/music_library.sqlite3`，显示素材 ID、类别、时长等真实字段与部分记录。 | 不截私有路径或无关用户数据；录音标签不等于文化身份已核实。 |
| 2 | `source-questionnaire.png` | 已实际使用的 TAM/知识前后测问卷空白页面，能看见题目与量表方式。 | 必须提供原件；遮盖姓名、电话、答卷 ID、二维码。 |
| 2 | `source-fieldwork.jpg` | 项目实际实地调研的原始照片，最好能见采访、观察或资料采集过程。 | 需本人同意与时间、地点、对象说明；没有原件就留空，不能用旅游照代替。 |
| 7 | `game-dongba-book.png` | `/game/dongba_book` 的真实文化书页。 | 已从本地 Web 页面截取；展示原 Godot 内容的 Web 迁移。 |
| 7 | `game-music-quiz.png` | `/game/music_quiz` 的真实视频辨识题。 | 已截取。画面显示浏览器视频控件，静态截图不能证明音轨播放效果。 |
| 7 | `game-dance-learning.png` | `/game/dance_learning` 的真实完整舞蹈演示页。 | 已截取。不要把教学视频说成 Wan 生成作品。 |
| 16 | `agent-dongba-result.png` | 一次真实 Web 东巴评价：标准图与玩家图、状态、差异、建议和 `source` 标记。 | 如果为 Mock，画面与讲解都写 Mock；隐藏玩家身份。 |
| 16 | `agent-music-result.png` | 一次真实 Web 古乐任务：校对音符、选项、MIDI/WAV 播放下载或结果状态。 | 不以只有文字的规划冒充已合成音频。 |
| 16 | `agent-dance-result.png` | 一次真实 Web 视频任务：审批状态、同一任务 ID、成功后的 MP4 播放下载。 | 未真实成功时只截当前真实状态，不用原片冒充生成品。 |
| 17 | `code-dongba.png` | IDE 中 `naxi_agents/dongba_agent.py`、`services/dongba_vision.py` 的双图输入、字段校验与回退关键代码。 | 不露 API Key、Base64 图像、个人文件路径。 |
| 17 | `code-music.png` | `services/score_omr.py` 的待校对门槛及 `services/music_render.py` 的 MIDI/WAV 调用关键代码。 | 保留文件名和函数名，别用不相关代码凑图。 |
| 17 | `code-dance.png` | `services/dance_service.py` 的异步创建、状态查询与结果保存关键代码。 | 不露请求凭证、签名 URL 或玩家媒体。 |
| 19 | `ui-dongba.png` | `/agent/dongba` 的真实输入界面：目标字、画布/上传控件与按钮。 | UI 截图无需付费调用。 |
| 19 | `ui-music.png` | `/agent/music` 的真实曲谱上传、校对和编曲参数界面。 | 显示页面实际支持的格式。 |
| 19 | `ui-dance.png` | `/agent/dance` 的本人视频、照片、服饰和背景选择界面。 | 个人照片须本人同意或遮蔽。 |
| 20 | `output-dongba.png` | 东巴评价结果特写：结构差异、修改建议与来源标记。 | 真实结果或明确标记的 Mock，不删来源。 |
| 20 | `output-music.png` | 古乐结果特写：WAV 播放器、MIDI/WAV 下载及素材/规划来源说明。 | 使用有权改编的输入曲谱。 |
| 20 | `output-dance.png` | 打跳成功结果特写：生成 MP4 播放器与下载、任务状态。 | 没有成功结果就继续留空。 |

第 2 页的问卷和实地调研资料、以及部分真实 Agent 生成结果，目前不能从仓库自动确认。请优先补这几类原件。所有截图最好保持同一浏览器窗口比例、清晰字号和少量必要上下文；具体账号、密钥、用户影像和私有 URL 必须脱敏。
