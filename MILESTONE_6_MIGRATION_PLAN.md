# Milestone 6：Godot 到原生 Web 的分阶段迁移计划

状态：**待选择设计方向，未开始正式迁移**。源工程 `D:\dachuang\naxi-game` 只读；当前 Streamlit `app.py` 和已有 Godot Web 导出继续可运行。完整场景、脚本和资产逐项清单见 [`docs/MILESTONE_6_GODOT_AUDIT.md`](docs/MILESTONE_6_GODOT_AUDIT.md)。本计划不能被当作“原生 Web 已完成”。

## 1. 不可删减的迁移映射

| 源场景/流程 ID | Web 组件/数据 | 验收要点 |
| --- | --- | --- |
| `MainMenu.tscn` | `HomeHero`, `ChapterIndex` | 古城原图、开始/继续、章节目录；游戏占首屏主体 |
| `VNStage.tscn` / `opening` | `DialogueStage` + `opening.dtl` | 16 句、院落→室内、人物左右、等待与切场 |
| `VNStage.tscn` / `clear_story` | 同上 + `clear_story.dtl` | 2 句原文和过场 |
| `VNStage.tscn` / `music_intro` | 同上 + `music_intro.dtl` | 6 句及两段原音频；曲种标签冲突先核实 |
| `VNStage.tscn` / `dance_intro` | 同上 + `dance_intro.dtl` | 5 句原文；文化断言待来源核验 |
| `VNStage.tscn` / `dance_transition` | 同上 + `dance_transition.dtl` | 空对白时间线仍有背景切换，迁移时保留动作 |
| `VNStage.tscn` / 未调用 `dongba_intro.dtl` | `DialogueStage` 的保留资料 | 不接入现行主流程，标记未使用 |
| `CultureBook.tscn` / `dongba_book` | `CultureBookStage` + 5 页 | 原书页纹理、文字、插图、翻页 |
| `CultureBook.tscn` / `music_book` | 同上 + 6 页 | 相同布局和顺序 |
| `CultureBook.tscn` / `dance_book` | 同上 + 5 页 | 相同布局和顺序 |
| `DongbaQuiz.tscn` / `dongba_quiz` | `QuizStage`, `QuizCard` + 16 题 | 4 类题型、3 次错题跳过、跨轮重问、反馈音效 |
| `MusicQuiz.tscn` / `music_quiz` | 同上 + 5 题 | 音乐片段播放、选择/反馈、重复规则 |
| `QuizCard.tscn` | 共用 `QuizCard` | 文/图/音/视频选项、正确/错误/跳过态，重复点击不重复作答 |
| `DanceLearning.tscn` / `dance_learning` | `DanceLearningStage` | 完整片→3 段视频→每段口诀重排；重复口诀同值可互换；不造节奏评分 |
| `CompletionPage.tscn` / `dongba_complete` | `ChapterCompletionStage` | 原完成文案、进入东巴 Agent 或跳过继续 |
| `CompletionPage.tscn` / `music_complete` | 同上 | 原完成文案、进入音乐 Agent 或跳过继续 |
| `CompletionPage.tscn` / `dance_complete` | 同上 | 原完成文案、进入视频 Agent 或跳过继续 |
| `EndScreen.tscn` / `end` | `EndStage` | 原结束文字与返回完整首页 |
| `ResultScreen.tscn` | `LegacyResultStage` 记录 | 现行流程未引用，不伪造失败关卡 |
| `Core/Game.tscn` | `LegacyEmptyGame` 记录 | 原脚本为空，保留映射不伪造玩法 |

此表覆盖全部 11 个场景、15 个现行步骤和 1 个未调用时间线。`test_book`、`test_page` 作为内容组件测试数据迁移，不能展示成正式章节。资产迁移以审计文件 88 项全集逐一建 URL/哈希映射；即使目前未引用的图片也留在归档与许可清单。

## 2. 分阶段执行与验收门槛

