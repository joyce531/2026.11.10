# Milestone 6D：古乐视频修复与打跳章节原生 Web 迁移

日期：2026-11-09。原工程 `D:\dachuang\naxi-game` 只读，项目原 Streamlit、Python Agent、`.env` 和模型配置未修改；未调用 Qwen/Wan 等 API，未提交 Git。先完成古乐视频工作包并测试，再实施打跳章节。

## 1. 审计依据与原 Godot 对照

实际读取了原工程 `project.godot`、`Data/content.json`、`Dialogues/dance_intro.dtl`、`Dialogues/dance_transition.dtl`、`Scenes/DanceLearning.tscn`、`scripts/dance/DanceLearning.gd`、通关/结尾场景与相关素材；Web 侧沿用 `main.tsx`、`state.ts`、`MusicChapter.tsx` 和 `localStorage`。原舞蹈学习顺序为：剧情导入 → 五页文化书 → 完整视频 → 三支分步视频及口诀 → 随机舞步顺序的口诀排序 → 通关 → 过渡 → 结尾。原脚本在每一道排序题内随机摆放字块、按可见口诀顺序比对；相同口诀的不同字块可互换；答错可重试，**无错误次数上限**。本轮保留此规则。

原数据仅有三个完整舞步，**没有第 4/5 步**：

| 原 ID | 原标题 | 原口诀（按动作数据顺序） | 原键位数据 |
| --- | --- | --- | --- |
| `step_01` | 窝热热交错步 | 左、右、左、左、左踢、右踢 | ← → ← ← ↑ ↑ |
| `step_02` | 三步跺脚 | 左、前、左、右、右、前、左、左 | ← ↑ ← → → ↑ ← ← |
| `step_03` | 阿哩哩转身对跳步 | 左、右、左踢、右踢、左踢、右、左、右踢、左踢、右踢 | ← → ↑ ↑ ↑ → ← ↑ ↑ ↑ |

所有 `actions.start/end` 均为 `null`，`instruction` 为空；原工程没有独立口诀语音文件或语音播报代码，也没有对方向键击键进行动作评分。Web 只显示原键位对应关系、可选用**浏览器合成语音**朗读原口诀；没有伪造原声、时间码、逐帧高亮、舞步判定或新的文化解释。原翻书音效 `Assets/culture_book/audio/page_turn.ogg` 缺失，原东巴例句音频 `Assets/dongba/sentence/dongba_sentence_01.ogg` 也仍缺失；均未制作替代品。

| 原 Godot 环节 | Web 路由 / 文件 | 迁移状态 |
| --- | --- | --- |
| `dance_intro.dtl`，人物立绘与室内背景 | `/game/dance_intro`，`DanceChapter.tsx` | 原 5 句对话逐句呈现、退出后保存序号 |
| `culture_books.dance`，5 页与 3 张插画 | `/game/dance_book` | 原文、原图、页序、前后翻页 |
| `DanceLearning.tscn` / `DanceLearning.gd` 完整演示 | `/game/dance_learning` 的 overview | 原完整视频，播放、暂停、进度、音量、重播 |
| 三支分步视频及口诀 | 同路由的 lesson | 原独立视频、原口诀和方向提示；可选合成朗读 |
| `CUE_ARRANGE` 排序逻辑 | 同路由的 arrange，`dance_state.ts` | 随机题序与字块、增删/还原、核对、错误计数、可跳过 |
| `completion_pages.dance` | `/game/dance_complete` | 原通关标题/正文/背景、进度及 Agent 入口 |
| `dance_transition.dtl` 与 EndScreen | `/game/dance_transition`、`/game/end` | 无对话的过渡改为继续按钮，保留结尾文案；原“返回微信问卷”改为返回 Web 首页 |

## 2. 古乐辨识视频映射

五题映射来自**原** `Data/content.json` 中每题 `prompt.audio` 对应的 `res://Assets/music/.../*.ogv`，并核对 `data/music/videos/` 五个文件与 Godot 原片 SHA-256 完全一致；没有按文件名猜曲目。原片均为 Theora/Vorbis OGV，浏览器副本是 H.264/AAC MP4。题目、答案和文化说明未改。

