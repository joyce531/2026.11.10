# Milestone 6C：纳西古乐原生 Web 迁移报告

审计和实现日期：2026-11-09。原 Godot 工程 `D:\dachuang\naxi-game\project.godot` 只读；未修改 Streamlit、东巴 Agent、舞蹈模块、`.env`，未调用任何模型 API。Web 在 6B 的 React + TypeScript 项目上增量实现。

## 文件清单

- 修改：`web/tools/import_godot.py`、`web/src/main.tsx`、`web/README.md`。
- 新增：`web/src/game/MusicChapter.tsx`、`web/src/game/music.css`、`web/src/game/music_content.json`、`web/src/agents/music_contract.ts`、`web/src/music_flow.test.tsx`、`web/src/game/music_state.test.ts`、`web/tools/test_music_import.py`、本报告。
- 导入脚本更新：`web/src/game/asset_manifest.json`、`web/src/game/dialogues.json` 及 `web/public/godot/Assets/music/` 的 7 段媒体和 `web/public/godot/Assets/culture_book/illustrations/music/` 的 3 张图；原工程中的源文件未改动。截图保存在 `.oil-ui/milestone6c/`。

## 原版流程与实现对应

| 原工程依据 | 原版内容与规则 | Web 对应 |
| --- | --- | --- |
| `Core/GameManager.gd`、`Dialogues/clear_story.dtl` | 东巴通关后两句过渡；再进入古乐导入 | `/game/clear_story`，东巴通关页新增“继续古乐剧情” |
| `Dialogues/music_intro.dtl`、`Scenes/VNStage.gd` | 六句对话；两段 OGG 音频、两个人物立绘和室内背景；无对话选择 | `/game/music_intro`，原话与音频按事件位置展示；手动播放/暂停/重播 |
| `Data/content.json:culture_books.music`、`Scenes/CultureBook.gd` | 六页：古乐引入、洞经/白沙介绍、乐器、两类音乐对比；三张插图 | `/game/music_book`，原文、原图、翻页与移动端排版 |
| `Data/content.json:quizzes.music`、`Scenes/MusicQuiz.tscn`、`Scenes/QuizCard.gd` | 五道原 OGV 音乐辨识题，洞经/白沙二选一；答对进入下一题，答错下一轮重问，累计三错标记跳过；答题正确/错误使用两段 OGG 反馈音效；JSON 的 `pass_ratio=0.8` 在原脚本中未用作通关门槛 | `/game/music_quiz`，原题、原答案/解释、原音视频、相同错答规则与两段反馈音效；显式播放/暂停/重播 |
| `Data/content.json:completion_pages.music` | 原标题、总结、雪山背景，进入下一段舞蹈剧情 | `/game/music_complete`，保留原文与背景；可进入古乐 Agent 入口或返回目录。舞蹈剧情尚未迁移，不伪装为已完成 |

章节导航仍由 `web/src/game/state.ts` 的 `FLOW` 管理。剧情位置、文化书页、题目状态、错答次数和反馈写入原 6B 的游客 `localStorage` 存档；两章题目快照分别存入 `miniGames.dongbaQuiz` 和 `miniGames.musicQuiz`。目录可从古乐章节重新开始、从文化书/辨识题进入、继续当前古乐位置、跳过整章或重看通关。完成与跳过分别进入 `completedSteps`、`skippedSteps`。跳过古乐后指向未迁移的 `dance_intro`，首页的继续按钮返回目录，不展示虚构的舞蹈关卡。章节中“退出并保存”与“跳过本章”均可使用。

## 素材与文化资料

只读导入脚本 `web/tools/import_godot.py` 从原 `Data/content.json` 生成 `web/src/game/music_content.json`，并将本章用到的原资源复制到 `web/public/godot/`。五段辨识素材为 `Assets/music/dongjing/dongjing_01/02/03.ogv` 和 `Assets/music/baisha/baisha_01/02.ogv`；两段剧情素材为 `Assets/music/stingers/stinger_fail_dongjing.ogg`、`stinger_win_baisha.ogg`；三张知识书插图为 `Assets/culture_book/illustrations/music/` 下的 `dongjing_performance.png`、`naxi_instruments.png`、`baisha_performance.png`。人物、背景、书页纹理延用 6B 原素材副本。导入清单中的 33 个现存文件均有 SHA-256，音乐七段媒体与三张插图经逐字节比对和哈希复核，与原工程一致。

