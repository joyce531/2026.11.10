# Milestone 6：Godot 原工程完整迁移审计

审计日期：2026-11-09。原工程 **`D:\dachuang\naxi-game`** 的 `project.godot` 已核实。只读检查了项目自有的全部 11 个 `.tscn`、14 个 `.gd`、10 个 `.tres`、6 条 Dialogic 时间线、2 个角色定义、`Data/content.json`、导出配置及 `Assets/`。`addons/dialogic/` 为随工程携带的第三方插件（约 956 个文件），迁移时保留其内容语义但不逐文件重写插件；`.godot/` 为编辑器缓存，不是迁移源。没有启动或修改原工程。本报告列出项目自有资源；Godot 生成的 `.import`、`.uid`、`.xmp` 旁车文件不当作独立画面或关卡。

## 1. 工程组织与运行入口

| 路径 | 作用 |
| --- | --- |
| `project.godot` | Godot `4.6` 特性、1920×1080 画布；主场景 `Scenes/MainMenu.tscn`；启用 Dialogic；自动加载 `GameManager`、`SceneLoader`、`ContentDB`、`ControlBar` |
| `Core/` | 15 步流程、问答状态、存档、淡入淡出、资源读取及游戏控制栏；`Game.tscn`/`game.gd` 为无实际逻辑的旧骨架 |
| `Scenes/` | 主菜单、视觉小说承载场景、共用文化书、东巴/音乐问答、打跳学习、通关页和结束页 |
| `scripts/dance/` | 打跳教学和口诀排列小游戏的实际脚本 |
| `Data/content.json` | 两套问答、三套文化书、三套通关页、一次打跳教学的内容与资源路径；另有 `test_book`/`test_page` 测试定义 |
| `Dialogues/` | 6 条 `.dtl` 时间线及 `host.dch`、`tourist.dch` 人物肖像配置 |
| `Assets/` | 67 PNG、9 OGV、9 OGG、1 WAV、1 TTF，以及字体许可文本；共 88 个可复用正式素材/说明文件 |
| `export_presets.cfg` | 已有 Web 单线程导出预设，指向 `..\..\livingnaxi-web2\index.html`；本轮原生迁移不采用嵌入 Web 导出作为完成方式 |
| `Features/`、`Shared/` | 当前无项目文件；不要凭目录推断尚有隐藏玩法 |

项目代码为 GDScript，未发现项目自有 C#。`project.godot` 只写 `4.6` 特性，**不能仅凭此文件证明补丁号 4.6.1**。Dialogic 用于剧情对话、角色站位、背景切换与音乐播放；Web 需实现对应数据播放器，不移植 Godot 插件运行时。

## 2. 场景—脚本—Web 对应关系（全部 11 个）

| Godot 场景 | 实际脚本/数据 | 当前作用与状态 | 原生 Web 目标 |
| --- | --- | --- | --- |
| `Scenes/MainMenu.tscn` | `Scenes/MainMenu.gd`, `GameManager.has_save()` | 古城背景；无存档开始，有存档继续/重新开始 | `/` 首页游戏主视觉与继续入口，`/chapters` 章节目录 |
| `Scenes/VNStage.tscn` | `Scenes/VNStage.gd` + 6 条 `.dtl` | 读取 `pending_timeline`，在 Dialogic 结束或 `advance` 信号后推进 | `/game/:stepId` 中 `DialogueStage`，逐句渲染人物/背景/等待/音频 |
| `Scenes/CultureBook.tscn` | `Scenes/CultureBook.gd` + `culture_books` | 共用翻页书，支持文/图左右布局、过渡、末页推进 | `CultureBookStage`，原内容与书页纹理、前后翻页及缺图状态 |
| `Scenes/DongbaQuiz.tscn` | `Scenes/QuizScene.gd`、实例 `QuizCard.tscn` | 16 道题；图→义、音→图、义→图、句图→义 | `QuizStage` 的 `dongba` 数据实例 |
| `Scenes/MusicQuiz.tscn` | 同上 | 5 道听/看音乐片段分类题 | `QuizStage` 的 `music` 数据实例 |
| `Scenes/QuizCard.tscn` | `Scenes/QuizCard.gd` | 共用题卡，选项按钮、图/音/视频、反馈与音效 | `QuizCard` 组件，五种题型及正确/错误/跳过视觉态 |
| `Scenes/DanceLearning.tscn` | `scripts/dance/DanceLearning.gd` + `dances.datiao_01` | 完整视频→三段教学→三组口诀排列→完成 | `DanceLearningStage`，HTML5 视频和可点选口诀排列 |
| `Scenes/CompletionPage.tscn` | `Scenes/CompletionPage.gd` + `completion_pages` | 东巴、音乐、舞蹈复用的阶段完成页 | `ChapterCompletionStage`，加入进入对应 Agent/跳过继续 |
| `Scenes/EndScreen.tscn` | `Scenes/EndScreen.gd` | Demo 结束，返回主菜单 | `/game/end`，返回完整平台首页 |
| `Scenes/ResultScreen.tscn` | `Scenes/ResultScreen.gd` | 旧的失败/重试页；现行流程未跳转，`last_result` 未填充 | `/game/legacy-result` 兼容映射；记录为历史未使用，不凭空接入主流程 |
| `Core/Game.tscn` | `Core/game.gd` | `_ready`/`_process` 均为空，实现骨架且非主场景 | `legacy/empty-game` 迁移记录，不新增虚假游戏画面 |

### 共用脚本映射

| 脚本 | 要保留的行为 | Web 对应 |
| --- | --- | --- |
| `Core/GameManager.gd` | 15 步顺序、进入/推进、问答 3 次错题跳过和跨轮重问、`step_id` 存档 | 版本化 `gameFlow` 数据 + 纯函数 reducer + 持久化进度服务 |
| `Core/SceneLoader.gd` | 0.3 秒黑场换场并防重复进入 | 路由过场、导航锁和 reduced-motion 回退 |
| `Core/ContentDB.gd` | 读取 `content.json`，按路径加载图/音/视频；缺资源显式回退 | 内容清单构建时校验、资源 URL 映射、缺失状态 |
| `Core/ControlBar.gd` | 游戏内菜单：暂停/恢复、全程重来、保存退出、不保存退出；暂停媒体 | 游戏内控制栏与媒体暂停；Web“退出”返回平台首页并保存策略明确 |
| `Scenes/QuizScene.gd` | 从 GameManager 读题、答题、继续下一题/轮 | `QuizStage` 控制器 |
| `Scenes/QuizCard.gd` | 五种题型、提示/音效/反馈、点击继续 | `QuizCard` UI + Web Audio/Video |