| 题号 | 原游戏题目引用 | 项目原片 | Web 实际引用 | 时长 |
| --- | --- | --- | --- | --- |
| q1 | `Assets/music/dongjing/dongjing_01.ogv` | `data/music/videos/dongjing_01.ogv` | `/game_media/music/dongjing_01.mp4` | 99.99 s |
| q2 | `Assets/music/baisha/baisha_01.ogv` | `data/music/videos/baisha_01.ogv` | `/game_media/music/baisha_01.mp4` | 36.15 s |
| q3 | `Assets/music/dongjing/dongjing_02.ogv` | `data/music/videos/dongjing_02.ogv` | `/game_media/music/dongjing_02.mp4` | 62.04 s |
| q4 | `Assets/music/baisha/baisha_02.ogv` | `data/music/videos/baisha_02.ogv` | `/game_media/music/baisha_02.mp4` | 43.58 s |
| q5 | `Assets/music/dongjing/dongjing_03.ogv` | `data/music/videos/dongjing_03.ogv` | `/game_media/music/dongjing_03.mp4` | 63.74 s |

`MusicChapter.tsx` 现在从 `music_video_manifest.json` 找到各题 MP4，用原生 `<video controls playsInline>` 呈现画面，未设静音；重播将时间归零并调用播放。题目变化时播放器以题目 ID 重新挂载，避免上一题残留。CSS 使用 `object-fit: contain`，不裁切原视频。剧情 OGG 音效仍为原来的音频播放器。

## 3. 打跳视频与资源清单

舞蹈视频引用均来自 `Data/content.json`，不是根据文件名猜测。`web/tools/prepare_game_videos.py` 在**核对项目原 OGV 与 Godot 原文件哈希相同**后，仅编码 Web 副本；第三步已有 `data/dance/dance_videos/datiao_01_step_03_mp4版本.mp4`，核对 H.264/AAC、时长和三个采样位置的画面后直接复用。原 OGV/MP4 均未改动。详细 SHA-256、分辨率和编解码器见 `web/src/game/{music,dance}_video_manifest.json`。

| 内容 | 项目原片 | Web 副本（`web/public` 下） | 页面位置 | 时长 |
| --- | --- | --- | --- | --- |
| 完整演示 | `data/dance/dance_videos/datiao_01_full.ogv` | `game_media/dance/datiao_01_full.mp4` | overview | 177.93 s |
| 窝热热交错步 | `data/dance/dance_videos/datiao_01_step_01.ogv` | `game_media/dance/datiao_01_step_01.mp4` | lesson/arrange | 20.78 s |
| 三步跺脚 | `data/dance/dance_videos/datiao_01_step_02.ogv` | `game_media/dance/datiao_01_step_02.mp4` | lesson/arrange | 14.21 s |
| 阿哩哩转身对跳步 | `data/dance/dance_videos/datiao_01_step_03.ogv`，已有 MP4 | `game_media/dance/datiao_01_step_03.mp4` | lesson/arrange | 8.95 s |

原文化书图片 `Assets/culture_book/illustrations/dance/datiao_{circle,step,together}.png`、室内背景 `Assets/vn/backgrounds/bg_in_the_room.png`、游客/朋友立绘和通关雪山背景都由 `import_godot.py` 复制到 `web/public/godot/`，哈希在 `asset_manifest.json`。原资源保持只读。页面未把教学视频传给 Wan；未来 AI 视频应使用玩家自行上传的视频，生成品也必须单独标识。

兼容性：原 OGV（Theora/Vorbis）不作为浏览器实际播放源，九段 H.264/AAC MP4 使用标准视频控件；原剧情/反馈 OGG 继续走 `<audio>`，并未更改。当前游戏引用的舞蹈文化书、人物、背景均为 PNG，已按 manifest 核实路径；本章节没有 JPG 页面资源。另检 `data/dance/dance_music/纳西三部曲.mp3` 为 9.20 秒、48 kHz、双声道 MP3，**未接入原打跳教学场景**，本轮不把它冒作原视频配乐或覆盖原音轨。浏览器人工听音仍需在现场机器完成。

