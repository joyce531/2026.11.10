# 纳西文化之旅 · 原生 Web 迁移样板

React + TypeScript 前端保留原 Streamlit 应用和只读的 Godot 工程。现在可从首页或目录独立游玩**东巴文字、纳西古乐、纳西打跳三个章节**。完整 AI Agent Web 接口尚未迁移；游戏中的入口会明确显示开发状态，不会自动调用真实模型。

在项目根目录启动本地 Mock 接口（仅调用现有 Python 本地评价，不调用 AI API）：

```powershell
.\.venv\Scripts\python.exe web\tools\mock_api.py
```

另开终端启动前端：

```powershell
cd web
npm.cmd install
npm.cmd run dev
```

打开 `http://127.0.0.1:5173/`。古乐章节是“剧情 → 六页文化书 → 五道原视频辨识题 → 通关”；打跳章节是“剧情 → 五页文化书 → 完整演示 → 三支分步教学视频 → 口诀排序 → 通关”。三个游戏章节不需要 Python Mock 接口，只有东巴 Agent 的 Web Mock 提交需要。需要现有完整 Agent 时，再从项目根目录运行 `.\.venv\Scripts\python.exe -m streamlit run app.py`。Web 游戏本身不调用真实 AI API。

代码分布：`src/game/*_content.json` 导入原 `Data/content.json` 的章节数据，`src/game/dialogues.json` 导入原 Dialogic 事件；`MusicChapter.tsx` 与 `DanceChapter.tsx` 呈现游戏；`dance_state.ts` 实现原舞步排序规则；`state.ts` 管理同一份游客存档。`public/godot/` 是原图片/音频的只读副本，哈希见 `asset_manifest.json`。OGV 原片保留在 `data/music/videos/` 和 `data/dance/dance_videos/`，浏览器用 `public/game_media/` 的 H.264/AAC MP4 副本；原片、Web 副本与页面引用关系及哈希见两个 `*_video_manifest.json`。重新导入资源可运行 `tools/import_godot.py`，视频副本生成方法见 `MILESTONE_6D_REPORT.md`。

测试：

```powershell
cd web
npm.cmd test
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m unittest discover -s web\tools -p test_mock_api.py -v
.\.venv\Scripts\python.exe -m unittest discover -s web\tools -p test_music_import.py -v
.\.venv\Scripts\python.exe -m unittest web.tools.test_music_video web.tools.test_dance_media
```

游客进度存储在此浏览器的 `localStorage`，记录当前剧情/书页/题目、每个舞步的完成或跳过、排序错误次数、视频时间点和 Agent 使用记录；三个章节共用同一份存档。清除浏览器站点数据会失去游客存档，尚无云同步。原 Godot 存档不会自动导入。

原工程没有舞步动作时间码、独立口诀录音和翻书音效文件。打跳页面可选择用浏览器合成语音朗读原口诀，并明确标注不是原声；不支持此功能的浏览器会禁用按钮。古乐题目保持原答案和文化内容，视频无法播放时明确报错，不偷换曲目。详细验收与未解决问题见根目录 `MILESTONE_6D_REPORT.md`。