全部 10 个项目自有 `.tres`：`default_bus_layout.tres`、`Assets/vn/style/naxi_style.tres`、`Assets/vn/UI/screens/shared/screen_theme.tres`、`Assets/vn/UI/quiz/quiz_theme.tres`、`Assets/vn/UI/quiz/quiz_progress_panel_texture.tres`、`Assets/vn/UI/quiz/quiz_feedback_panel_texture.tres`、`Assets/vn/UI/quiz/quiz_audio/{quiz_audio_bg_normal_texture,quiz_audio_bg_hover_texture,quiz_audio_bg_pressed_texture,quiz_audio_play_icon_texture}.tres`。它们是 Godot 的音频总线/主题/纹理包装；Web 需重建 CSS 和媒体播放规则，并复用引用的 PNG，不直接读取 `.tres`。

## 3. 现行流程与每关实际功能

顺序取自 `Core/GameManager.gd::_build_flow()`，不是按文件名推测：

| 顺序 / 稳定 ID | 内容源 | 玩家行为 / 跳转 | Web 路由状态 |
| --- | --- | --- | --- |
| 1 `opening` | `Dialogues/opening.dtl` | 院落→室内，朋友与游客对话，引出东巴文 | 剧情页；待迁移 |
| 2 `dongba_book` | `culture_books.dongba` | 5 页阅读与翻页 | 文化书；待迁移 |
| 3 `dongba_quiz` | `quizzes.dongba` | 16 题、4 类题型；错题再次出现，累计错 3 次跳过 | 问答；待迁移 |
| 4 `dongba_complete` | `completion_pages.dongba` | 完成阶段，当前只继续 | 完成页 + 东巴评价分支；待迁移 |
| 5 `clear_story` | `Dialogues/clear_story.dtl` | 东巴阶段后的过渡对话 | 剧情页；待迁移 |
| 6 `music_intro` | `Dialogues/music_intro.dtl` | 播放两段提示音并引入音乐分类 | 剧情/音频；待迁移 |
| 7 `music_book` | `culture_books.music` | 6 页阅读与翻页 | 文化书；待迁移 |
| 8 `music_quiz` | `quizzes.music` | 5 道音乐分类题；同一重问规则 | 音乐问答；待迁移 |
| 9 `music_complete` | `completion_pages.music` | 完成阶段，当前只继续 | 完成页 + 音乐 Agent 分支；待迁移 |
| 10 `dance_intro` | `Dialogues/dance_intro.dtl` | 打跳教学导入 | 剧情页；待迁移 |
| 11 `dance_book` | `culture_books.dance` | 5 页阅读与翻页 | 文化书；待迁移 |
| 12 `dance_learning` | `dances.datiao_01` | 先看完整视频，再看 3 段教学；随机打散每段口诀后按可见口诀顺序排列判定 | 舞蹈小游戏；待迁移 |
| 13 `dance_complete` | `completion_pages.dance` | 完成阶段，当前只继续 | 完成页 + 视频 Agent 分支；待迁移 |
| 14 `dance_transition` | `Dialogues/dance_transition.dtl` | **时间线文件存在但为空背景声明，没有对白** | 保留空过渡的状态与切场，需决定是否允许零内容自动推进 |
| 15 `end` | `Scenes/EndScreen.tscn` | 返回主菜单 | 结局页；待迁移 |

原问答没有通关率判定：`pass_ratio` 虽在 JSON 中，现行 `GameManager` 不使用；问错题会在下一轮重问，三次累计错误后显示复习提示并标记 `skipped`。`ResultScreen` 是未调用的旧实现。打跳小游戏按**可见口诀文本**而非内部 action ID 比对，重复口诀可互换；没有动作识别或节奏打分。`actions[*].start/end` 当前为 `null`，说明尚无逐动作时间标注，不能声称已有节拍映射。

## 4. 剧情与 Dialogic 清单

| 文件 | 实际内容 / 迁移注意 |
| --- | --- |
| `opening.dtl` | 16 句双人对话；院落、门声、室内背景切换、人物进退；整段原文需逐句保留 |
| `dongba_intro.dtl` | 5 句东巴引导，但**不在现行 15 步流程内**；保留为可追溯未使用时间线 |
| `clear_story.dtl` | 2 句文化过渡 |
| `music_intro.dtl` | 6 句、两段 `stinger` 音频和等待指令；文案对两段音频的曲种称呼与文件名标签相反，需人工核对音源/文案，不能按文件名擅自改剧情 |
| `dance_intro.dtl` | 5 句打跳引导，包含未经本轮核验的文化陈述；迁移照录，同时建立来源审核项 |
| `dance_transition.dtl` | 仅一条室内背景指令，无对白 |
| `host.dch` / `tourist.dch` | “朋友”“游客”角色名、左右位置、色彩、肖像；host 默认/正装 2 张，tourist 默认及喜/悲状态共 7 张肖像配置；保留资产引用关系 |

Dialogic 指令类型实际出现：`background`、`join`、`leave`、`clear`、`wait`、`audio example`；Web 播放器只实现项目用到的指令子集并保留原时间线与播放顺序。原文中关于东巴字、纳西音乐和打跳的文化解释**未有来源元数据**；迁移不是专家校对，发布前需逐项核验。

## 5. 图片、音频、视频与字体清单（项目自有资产全集）

以下路径均以原工程 `Assets/` 为根；同组名称仅是文件名，不代表文化身份已验证。迁移后要建立每个源路径到 Web 资源 URL 的逐项映射并核对 hash/授权，不直接运行 Godot 资源系统。

