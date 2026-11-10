# Naxi AI Studio｜教育赛道 HTML 展示

21 页、16:9、可离线打开的 HTML 展示，以“AI 赋能冷门绝学课程，让纳西非遗走进校园美育课堂”为主线。打开 [index.html](index.html) 即可预览。方向键、空格和 PageUp/PageDown 翻页；F 或右上角按钮全屏。每页固定单屏，不需要上下滚动。

| 部分 | 页码 | 主题 |
| --- | --- | --- |
| （一）作品背景与说明 | 1 | 艺术封面、项目定位 |
| （二）数据收集与处理 | 2–5 | 来源、资源库、预处理、课程化 |
| （三）分析过程 | 6–10 | 方法、真实游戏学习画面、教学闭环、实际架构 |
| （四）创新性与独特视角 | 11–12 | 制度保障与 AI 教学转化互补、跨学科 Agent |
| （五）结果解释与建议 | 13–18 | 调用、前后测、TAM、问题、代码证据、风险 |
| （六）应用结果呈现 | 19–20 | 真实 UI/视频、任务提示词、结果与本地入口 |
| 尾声 · 项目总结 | 21 | 项目主张、视觉收束 |

六章首张页（1、2、6、11、13、19）使用入章排版。封面以 **Living Naxi** 为艺术主标题，保留 Naxi AI Studio 平台标识；第 21 页用大字、阴影和倒影总结项目。第 7 页专门展示东巴文化书、古乐视频辨识和打跳教学的真实 Web 截图；上方标签可切换原有三门课程对照图。逐页讲稿见 [research/SPEAKER_SCRIPT.md](research/SPEAKER_SCRIPT.md)。第 1–14 页依次使用用户提供的 P1–P14，第 15–21 页依次复用 P1/P4/P1/P2/P3/P4/P1。每页只用一套背景派生的主题色；部分原图文字与本项目无关，公开使用前须确认授权。

## 可编辑图表与截图

13 张独立可编辑 SVG 在 [diagrams/](diagrams/)；源代码为 [scripts/build_diagrams.py](scripts/build_diagrams.py)。页面内容源在 [scripts/build_deck.py](scripts/build_deck.py)，样式在 [styles/site.css](styles/site.css) 与 [styles/deck.css](styles/deck.css)。旧 `build_pages.py` 已停用。

19 个真实资料截图位分布在第 2、7、16、17、19、20 页，涵盖游戏学习、素材数据库、问卷、实地调研、Agent 结果、关键代码和真实 Web 界面。第 7 页的 3 张游戏截图由本地 Web 游戏直接截取；其他材料仍按真实到件情况启用。具体文件名、拍摄内容及脱敏规则见 [research/SCREENSHOT_SHOTLIST.md](research/SCREENSHOT_SHOTLIST.md)。把 PNG/JPEG 放入 `assets/evidence/` 后运行：

```powershell
.\.venv\Scripts\python.exe presentation\naxi-html\scripts\enable_evidence.py
```

脚本只启用实际存在且可解码的图片。所有幻灯片缩略图统一为 **4:3**，可裁切填充；点击后查看未裁切的原始图片，长代码截图也能完整检查。原截图文件不会被改动。没有原件时保留待插入，不伪造调查、图片或 Agent 输出。

资料页、结果页和提示词页采用错位阅读路径。第 19 页一次只显示一个 Agent 的 4:3 截图，可用标签切换；演示视频仅占用一条链接。录制说明见 [research/DEMO_VIDEO_SHOTLIST.md](research/DEMO_VIDEO_SHOTLIST.md)。录好并上传到有权访问的 HTTPS 地址后，将链接填入 `assets/demos/links.json`，再运行：

```powershell
.\.venv\Scripts\python.exe presentation\naxi-html\scripts\enable_videos.py
```

若重新生成全部页面，顺序为 `build_diagrams.py`、`build_deck.py`、`enable_evidence.py`、`enable_videos.py`。空视频链接只显示“待添加”；本展示打开时不会调用任何付费 AI API。

研究数字来自项目 Word 大纲，原始匿名数据和分析脚本仍待归档；舞步识别前后测 `p=.296`，未达显著。技术与证据边界见 [research/EVIDENCE_LEDGER.md](research/EVIDENCE_LEDGER.md)。
