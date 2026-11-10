# Milestone 6B：迁移前缺口补全与东巴 Web 样板

日期：2026-11-09。原 Godot 工程 `D:\dachuang\naxi-game` 只读；原 Streamlit 页面、Agent、`.env`、舞蹈及音乐素材未改动。Web 前端新增于 `web/`，默认只在本机运行。未调用 Qwen、Wan 或 OpenAI API。

## 1. 审计中三个缺失资源：准确引用位置

| 缺失资源 | 源引用 | 当前可见影响 | 本轮处理 |
| --- | --- | --- | --- |
| `Assets/dongba/sentence/dongba_sentence_01.ogg` | 原 `Data/content.json` 第 225 行，`quizzes.dongba.questions[id=dongba_t4_sentence].prompt.audio` | 最后一题的例句音频无法播放；原 `ContentDB` 会退回静音 | Web 题卡明确提示音频缺失，仍展示现有例句图片，不造音频 |
| `Assets/culture_book/audio/page_turn.ogg` | 原 `Data/content.json` 第 308、337、380、430 行；测试、东巴、音乐、打跳文化书的 `page_turn_sfx` | 原翻页音效缺失 | Web 翻页可操作，并说明原音效缺失 |
| `Assets/culture_book/illustrations/test_missing.png` | 原 `Data/content.json` 第 328 行，`culture_books.test_book.spreads`，仅测试书 | 测试书插图缺失，不影响主线东巴书 | 不造测试插图；未来迁移测试书时显式显示缺图 |

以上为**三种路径**、多处引用。前两种位于正式流程；第三种是测试数据。若用户补齐资源，应由本人确认文件来源/授权后再进行资源导入，本轮没有改原项目。

## 2. 原剧情与完整性

详见 [Dialogic 剧情与 Web 状态映射](docs/MILESTONE_6B_DIALOGIC_FLOW.md)。实际 83 个 `.tscn` 位于 `addons/dialogic/`，是插件场景，不是 83 个原创剧情场景；项目原创时间线为六条 `.dtl`。主线 15 步与所有六条剧情的顺序、人物、背景、事件、结束转换均已列出。`dongba_intro.dtl` 不在现行主线。原剧情没有 Dialogic 用户选择；Agent 分支由本次 Web 通关页新增。导入的剧情事件与东巴题库/知识书都保留原文，没有用假文化数据填空。

## 3. 存档模型

浏览器游客存档键为 `naxi-ai-studio:guest-save:v1`，每次推进自动写入。结构分开保存：

```json
{
  "version": 1,
  "userId": "guest-local",
  "currentStep": "dongba_quiz",
  "dialogueIndex": 0,
  "bookIndex": 0,
  "completedSteps": ["opening", "dongba_book"],
  "skippedSteps": [],
  "quiz": { "status": {}, "wrongCounts": {}, "queue": [], "pos": 0, "round": 1, "feedback": null },
  "miniGames": {},
  "agentUses": [],
  "works": [],
  "lastPlayedAt": "ISO-8601 UTC"
}
```

`completedSteps` 与 `skippedSteps` 独立；答题状态另存每题 `pending/done/skipped` 与累计错答次数。原 Godot 存档只存 `step_id`，重入问答会重置；Web 已提升到保存当前题与反馈。游客数据留在当前浏览器，没有账号、跨设备同步或服务端备份。未来云存档接口建议 `GET/PUT /api/v1/users/{id}/progress`，正文沿用同一 versioned schema，附 `revision` 做并发控制；Agent 使用与作品应单独记录关联用户 ID，媒体文件只存安全对象引用，服务器负责鉴权与隐私。该接口**尚未实现**。

## 4. 舞蹈音乐、FFmpeg 和 Wan 参考素材

`data/dance/dance_music/纳西三部曲.mp3` 存在，230,147 字节；当前虚拟环境 `soundfile` 可解码为 MP3、48,000 Hz、双声道、约 9.199 秒，SHA-256 为 `312be601cd8d065c1cb000b43c25981a44b203d3c8e041636ccec3aea17a55b2`。目前项目中未见该文件的来源、创作者、授权、节拍人工标注；文件名仅表示用户放置的标签，**不证明曲名或纳西音乐身份**。未推断 BPM、拍号、起拍位置或两小节边界。