原 `music_intro.dtl` 将 `stinger_fail_dongjing.ogg` 的播放结果称为“白沙细乐”，将 `stinger_win_baisha.ogg` 称为“洞经音乐”；**脚本称呼与文件名相反**。本轮保留原话与原音频，并在两段播放处标记“身份待核实”，没有据文件名修改文化判断。原 `Data/content.json` 有两类音乐和乐器说明，**没有可核实的具体曲牌名称、曲牌教学步骤或曲牌音频**；页面明确标注缺口，未编造。原工程的 `Assets/culture_book/audio/page_turn.ogg` 仍缺失，故保留无声翻页。另一个既有缺失文件 `Assets/dongba/sentence/dongba_sentence_01.ogg` 与本章无关。

## Web Agent 边界

古乐通关进入 `/agent/music`，可返回通关页、目录或首页；进度不会丢失。`web/src/agents/music_contract.ts` 仅定义未来的曲谱上传、音符校对、编曲请求和 MIDI/WAV 产物类型。当前 Web 古乐 Agent 入口**没有识谱、编曲或音频生成按钮，没有 Mock 结果，也没有网络模型请求**；现有 Streamlit 古乐模块仍可独立打开。技术链路尚需把现有 Python 服务封装为受控 API 后再接入。

## 验收与测试

- `npm.cmd run build`：TypeScript 检查及 Vite 生产构建通过。
- `npm.cmd test`：4 个测试文件、8 个测试通过，包括原东巴从首页到通关的全流程回归、古乐剧情/六页书/五题/Agent 往返/退出恢复、古乐三次错答重问及跳过规则。
- `python -m unittest discover -s web/tools -p test_music_import.py -v`：原 JSON 内容与导入结果一致，七段音乐素材及三张插图与原工程字节一致。
- `python -m unittest discover -s web/tools -p test_mock_api.py -v`：东巴 Agent 本地 Mock 的 3 个既有回归测试通过。
- 浏览器验收：桌面 1440×900 和手机 390×844 的剧情、文化书、辨识题截图在 `.oil-ui/milestone6c/`；检查工具未发现控制台错误、横向溢出或图片加载失败。原 OGV 题目与剧情 OGG 片段在浏览器点击“从头重播”后时间均由 0:00 走到 0:02，播放/暂停控件可操作。截图中的 OGV 画面为黑色，**这里只能确认容器和时间轴在本机浏览器运行，尚不能据此证明视频画面解码或扬声器音质**；音乐试听仍需人工听验。浏览器不支持原格式时页面会提示，未替换为未经核实的曲目。

截图：[章节目录桌面](.oil-ui/milestone6c/chapters/page-1440x900.png)、[章节目录手机](.oil-ui/milestone6c/chapters/page-390x844.png)、[剧情桌面](.oil-ui/milestone6c/story/page-1440x900.png)、[剧情手机最终版](.oil-ui/milestone6c/story-final/page.png)、[剧情音频播放](.oil-ui/milestone6c/story-playback/page.png)、[文化书桌面](.oil-ui/milestone6c/book/page-1440x900.png)、[文化书手机](.oil-ui/milestone6c/book/page-390x844.png)、[辨识题桌面](.oil-ui/milestone6c/quiz/page-1440x900.png)、[辨识题手机](.oil-ui/milestone6c/quiz/page-390x844.png)、[题目播放时间轴](.oil-ui/milestone6c/playback/page.png)。

## 仍待处理与下一章

1. 请提供或确认有来源的曲牌名称、知识文字和授权录音；核对剧情两段音频与文本称呼，避免把文件名当文化证据。补齐原翻书音效（若有），并在人耳试听后确认 OGV 的浏览器音频表现；若目标浏览器不支持 OGV，再对原文件只读转码为 MP4/音频副本并核对内容。
2. 打跳章节下一批任务：按原 `dance_intro`、`dance_book`、`dance_learning`、`dance_complete` 与 Dialogic 流程审计逐场景映射；导入原教学视频、舞步图和背景；迁移舞步判定/口诀交互；沿同一 `Progress` 保存小关卡状态；完赛串联现有舞蹈 Agent 入口。教学 OGV 仅用于游戏，不发送给 Wan。随后做桌面/手机截图、离线回归与人工视频试听。

启动：在 `web/` 执行 `npm.cmd run dev`，访问 `http://127.0.0.1:5173/`。Web 游戏无需 API Key；原 Streamlit 启动方式保持不变。