| 类别 | 全部文件 |
| --- | --- |
| 视觉小说背景 5 PNG | `vn/backgrounds/bg_ancient_city.png`, `bg_at_home_yard.png`, `bg_in_the_room.png`, `bg_snow_mountain.png`, `bg_snow_pasture.png` |
| 人物立绘 12 PNG | `vn/portraits/char_male_casual.png`, `char_male_formal.png`, `char_tourist_camera.png`, `char_female_happy_01.png`, `char_female_happy_02.png`, `char_female_happy_03.png`, `char_female_neutral.png`, `char_female_sad_01.png`, `char_female_sad_02.png`, `char_female_sad_03.png`, `char_pedestrian_01.png`, `char_pedestrian_02.png` |
| 视觉装饰 1 PNG | `vn/decorations/deco_dongba_painting.png` |
| 屏幕共用 UI 7 PNG | `vn/UI/screens/shared/screen_info_panel_9p.png`, `screen_divider.png`, `screen_deco_diamond.png`, `screen_button_normal_9p.png`, `screen_button_hover_9p.png`, `screen_button_pressed_9p.png`, `screen_button_disabled_9p.png` |
| 问答纸面 UI 7 PNG | `vn/UI/quiz/quiz_paper/quiz_title_plaque_9p.png`, `quiz_progress_deco.png`, `quiz_main_panel_9p.png`, `quiz_feedback_panel_9p.png`, `quiz_corner_pattern.png`, `quiz_cloud_left.png`, `quiz_cloud_right.png` |
| 问答选项 UI 7 PNG | `vn/UI/quiz/quiz_option/quiz_option_bg_normal_9p.png`, `quiz_option_bg_hover_9p.png`, `quiz_option_bg_pressed_9p.png`, `quiz_option_bg_correct_9p.png`, `quiz_option_bg_wrong_9p.png`, `quiz_option_bg_skipped_9p.png`, `quiz_option_bg_disabled_9p.png` |
| 问答播放 UI 4 PNG | `vn/UI/quiz/quiz_audio/quiz_audio_bg_normal_9p.png`, `quiz_audio_bg_hover_9p.png`, `quiz_audio_bg_pressed_9p.png`, `quiz_audio_play_icon.png` |
| 问答菜单 UI 10 PNG | `vn/UI/quiz/quiz_menu/quiz_menu_bg_normal_9p.png`, `quiz_menu_bg_hover_9p.png`, `quiz_menu_bg_pressed_9p.png`, `quiz_menu_icon.png`, `menu_popup_panel_9p.png`, `menu_popup_connector.png`, `menu_action_normal_9p.png`, `menu_action_hover_9p.png`, `menu_action_pressed_9p.png`, `menu_action_disabled_9p.png` |
| 文化书 8 PNG | `culture_book/book/open_book.png`; `culture_book/illustrations/dongba/dongba_manuscript.png`; `culture_book/illustrations/music/naxi_instruments.png`, `dongjing_performance.png`, `baisha_performance.png`; `culture_book/illustrations/dance/datiao_together.png`, `datiao_step.png`, `datiao_circle.png` |
| 东巴图像 6 PNG | `dongba/glyphs/dongba_01_person.png`, `dongba_02_mountain.png`, `dongba_03_water.png`, `dongba_04_fire.png`, `dongba_05_sun.png`; `dongba/sentence/dongba_sentence_01.png` |
| 音频 9 OGG + 1 WAV | `dongba/audio/dongba_01_person.ogg`, `dongba_02_mountain.ogg`, `dongba_03_water.ogg`, `dongba_04_fire.ogg`, `dongba_05_sun.ogg`; `dongba/sfx/sfx_correct.ogg`, `sfx_wrong.ogg`; `music/stingers/stinger_win_baisha.ogg`, `stinger_fail_dongjing.ogg`; `_placeholder/silent.wav` |
| 视频 9 OGV | `music/baisha/baisha_01.ogv`, `baisha_02.ogv`; `music/dongjing/dongjing_01.ogv`, `dongjing_02.ogv`, `dongjing_03.ogv`; `dance/datiao/video/datiao_01_full.ogv`, `datiao_01_step_01.ogv`, `datiao_01_step_02.ogv`, `datiao_01_step_03.ogv` |
| 字体 1 TTF + 许可说明 | `fonts/MaShanZheng-Regular.ttf`, `fonts/OFL-MaShanZheng.txt` |

另有项目图标 `icon.svg`（位于工程根目录，不计入上表的 `Assets/` 88 项）。`Assets/` 内五个 `.xmp` 为东巴音频旁车元数据；`project.godot` 中的 SFX/Music bus 名称需在 Web 播放器音量管理中重建。`bg_snow_pasture`、中性/路人肖像、部分云纹 UI、东巴 SFX 等虽未在项目自有源文件中直接引用，仍是原项目资源，迁移清单不能删掉。

## 6. 缺失引用与现状风险

静态扫描项目自有 `.gd/.tscn/.tres/.dtl/.dch/.json/.cfg` 的 `res://` 引用，找到以下**实际缺失目标**：`Assets/culture_book/audio/page_turn.ogg`、`Assets/culture_book/illustrations/test_missing.png`、`Assets/dongba/sentence/dongba_sentence_01.ogg`。第一项由 `CultureBook.gd` 静音回退；第二项属于 `test_book` 的测试占位；第三项在正式东巴句图题引用，读音会回退静音。Web 需明确提示/保留静音，不伪造音频。

原工程的 OGV 不是通用浏览器交付格式；迁移须对**副本**转码并检查音轨、编码与授权，不能修改原 OGV。原 Web 导出 `D:\livingnaxi-web2` 可作迁移行为对照和回归基线，不是本轮原生实现。现有素材文件名、问答文案、读音、音乐类别及打跳口诀均未附权威来源；迁移前后必须以源文件逐项校对，不能用 AI 补文化资料。音乐引导文案与两段提示音文件名的类别指向相反，是明确的人工复核项。

## 7. Web 页面规划与复用边界

`/` 为游戏主导的统一首页，`/chapters` 为章节目录，`/game/:stepId` 承载对话、文化书、问答、舞蹈、完成页和结局，`/studio/dongba|music|dance` 为游戏可跳转且可独立访问的创作入口，`/works` 为作品列表，`/account` 为未来登录入口。每个 15 步 ID、11 场景、6 时间线、2 问答库、3 文化书、3 完成页及 88 项原始资产在迁移表中有对应；实施时用机器生成的资源映射和逐场景回归测试验收。`ResultScreen`/`Core/Game` 和未用 `dongba_intro` 保留“旧/未用”标记，避免把它们误说成现行流程。