## 4. 统一存档与 Agent 衔接

三章继续共享 `state.ts` 的 `naxi-ai-studio:guest-save:v1` 本地存档。打跳使用现有 `Progress.miniGames.dance`，记录 `phase`、当前舞步、随机题序/字块、答题排列、错题次数、已完成/已跳过舞步、暂停状态和视频时间点；总 `completedSteps` 与 `skippedSteps` 分开存放，跳过不算完成。可从首页或目录进入，从目录选择任意舞步，退出后继续，刷新后恢复原阶段/舞步/排序与近似视频位置；可暂停、重播或跳过舞步及整章。原 Godot 只保存整体环节，本地 Web 存档更细，但**不会导入 Godot 存档，也不是云端账户**。

打跳通关后可进入 `/agent/dance`，页面明确标记 Web 接口开发中，提供返回通关页/目录与现有 Streamlit 页面链接；Web 未调用 Wan、未生成示例视频。古乐通关可继续打跳剧情。首页仍以游戏为首屏主体，三个 Agent 入口在下方。

## 5. 文件变更与验收

- 修改：`web/src/game/MusicChapter.tsx`、`web/src/game/music.css`、`web/src/main.tsx`、`web/src/music_flow.test.tsx`、`web/tools/import_godot.py`、`web/README.md`。
- 新增代码/测试：`web/src/game/DanceChapter.tsx`、`web/src/game/dance.css`、`web/src/game/dance_state.ts`、`web/src/game/dance_state.test.ts`、`web/src/dance_flow.test.tsx`、`web/tools/prepare_game_videos.py`、`web/tools/test_music_video.py`、`web/tools/test_dance_media.py`。
- 新增导入/副本：`web/src/game/dance_content.json`、两个视频 manifest、`web/public/game_media/music/` 五个 MP4、`web/public/game_media/dance/` 四个 MP4、`web/public/godot/` 中新增的打跳插画/背景/立绘副本；`dialogues.json`/`asset_manifest.json` 由只读导入器更新。

**已实际验证**：`npm test` 6 个测试文件、11 项通过；Python 视频映射/哈希/画面解码 2 项通过；`npm run build` 通过。FFmpeg 9.0.2 探测九段 Web MP4 为 H.264/AAC，逐段解码视频和音频，并对九段音轨执行音量检测，平均音量约 −21.9 至 −33.2 dB（并非静音）。桌面 Chrome 逐题点击后截到 **q1–q5 全部五段视频的实际画面**；反馈按钮调至音频控件前方后，切题时不再被音频控件遮挡。桌面 Chrome 已显示完整舞蹈和三段分步的实际画面；手机 Chrome 已显示完整舞蹈和第一步的实际画面。截图在 `.oil-ui/milestone6d/`，检查无控制台错误、横向溢出或图片加载失败。测试版 Chrome 启动参数含 `--mute-audio`，因此**无法据此声称人工听见声音**；已用 FFmpeg 确认音轨存在且非静音。原生控件的暂停、音量、进度/拖动、重播行为依赖浏览器标准实现；重播按钮与切题映射有组件/单元测试，未逐项完成有声人工试听。

**未解决/下一阶段**：补回原缺失的翻书音效、东巴例句音频需用户提供原资料；打跳口诀原声与动作时间码本来不存在，若要原声教学或逐动作循环需提供录音/标注；文化知识仍以原工程为准，后续需来源核实；游客存档清除浏览器数据后不可恢复；Web AI Agent/账号云存档未接入。下一阶段可在服务端封装现有 Wan 视频服务，明确区分教学视频、玩家上传视频和生成结果，并加入同意、任务防重复提交、成本控制及作品存储；本轮没有开始这些 API 工作。

本地预览：项目根目录执行 `cd web`，再执行 `npm.cmd run dev`，访问 `http://127.0.0.1:5173/`。原 Streamlit 仍可单独运行。