当前 PATH 中 `ffmpeg`、`ffprobe` 均不可用。下一阶段可从 [FFmpeg 官方下载页](https://ffmpeg.org/download.html) 指向的 Windows 构建获取可执行文件，放入项目外的受控工具目录并配置 `FFMPEG_BIN`/`FFPROBE_BIN`，不修改全局 Python。先用 `ffprobe -v error -show_streams -show_format <输入>` 验证编码、时长、音轨，再对**生成结果副本**用 FFmpeg 合并音视频；检查输出 MP4 解码/同步后才交付。节拍检测须附算法与置信度、让用户人工确认，不能仅凭 9.199 秒自动宣布为“两小节”。此轮不安装 FFmpeg、不合成音视频。

服饰参考 `data/dance/dance_outfits/` 四张 JPEG 均可读，均为 1276×2848 的窄长截图，含人物、文字及手机边框；服饰轮廓可见，但需制作**授权的无字、少边框参考副本**才能较稳地给 Wan 做服饰参考，原图不动。背景 `data/dance/dance_backgrounds/` 六张 JPEG 均可读：古城 1276×824、小山 1276×681、平原 2184×1276、经幡 2160×1276、草甸 700×496、雪山 1276×690。适合做场景候选预览；`草甸` 分辨率较低，放大效果待实测。任何图片的地点、服饰文化归属及使用权仍待核实。Wan 仍以玩家上传的个人舞蹈视频为动作来源；原教学视频只用于游戏学习，不发送给 Wan。本轮未调用视频 API。

## 5. Web 样板交付

`web/` 是独立 Vite/React/TypeScript 工程。首页选定 A+B+C：原古城背景和大标题形成首屏游戏主角；剧情/文化书/问答用原立绘、原书页、纸张质感；Agent 入口与 Mock 页面用靛蓝科技感。桌面与手机响应式布局已实现。`app.py` 原 Streamlit 入口保持可运行。

已可操作：首页/目录导航、开始与继续、17 个可见剧情节点、五页文化书、16 道东巴题、答题反馈、错题跨轮重问、三次错答待复习、通关后 Agent/跳过分支、退出并自动存档、重进恢复，以及独立 Web 东巴离线 Mock 页面。Web Mock 通过 `web/tools/mock_api.py` **只调用现有** `DongbaHandwritingAgent(mock=True)`，不调用真实模型；支持画布与照片上传。原有完整 Streamlit Agent 可从 Web 新标签页打开，返回时浏览器存档仍在。

尚未完成：后续古乐/打跳游戏原生迁移、原剧情动画和全部立绘状态的逐帧还原、云存档、三个 Agent 的统一 Web 服务接口、作品媒体存储、舞蹈音乐节拍映射与 FFmpeg 合成。目录中明确显示未迁移章节，不把占位页面称为完成。

资源由 `web/tools/import_godot.py` 从原工程只读复制东巴样板必需的 23 个文件，并在 `web/src/game/asset_manifest.json` 记录 SHA-256。原资源不删除、不移动、不覆盖。后续章节应按审计清单逐项导入并核对授权与哈希。

## 6. 启动、验证与下一批任务

在项目根目录开两个终端：

```powershell
.\.venv\Scripts\python.exe web\tools\mock_api.py
cd web
npm.cmd run dev
```

打开 `http://127.0.0.1:5173/`。如果只预览游戏而不测试 Agent Mock，可仅启动 `npm.cmd run dev`。原 Streamlit 可另行运行 `.\.venv\Scripts\python.exe -m streamlit run app.py`，用于页面内“打开现有 Agent”。

下一批古乐：迁移 `clear_story`、`music_intro` 的音频事件、六页书、五题问答与完成页；核对音频文件名和剧情称谓冲突；接入现有古乐服务的离线接口。下一批打跳：迁移 `dance_intro`、五页书、完整/分段教学视频、三组口诀判定、完成与过场；确认教学素材版权和具体动作名称，再做节拍人工标注与 FFmpeg 后处理。统一平台阶段：账号/云存档、Agent 任务记录与成本控制、作品管理；继续保留 Streamlit 版本以便回退。

## 7. 自动化测试与视觉验收

| 检查 | 结果 |
| --- | --- |
| `npm.cmd test` | 2 个测试文件、6 项通过：16 题通关、三次错答/跳过、游客存档恢复与损坏回退、拒绝写入处理，以及首页→完整东巴章节→Agent→目录→继续游戏的 jsdom 模拟交互串联 |
| `npm.cmd run build` | TypeScript 检查与 Vite 生产构建通过 |
| `python -m unittest discover -s web/tools -p test_mock_api.py -v` | 3 项通过：错误图形判 `incorrect`、空白图质量拒绝、缺少标准字明确报错 |
| `python -m unittest tests.test_dongba_agent tests.test_glyph_data -v` | 现有东巴 Agent/字库 20 项通过，业务代码未改 |
| HTTP 经 Vite 代理请求本地 Mock | `200`，返回 `source=mock`、`status=incorrect`；无真实 API 调用 |
| 原资源哈希 | 导入的 23/23 份副本与 Godot 源及 manifest 一致；另 2 个正式流程音频仍缺失 |
| 原有东巴读音文件 | 5/5 个 OGG 均可由当前 Python 音频库解码，时长约 2.00–4.97 秒；浏览器实际播放仍需目标设备复核 |

实际浏览器桌面 1440×900 与手机 390×844 截图：

- 首页：[桌面](.oil-ui/milestone6b/screenshots/page-1440x900.png)、[手机](.oil-ui/milestone6b/screenshots/page-390x844.png)
- 章节目录：[桌面](.oil-ui/milestone6b/chapters-final/page-1440x900.png)、[手机](.oil-ui/milestone6b/chapters-final/page-390x844.png)
- 东巴剧情：[桌面](.oil-ui/milestone6b/story/page-1440x900.png)、[手机](.oil-ui/milestone6b/story/page-390x844.png)
- 文化书：[桌面](.oil-ui/milestone6b/book/page-1440x900.png)、[手机](.oil-ui/milestone6b/book/page-390x844.png)
- 问答：[桌面](.oil-ui/milestone6b/quiz/page-1440x900.png)、[手机](.oil-ui/milestone6b/quiz/page-390x844.png)
- 东巴 Mock：[桌面](.oil-ui/milestone6b/agent-final/page-1440x900.png)、[手机](.oil-ui/milestone6b/agent-final/page-390x844.png)

Oil UI 截图检查无控制台错误、横向溢出或失败图片；Mock 页首轮的行高问题及目录页首轮的对比度/行高问题已通过样式修正并重新截图。已自行查看所有上述实际截图；未进行独立设计评审。纯浏览器手动触屏绘制、照片 EXIF 方向和原 OGG 声音播放尚未逐设备测试，需现场在目标设备复核。