| 批次 | 实际交付 | 测试、截图、回退条件 |
| --- | --- | --- |
| 0. 设计确认与基线 | 选 A/B/C 或具体拼合；锁定原 Godot 与 Streamlit 基线；核对版权和缺失资源 | 桌面/手机设计截图；记录本轮源文件 hash；旧版启动与现有测试通过 |
| 1. 内容与资源搬迁 | 只读解析器/转换器、`gameFlow`、对话数据、资产清单和浏览器可播视频副本 | 15 步/6 时间线/全部 88 项对账；缺 3 个文件显式报缺；文本逐句比对、OGV 转码副本逐段试听；旧工程无变动 |
| 2. 游戏核心 | React/TS 路由、首页、开始/继续/章节目录、进度 reducer、游客 localStorage | 刷新/关闭/继续/跳关/重玩/退出/断电恢复测试；桌面与手机截图；旧版仍可用 |
| 3. 剧情与文化书 | Dialogic 子集播放器，3 本书与 5 条现行时间线 | 逐句、立绘、背景、页序、音频/缺失状态与 Godot 对照；截图/音频人工验收 |
| 4. 东巴与音乐问答 | 共用 QuizCard + 21 道题 | 固定答案测试、跨轮重问与三错跳过、题目音/图、完成与中途存档；截图与旧版对照 |
| 5. 打跳教学 | 4 段教学视频、三段口诀排列 | 顺序判定、相同口诀可互换、错误重试、视频播放；原口诀文本和视频来源核对 |
| 6. 完成页与 Agent 串联 | 三个完成页分支、独立 Agent 路由、返回游戏/首页/作品 | 分支进入再返回，游戏状态不丢；Mock/真实来源清晰；失败可恢复 |
| 7. 统一后端与作品 | FastAPI 适配、用户/任务/作品/成本与服务端存档 | API 契约、权限隔离、重复提交、预算上限、失败/超时测试；保留 Streamlit 路径 |
| 8. 音乐视频升级与切换 | 已确认两小节音频映射、FFmpeg 合成、部署与账号 | FFmpeg 输出和音画同步、模型作业状态、权限、完整 15 步端到端；经人工验收后才改变正式入口 |

每批遵循“新增旁路实现→单元/集成测试→真实桌面和手机截图→与原游戏逐项对照→回归现有 Agent→可回滚版本”的门槛。若某关的原文字/资源无法核实，保留原版作为基线并把问题标为阻塞，不用模型填空。无需本轮提交 Git；后续正式迁移的版本固化要先保护当前未提交文件。

## 3. 资源与行为对照方法

- 给每个 `res://Assets/...` 引用生成 `source_path → web_url → sha256 → mime → status`，和磁盘上的 88 项做双向对账。`.tres` 的贴图/字体/九宫格边距改用 CSS 或原 PNG；`default_bus_layout.tres` 改成 Web 音量通道。
- 9 段 OGV 对副本转为 Web 可播格式，并用浏览器实际解码、声画时长、首/中/末帧对照验证。正式来源无法转码时保留明确不可播放状态，不替换别的视频。
- Dialogic 以确定性状态机执行：每条对白和背景/站位/声音/等待指令产生可测试事件，末尾只触发一次 `advance`；`dance_transition` 虽无对白仍产生背景事件。
- 问答状态机保留 `pending/done/skipped`、每题累计错数、当前轮队列、位置；还原 `MAX_WRONG=3` 和重复口诀文本判定。Web 新增逐题自动存档，不修改原游戏规则。
- 存档版本号与稳定 `step_id` 绑定。恢复时确认该 ID 存在于当前 `gameFlow`；不把旧 `user://savegame.json` 的索引版 v1 误映射。读取旧 v2 保存若有需要，做显式导入和用户确认；当前项目并未读取原 Godot 用户目录。

## 4. 风险与待确认

1. 教学资料的来源和版权信息不全；照原文迁移不等于文化事实已审定。`music_intro.dtl` 的曲种说法与提示音文件名相反，需要听审并由资料负责人确认。
2. 原 `Data/content.json` 缺 3 个引用目标；东巴句图题读音和翻页声是正式体验影响项。
3. 原文化书与问答以 1920×1080 设计，手机需重新排布但不删内容和交互；翻页书在窄屏可上下堆叠保留顺序。
4. 当前 `data/dance/dance_music/纳西三部曲.mp3` 只有约 9.2 秒，无 BPM/拍号/起拍/逐动作标注；短音频检测结果需人工校对。FFmpeg 在本机 PATH 未发现，音视频合成需要明确安装或配置可执行文件。
5. `data/dance` 的教学 OGV 和 Wan 用户输入职责不同：教学素材只在游戏中播放；Wan 使用玩家本人视频，不把教学全片/拆分舞步额外发送。
6. 当前舞蹈任务只有 Streamlit Session State 生命周期，服务端统一任务/作品持久化前不能宣称多用户云存档已完成。

本轮的三方向可预览页为 `docs/milestone6_design/style-explorer.html`；它只是首页设计对比，不连接后端或开始正式 React 迁移。