## 附录：Dialogic 插件场景和文件全集索引

以下是第三方 `addons/dialogic/` 的逐文件**索引和迁移归属**，避免把插件附带的场景误记成原游戏关卡。插件配置 `plugin.cfg` 标识版本 `2.0-Alpha-19 (Godot 4.4+)`。对话运行时的必要视觉/事件语义映射到 Web `DialogueStage`；编辑器和示例场景不作为玩家页面迁移。**本轮未对插件每个脚本逐行做安全审计，也不承诺完整移植 Dialogic 插件功能**；以下清单用于防遗漏和追溯。

插件含 83 个场景、255 个 GDScript、29 个 `.tres`、151 个原始媒体/字体文件（不计 `.import`、`.uid`）。

### 插件场景逐项映射

| 插件 `.tscn` | Web 归属 |
| --- | --- |
| `addons/dialogic/Editor/CharacterEditor/char_edit_p_section_exports.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/char_edit_p_section_layout.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/char_edit_p_section_main.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/char_edit_p_section_main_exports.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/char_edit_section_general.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/char_edit_section_portraits.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/character_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/character_prefix_suffix.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/CharacterEditor/portrait_scene_browser.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Common/BrowserItem.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Common/hint_tooltip_icon.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Common/reference_manager.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Common/side_bar.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Common/update_install_window.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/editor_main.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/BranchEnd.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/EventBlock/event_block.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/array_part.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/dictionary_part.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_array.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_audio_preview.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_bool_button.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_bool_check.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_color.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_condition.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_dictionary.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_file.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_flex_value.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_image_preview.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_number.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_options_dynamic.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_options_fixed.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_text_multiline.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_text_singleline.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_vector2.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_vector3.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Events/Fields/field_vector4.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/HomePage/home_page.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Settings/CoreSettingsPages/settings_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Settings/CoreSettingsPages/settings_general.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Settings/CoreSettingsPages/settings_modules.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Settings/CoreSettingsPages/settings_translation.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/Settings/settings_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/TimelineEditor/test_timeline_scene.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/TimelineEditor/TextEditor/timeline_editor_text.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/TimelineEditor/timeline_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/TimelineEditor/VisualEditor/AddEventButton.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Editor/TimelineEditor/VisualEditor/timeline_editor_visual.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Example Assets/portraits/CustomPortrait_AnimatedSprite.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Example Assets/portraits/CustomPortrait_FaceAtlas.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Audio/settings_audio.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Background/DefaultBackgroundScene/default_background.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Character/default_portrait.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Character/settings_portraits.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Choice/settings_choices.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Choice/ui_choice_end.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Condition/ui_condition_end.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Base_Default/default_layout_base.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Base_TextBubble/text_bubble_base.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_FullBackground/full_background_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_Glossary/glossary_popup_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_History/example_history_item.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_History/history_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_Input/full_advance_input_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_SpeakerPortraitTextbox/textbox_with_speaker_portrait.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/text_bubble.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/text_bubble_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_TextInput/text_input_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/vn_choice_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Portraits/vn_portrait_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/vn_textbox_layer.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Glossary/glossary_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/HighlightPortrait/simple_highlight_portrait.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/History/settings_history.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/LayeredPortrait/layered_portrait.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Save/settings_save.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Style/character_settings_style.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/StyleEditor/Components/style_browser.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/StyleEditor/style_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Text/character_settings/character_moods_settings.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Text/character_settings/character_portrait_mood_settings.tscn` | 对话运行时语义 → `DialogueStage` 的对应背景/立绘/文本/音频/选择子组件；仅移植原时间线实际使用的能力 |
| `addons/dialogic/Modules/Text/settings_text.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |
| `addons/dialogic/Modules/Variable/variables_editor/variables_editor.tscn` | 编辑器/插件示例；无玩家页面，Web 内容编辑器另行设计 |

<details><summary>插件 GDScript 全集路径（库存，不逐行移植）：255 项</summary>

```text
addons/dialogic/Core/Dialogic_Subsystem.gd
addons/dialogic/Core/DialogicGameHandler.gd
addons/dialogic/Core/DialogicResourceUtil.gd
addons/dialogic/Core/DialogicUtil.gd
addons/dialogic/Core/index_class.gd
addons/dialogic/Editor/CharacterEditor/char_edit_p_section_exports.gd
addons/dialogic/Editor/CharacterEditor/char_edit_p_section_layout.gd
addons/dialogic/Editor/CharacterEditor/char_edit_p_section_main.gd
addons/dialogic/Editor/CharacterEditor/char_edit_p_section_main_exports.gd
addons/dialogic/Editor/CharacterEditor/char_edit_section_general.gd
addons/dialogic/Editor/CharacterEditor/char_edit_section_portraits.gd
addons/dialogic/Editor/CharacterEditor/character_editor.gd
addons/dialogic/Editor/CharacterEditor/character_editor_main_settings_section.gd
addons/dialogic/Editor/CharacterEditor/character_editor_portrait_settings_section.gd
addons/dialogic/Editor/CharacterEditor/character_editor_portrait_tree.gd
addons/dialogic/Editor/CharacterEditor/character_prefix_suffix.gd
addons/dialogic/Editor/CharacterEditor/portrait_scene_browser.gd
addons/dialogic/Editor/Common/broken_reference_manager.gd
addons/dialogic/Editor/Common/BrowserItem.gd
addons/dialogic/Editor/Common/DCSS.gd
addons/dialogic/Editor/Common/hint_tooltip_icon.gd
addons/dialogic/Editor/Common/reference_manager.gd
addons/dialogic/Editor/Common/reference_manager_window.gd
addons/dialogic/Editor/Common/ReferenceManager_AddReplacementPanel.gd
addons/dialogic/Editor/Common/sidebar.gd
addons/dialogic/Editor/Common/sidebar_resource_tree.gd
addons/dialogic/Editor/Common/toolbar.gd
addons/dialogic/Editor/Common/unique_identifiers_manager.gd
addons/dialogic/Editor/Common/update_install_window.gd
addons/dialogic/Editor/Common/update_manager.gd
addons/dialogic/Editor/dialogic_editor.gd
addons/dialogic/Editor/editor_main.gd
addons/dialogic/Editor/editors_manager.gd
addons/dialogic/Editor/Events/BranchEnd.gd
addons/dialogic/Editor/Events/event_field.gd
addons/dialogic/Editor/Events/EventBlock/event_block.gd
addons/dialogic/Editor/Events/EventBlock/event_right_click_menu.gd
addons/dialogic/Editor/Events/Fields/array_part.gd
addons/dialogic/Editor/Events/Fields/dictionary_part.gd
addons/dialogic/Editor/Events/Fields/field_array.gd
addons/dialogic/Editor/Events/Fields/field_audio_preview.gd
addons/dialogic/Editor/Events/Fields/field_bool_button.gd
addons/dialogic/Editor/Events/Fields/field_bool_check.gd
addons/dialogic/Editor/Events/Fields/field_color.gd
addons/dialogic/Editor/Events/Fields/field_condition.gd
addons/dialogic/Editor/Events/Fields/field_dictionary.gd
addons/dialogic/Editor/Events/Fields/field_file.gd
addons/dialogic/Editor/Events/Fields/field_flex_value.gd
addons/dialogic/Editor/Events/Fields/field_image_preview.gd
addons/dialogic/Editor/Events/Fields/field_number.gd
addons/dialogic/Editor/Events/Fields/field_options_dynamic.gd
addons/dialogic/Editor/Events/Fields/field_options_fixed.gd
addons/dialogic/Editor/Events/Fields/field_text_multiline.gd
addons/dialogic/Editor/Events/Fields/field_text_singleline.gd
addons/dialogic/Editor/Events/Fields/field_vector2.gd
addons/dialogic/Editor/Events/Fields/field_vector3.gd
addons/dialogic/Editor/Events/Fields/field_vector4.gd
addons/dialogic/Editor/Events/Fields/field_vector_base.gd
addons/dialogic/Editor/HomePage/home_page.gd
addons/dialogic/Editor/Inspector/inspector_plugin.gd
addons/dialogic/Editor/Inspector/timeline_inspector_field.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/csv_file.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/settings_editor.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/settings_general.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/settings_modules.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/settings_tools.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/settings_translation.gd
addons/dialogic/Editor/Settings/CoreSettingsPages/tool_resave.gd
addons/dialogic/Editor/Settings/HintLabelStylingScript.gd
addons/dialogic/Editor/Settings/settings_editor.gd
addons/dialogic/Editor/Settings/settings_page.gd
addons/dialogic/Editor/TimelineEditor/shortcut_popup.gd
addons/dialogic/Editor/TimelineEditor/test_timeline_scene.gd
addons/dialogic/Editor/TimelineEditor/TextEditor/CodeCompletionHelper.gd
addons/dialogic/Editor/TimelineEditor/TextEditor/syntax_highlighter.gd
addons/dialogic/Editor/TimelineEditor/TextEditor/timeline_editor_text.gd
addons/dialogic/Editor/TimelineEditor/timeline_editor.gd
addons/dialogic/Editor/TimelineEditor/VisualEditor/AddEventButton.gd
addons/dialogic/Editor/TimelineEditor/VisualEditor/timeline_editor_visual.gd
addons/dialogic/Editor/TimelineEditor/VisualEditor/TimelineArea.gd
addons/dialogic/Example Assets/already_read_indicator.gd
addons/dialogic/Example Assets/bbcode_transitions/bbcode_transition_effect.gd
addons/dialogic/Example Assets/default_event.gd
addons/dialogic/Example Assets/portraits/CustomPortrait_AnimatedSprite.gd
addons/dialogic/Example Assets/portraits/CustomPortrait_FaceAtlas.gd
addons/dialogic/Modules/Audio/event_audio.gd
addons/dialogic/Modules/Audio/index.gd
addons/dialogic/Modules/Audio/settings_audio.gd
addons/dialogic/Modules/Audio/subsystem_audio.gd
addons/dialogic/Modules/Background/DefaultBackgroundScene/default_background.gd
addons/dialogic/Modules/Background/dialogic_background.gd
addons/dialogic/Modules/Background/event_background.gd
addons/dialogic/Modules/Background/index.gd
addons/dialogic/Modules/Background/node_background_holder.gd
addons/dialogic/Modules/Background/subsystem_backgrounds.gd
addons/dialogic/Modules/Background/Transitions/class_dialogic_background_transition.gd
addons/dialogic/Modules/Background/Transitions/Defaults/push_down.gd
addons/dialogic/Modules/Background/Transitions/Defaults/push_left.gd
addons/dialogic/Modules/Background/Transitions/Defaults/push_right.gd
addons/dialogic/Modules/Background/Transitions/Defaults/push_up.gd
addons/dialogic/Modules/Background/Transitions/Defaults/simple_fade.gd
addons/dialogic/Modules/Background/Transitions/Defaults/swipe_diagonal_up_left.gd
addons/dialogic/Modules/Background/Transitions/Defaults/swipe_left_to_right.gd
addons/dialogic/Modules/Background/Transitions/Defaults/swipe_right_to_left.gd
addons/dialogic/Modules/Background/Transitions/simple_push_transitions.gd
addons/dialogic/Modules/Background/Transitions/simple_swipe_transitions.gd
addons/dialogic/Modules/Call/event_call.gd
addons/dialogic/Modules/Call/index.gd
addons/dialogic/Modules/Character/class_dialogic_animation.gd
addons/dialogic/Modules/Character/default_portrait.gd
addons/dialogic/Modules/Character/DefaultAnimations/bounce.gd
addons/dialogic/Modules/Character/DefaultAnimations/bounce_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/fade_down_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/fade_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/fade_up_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/heartbeat.gd
addons/dialogic/Modules/Character/DefaultAnimations/instant_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/shake_x.gd
addons/dialogic/Modules/Character/DefaultAnimations/shake_y.gd
addons/dialogic/Modules/Character/DefaultAnimations/slide_down_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/slide_left_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/slide_right_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/slide_up_in.gd
addons/dialogic/Modules/Character/DefaultAnimations/tada.gd
addons/dialogic/Modules/Character/DefaultAnimations/zoom_center_in_out.gd
addons/dialogic/Modules/Character/DefaultAnimations/zoom_in_out.gd
addons/dialogic/Modules/Character/dialogic_portrait.gd
addons/dialogic/Modules/Character/DialogicPortraitAnimationsUtil.gd
addons/dialogic/Modules/Character/event_character.gd
addons/dialogic/Modules/Character/index.gd
addons/dialogic/Modules/Character/node_portrait_container.gd
addons/dialogic/Modules/Character/settings_portraits.gd
addons/dialogic/Modules/Character/subsystem_containers.gd
addons/dialogic/Modules/Character/subsystem_portraits.gd
addons/dialogic/Modules/Choice/event_choice.gd
addons/dialogic/Modules/Choice/index.gd
addons/dialogic/Modules/Choice/node_button_sound.gd
addons/dialogic/Modules/Choice/node_choice_button.gd
addons/dialogic/Modules/Choice/settings_choices.gd
addons/dialogic/Modules/Choice/subsystem_choices.gd
addons/dialogic/Modules/Choice/ui_choice_end.gd
addons/dialogic/Modules/Clear/event_clear.gd
addons/dialogic/Modules/Clear/index.gd
addons/dialogic/Modules/Comment/event_comment.gd
addons/dialogic/Modules/Comment/index.gd
addons/dialogic/Modules/Condition/event_condition.gd
addons/dialogic/Modules/Condition/index.gd
addons/dialogic/Modules/Condition/ui_condition_end.gd
addons/dialogic/Modules/Core/event_end_branch.gd
addons/dialogic/Modules/Core/index.gd
addons/dialogic/Modules/Core/subsystem_animation.gd
addons/dialogic/Modules/Core/subsystem_expression.gd
addons/dialogic/Modules/Core/subsystem_input.gd
addons/dialogic/Modules/DefaultLayoutParts/Base_Default/default_layout_base.gd
addons/dialogic/Modules/DefaultLayoutParts/Base_TextBubble/text_bubble_base.gd
addons/dialogic/Modules/DefaultLayoutParts/index.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_FullBackground/full_background_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_Glossary/glossary_popup_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_History/example_history_item.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_History/history_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_Input/full_advance_input_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_SpeakerPortraitTextbox/speaker_portrait_textbox_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/text_bubble.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/text_bubble_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_TextInput/text_input_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/vn_choice_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Portraits/vn_portrait_layer.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/animations.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/autoadvance_indicator.gd
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/vn_textbox_layer.gd
addons/dialogic/Modules/End/event_end.gd
addons/dialogic/Modules/End/index.gd
addons/dialogic/Modules/Glossary/event_glossary.gd
addons/dialogic/Modules/Glossary/glossary_editor.gd
addons/dialogic/Modules/Glossary/glossary_resource.gd
addons/dialogic/Modules/Glossary/index.gd
addons/dialogic/Modules/Glossary/subsystem_glossary.gd
addons/dialogic/Modules/HighlightPortrait/index.gd
addons/dialogic/Modules/HighlightPortrait/simple_highlight_portrait.gd
addons/dialogic/Modules/History/event_history.gd
addons/dialogic/Modules/History/index.gd
addons/dialogic/Modules/History/settings_history.gd
addons/dialogic/Modules/History/subsystem_history.gd
addons/dialogic/Modules/Jump/event_jump.gd
addons/dialogic/Modules/Jump/event_label.gd
addons/dialogic/Modules/Jump/event_return.gd
addons/dialogic/Modules/Jump/index.gd
addons/dialogic/Modules/Jump/subsystem_jump.gd
addons/dialogic/Modules/LayeredPortrait/custom_layered_portrait.gd
addons/dialogic/Modules/LayeredPortrait/index.gd
addons/dialogic/Modules/LayeredPortrait/layered_portrait.gd
addons/dialogic/Modules/Save/event_save.gd
addons/dialogic/Modules/Save/index.gd
addons/dialogic/Modules/Save/settings_save.gd
addons/dialogic/Modules/Save/subsystem_save.gd
addons/dialogic/Modules/Settings/event_setting.gd
addons/dialogic/Modules/Settings/index.gd
addons/dialogic/Modules/Settings/subsystem_settings.gd
addons/dialogic/Modules/Signal/event_signal.gd
addons/dialogic/Modules/Signal/index.gd
addons/dialogic/Modules/Style/character_settings_style.gd
addons/dialogic/Modules/Style/DialogicStylesUtil.gd
addons/dialogic/Modules/Style/event_style.gd
addons/dialogic/Modules/Style/index.gd
addons/dialogic/Modules/Style/node_style.gd
addons/dialogic/Modules/Style/subsystem_styles.gd
addons/dialogic/Modules/StyleEditor/Components/style_browser.gd
addons/dialogic/Modules/StyleEditor/Components/style_browser_window.gd
addons/dialogic/Modules/StyleEditor/Components/style_layer_tree.gd
addons/dialogic/Modules/StyleEditor/index.gd
addons/dialogic/Modules/StyleEditor/style_editor.gd
addons/dialogic/Modules/StyleEditor/style_layer_editor.gd
addons/dialogic/Modules/Text/auto_advance.gd
addons/dialogic/Modules/Text/auto_skip.gd
addons/dialogic/Modules/Text/character_settings/character_moods_settings.gd
addons/dialogic/Modules/Text/character_settings/character_portrait_mood_settings.gd
addons/dialogic/Modules/Text/event_text.gd
addons/dialogic/Modules/Text/index.gd
addons/dialogic/Modules/Text/manual_advance.gd
addons/dialogic/Modules/Text/node_dialog_text.gd
addons/dialogic/Modules/Text/node_input.gd
addons/dialogic/Modules/Text/node_name_label.gd
addons/dialogic/Modules/Text/node_next_indicator.gd
addons/dialogic/Modules/Text/node_type_sound.gd
addons/dialogic/Modules/Text/settings_text.gd
addons/dialogic/Modules/Text/subsystem_text.gd
addons/dialogic/Modules/TextInput/event_text_input.gd
addons/dialogic/Modules/TextInput/index.gd
addons/dialogic/Modules/TextInput/node_text_input.gd
addons/dialogic/Modules/TextInput/subsystem_text_input.gd
addons/dialogic/Modules/Variable/event_variable.gd
addons/dialogic/Modules/Variable/index.gd
addons/dialogic/Modules/Variable/subsystem_variables.gd
addons/dialogic/Modules/Variable/variables_editor/variable_tree.gd
addons/dialogic/Modules/Variable/variables_editor/variables_editor.gd
addons/dialogic/Modules/Voice/event_voice.gd
addons/dialogic/Modules/Voice/index.gd
addons/dialogic/Modules/Voice/subsystem_voice.gd
addons/dialogic/Modules/Wait/event_wait.gd
addons/dialogic/Modules/Wait/index.gd
addons/dialogic/Modules/WaitInput/event_wait_input.gd
addons/dialogic/Modules/WaitInput/index.gd
addons/dialogic/plugin.gd
addons/dialogic/Resources/character.gd
addons/dialogic/Resources/CharacterResourceLoader.gd
addons/dialogic/Resources/CharacterResourceSaver.gd
addons/dialogic/Resources/dialogic_identifiable_resource.gd
addons/dialogic/Resources/dialogic_layout_base.gd
addons/dialogic/Resources/dialogic_layout_layer.gd
addons/dialogic/Resources/dialogic_style.gd
addons/dialogic/Resources/dialogic_style_layer.gd
addons/dialogic/Resources/event.gd
addons/dialogic/Resources/timeline.gd
addons/dialogic/Resources/TimelineResourceLoader.gd
addons/dialogic/Resources/TimelineResourceSaver.gd
```

</details>

<details><summary>插件 `.tres` 全集路径（Godot 专用资源）：29 项</summary>

```text
addons/dialogic/Editor/Common/TitleBgStylebox.tres
addons/dialogic/Editor/Events/styles/InputFieldsStyle.tres
addons/dialogic/Editor/Events/styles/ResourceMenuHover.tres
addons/dialogic/Editor/Events/styles/ResourceMenuNormal.tres
addons/dialogic/Editor/Events/styles/ResourceMenuPanelBackground.tres
addons/dialogic/Editor/Events/styles/SectionPanel.tres
addons/dialogic/Editor/Events/styles/selected_styleboxflat.tres
addons/dialogic/Editor/Events/styles/SimpleButtonHover.tres
addons/dialogic/Editor/Events/styles/SimpleButtonNormal.tres
addons/dialogic/Editor/Events/styles/TextBackground.tres
addons/dialogic/Editor/Events/styles/unselected_stylebox.tres
addons/dialogic/Editor/Theme/MainTheme.tres
addons/dialogic/Editor/Theme/PickerTheme.tres
addons/dialogic/Example Assets/bbcode_transitions/fade_in.tres
addons/dialogic/Example Assets/bbcode_transitions/fade_scale_in.tres
addons/dialogic/Example Assets/bbcode_transitions/fancy_in.tres
addons/dialogic/Example Assets/bbcode_transitions/shaky_in.tres
addons/dialogic/Modules/Background/Transitions/Defaults/simple_fade.tres
addons/dialogic/Modules/Background/Transitions/simple_swipe_gradient.tres
addons/dialogic/Modules/Character/preview_character.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_SpeakerPortraitTextbox/default_stylebox.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/choice_panel_focus.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/choice_panel_hover.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/choice_panel_normal.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/vn_textbox_default_panel.tres
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/vn_textbox_name_label_panel.tres
addons/dialogic/Modules/DefaultLayoutParts/Style_SpeakerTextbox/speaker_textbox_style.tres
addons/dialogic/Modules/DefaultLayoutParts/Style_TextBubbles/textbubble_style.tres
addons/dialogic/Modules/DefaultLayoutParts/Style_VN_Default/default_vn_style.tres
```

</details>

<details><summary>插件原始媒体/字体路径（编辑器/运行时依赖，非原游戏新增关卡）：151 项</summary>

```text
addons/dialogic/Editor/HomePage/icon_bg.png
addons/dialogic/Editor/Images/dialogic-logo.svg
addons/dialogic/Editor/Images/Dropdown/default.svg
addons/dialogic/Editor/Images/Dropdown/divide.svg
addons/dialogic/Editor/Images/Dropdown/join.svg
addons/dialogic/Editor/Images/Dropdown/leave.svg
addons/dialogic/Editor/Images/Dropdown/minus.svg
addons/dialogic/Editor/Images/Dropdown/multiply.svg
addons/dialogic/Editor/Images/Dropdown/plus.svg
addons/dialogic/Editor/Images/Dropdown/set.svg
addons/dialogic/Editor/Images/Dropdown/update.svg
addons/dialogic/Editor/Images/Interactable/decrement_icon.svg
addons/dialogic/Editor/Images/Interactable/increment_icon.svg
addons/dialogic/Editor/Images/Pieces/add-folder.svg
addons/dialogic/Editor/Images/Pieces/close-icon.svg
addons/dialogic/Editor/Images/Pieces/closed-icon.svg
addons/dialogic/Editor/Images/Pieces/expand-icon.svg
addons/dialogic/Editor/Images/Pieces/open-icon.svg
addons/dialogic/Editor/Images/Pieces/variable.svg
addons/dialogic/Editor/Images/Pieces/variable_icon.png
addons/dialogic/Editor/Images/Pieces/warning.svg
addons/dialogic/Editor/Images/plugin-icon.svg
addons/dialogic/Editor/Images/preview_character.png
addons/dialogic/Editor/Images/preview_character_speaker.png
addons/dialogic/Editor/Images/Resources/character.svg
addons/dialogic/Editor/Images/Resources/icon_character.png
addons/dialogic/Editor/Images/Resources/portrait.svg
addons/dialogic/Editor/Images/Resources/timeline.svg
addons/dialogic/Editor/Images/Toolbar/add-character.svg
addons/dialogic/Editor/Images/Toolbar/add-timeline.svg
addons/dialogic/Editor/Images/Unknown.png
addons/dialogic/Example Assets/backgrounds/BubbleEnd.png
addons/dialogic/Example Assets/backgrounds/rpg_box.webp
addons/dialogic/Example Assets/Fonts/Roboto-Bold.ttf
addons/dialogic/Example Assets/Fonts/Roboto-Italic.ttf
addons/dialogic/Example Assets/Fonts/Roboto-Regular.ttf
addons/dialogic/Example Assets/next-indicator/next-indicator-dialogic-1.png
addons/dialogic/Example Assets/next-indicator/next-indicator.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 blink.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 doubt.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 hate.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 plot.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 sad.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 scoff.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 shy.png
addons/dialogic/Example Assets/portraits/Antonio/pl5 surprise.png
addons/dialogic/Example Assets/portraits/Antonio/pl5.png
addons/dialogic/Example Assets/portraits/Jane/pl3 avoid.png
addons/dialogic/Example Assets/portraits/Jane/pl3 blink.png
addons/dialogic/Example Assets/portraits/Jane/pl3 concept.png
addons/dialogic/Example Assets/portraits/Jane/pl3 confusion.png
addons/dialogic/Example Assets/portraits/Jane/pl3 doubt.png
addons/dialogic/Example Assets/portraits/Jane/pl3 happy.png
addons/dialogic/Example Assets/portraits/Jane/pl3 plot.png
addons/dialogic/Example Assets/portraits/Jane/pl3 sad.png
addons/dialogic/Example Assets/portraits/Jane/pl3 shy.png
addons/dialogic/Example Assets/portraits/Jane/pl3 surprise.png
addons/dialogic/Example Assets/portraits/Portrait1.png
addons/dialogic/Example Assets/portraits/Portrait2.png
addons/dialogic/Example Assets/portraits/Princess/anger.png
addons/dialogic/Example Assets/portraits/Princess/frown.png
addons/dialogic/Example Assets/portraits/Princess/joy.png
addons/dialogic/Example Assets/portraits/Princess/neutral.png
addons/dialogic/Example Assets/portraits/Princess/princess_blank.png
addons/dialogic/Example Assets/portraits/Princess/shock.png
addons/dialogic/Example Assets/portraits/Princess/smile.png
addons/dialogic/Example Assets/portraits/rpg_portraits/base1.png
addons/dialogic/Example Assets/portraits/rpg_portraits/base2.png
addons/dialogic/Example Assets/portraits/rpg_portraits/base3.png
addons/dialogic/Example Assets/portraits/rpg_portraits/base4.png
addons/dialogic/Example Assets/sound-effects/typing1.wav
addons/dialogic/Example Assets/sound-effects/typing2.wav
addons/dialogic/Example Assets/sound-effects/typing3.wav
addons/dialogic/Example Assets/sound-effects/typing4.wav
addons/dialogic/Example Assets/sound-effects/typing5.wav
addons/dialogic/Modules/Audio/icon_music.png
addons/dialogic/Modules/Audio/icon_sound.png
addons/dialogic/Modules/Background/icon.png
addons/dialogic/Modules/Call/icon.png
addons/dialogic/Modules/Character/custom_portrait_thumbnail.png
addons/dialogic/Modules/Character/default_portrait_thumbnail.png
addons/dialogic/Modules/Character/icon.svg
addons/dialogic/Modules/Character/icon_position.png
addons/dialogic/Modules/Character/portrait_position.svg
addons/dialogic/Modules/Character/simple_image_portrait_thumbnail.png
addons/dialogic/Modules/Character/update_mirror.svg
addons/dialogic/Modules/Character/update_portrait.svg
addons/dialogic/Modules/Character/update_position.svg
addons/dialogic/Modules/Character/update_position.svg.2023_09_23_08_37_47.0.svg
addons/dialogic/Modules/Character/update_z_index.svg
addons/dialogic/Modules/Choice/icon.svg
addons/dialogic/Modules/Clear/clear_background.svg
addons/dialogic/Modules/Clear/clear_characters.svg
addons/dialogic/Modules/Clear/clear_music.svg
addons/dialogic/Modules/Clear/clear_positions.svg
addons/dialogic/Modules/Clear/clear_style.svg
addons/dialogic/Modules/Clear/clear_textbox.svg
addons/dialogic/Modules/Clear/icon.png
addons/dialogic/Modules/Comment/icon.png
addons/dialogic/Modules/Condition/icon.svg
addons/dialogic/Modules/Core/icon.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_FullBackground/background_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_FullBackground/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_Glossary/popup_glossary_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_Glossary/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_History/history_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_History/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_Input/input_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_Input/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_SpeakerPortraitTextbox/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_SpeakerPortraitTextbox/speaker-textbox-icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_Textbubble/text_bubble_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_TextInput/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_TextInput/text_input_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/choices_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Choices/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Portraits/portrait_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Portraits/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/next.svg
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Layer_VN_Textbox/textbox_layer_icon.svg
addons/dialogic/Modules/DefaultLayoutParts/Style_SpeakerTextbox/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Style_TextBubbles/preview.png
addons/dialogic/Modules/DefaultLayoutParts/Style_VN_Default/preview.png
addons/dialogic/Modules/End/icon.png
addons/dialogic/Modules/Glossary/add-glossary.svg
addons/dialogic/Modules/Glossary/icon.svg
addons/dialogic/Modules/HighlightPortrait/highlight_portrait_thumbnail.png
addons/dialogic/Modules/History/definition.svg
addons/dialogic/Modules/History/icon.svg
addons/dialogic/Modules/Jump/icon_jump.png
addons/dialogic/Modules/Jump/icon_label.png
addons/dialogic/Modules/Jump/icon_return.svg
addons/dialogic/Modules/LayeredPortrait/layered_portrait_thumbnail.png
addons/dialogic/Modules/Save/icon.svg
addons/dialogic/Modules/Settings/icon.svg
addons/dialogic/Modules/Signal/icon.png
addons/dialogic/Modules/Style/icon.png
addons/dialogic/Modules/StyleEditor/styles_icon.svg
addons/dialogic/Modules/Text/icon.svg
addons/dialogic/Modules/Text/node_dialog_text_icon.svg
addons/dialogic/Modules/Text/node_name_label_icon.svg
addons/dialogic/Modules/Text/node_next_indicator_icon.svg
addons/dialogic/Modules/TextInput/icon.png
addons/dialogic/Modules/Variable/add-variable.svg
addons/dialogic/Modules/Variable/icon.png
addons/dialogic/Modules/Variable/variable.svg
addons/dialogic/Modules/Voice/icon.png
addons/dialogic/Modules/Wait/icon.svg
addons/dialogic/Modules/WaitInput/icon.svg
```

</details>
