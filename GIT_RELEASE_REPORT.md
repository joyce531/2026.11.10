# Naxi AI Studio Git 发布审查报告

审查日期：2026-11-10。此次只整理并提交已能安全判断的源码、结构化目录和文档；未删除、移动或覆盖任何本地素材。发布状态见文末补充记录。

## 状态与提交

- 初始 `git status --porcelain=v1 -uall`：**377 项**（376 个未跟踪文件、1 个已跟踪文件修改），无已暂存项、合并冲突或进行中的合并/变基。初始仅 `.gitignore` 和 `AGENTS.md` 已被跟踪；分支为 `master`。
- 新增的忽略规则排除了初始未跟踪候选中的 **183 个文件**；另有原本就被忽略的 `.env`、虚拟环境等，不计入这 183 项。
- 本轮三个 Commit 共涉及 **195 个文件**（其中 `.gitignore` 是本轮新增修改项，`AGENTS.md` 为原有修改）；总计 18,481 行新增、41 行删除。此统计是 Git 变更文件数，不把忽略目录内数千个构建依赖算作候选。

| 顺序 | Commit ID | 文件数 | 内容 |
| --- | --- | ---: | --- |
| 1 | `7ed9872b9b515653bcd4460f2f5a0cd5888cd572` | 76 | Python Agent/服务、Web API、数据 schema/目录、测试、配置、`.gitignore` |
| 2 | `cf03a7ec1da94d6008687d78683d4a7c462468ee` | 39 | React + TypeScript 游戏及 Agent 入口、存档、前端测试和构建配置 |
| 3 | `3d77b25cd63ee6bb3621e3b6127561410d393ca6` | 80 | 核心说明书、里程碑报告、HTML 展示站源码与 SVG 图表 |

最初三个功能提交后、生成本报告前，`git status --short` 为空。报告中的前三个 Commit ID 均为本地实际提交。

## 排除清单与原因

以下路径由 `.gitignore` 或已有的嵌套忽略规则排除，原文件全部留在原位。按初始候选与提交清单的差额，新增排除 **183 个文件**。同一目录下各素材的授权状态并未逐一获得书面核实，故整体按“待确认”处理，不因项目运行需要而自动公开发布。

| 排除路径或模式 | 原因 |
| --- | --- |
| `.env`、`.env.*`（保留 `.env.example`）、`.streamlit/secrets.toml`、`*.db`、`*.sqlite3` | 密钥/本地运行数据；尤其 `data/music/music_library.sqlite3` 虽无检出的邮箱、手机号或密钥，但 13 条素材记录含 39 处本机绝对路径，不能作为可复现的公开索引 |
| `data/dance/dance_portrait_of_me/`、`web/public/uploads/`、`uploads/`、`data/handwriting_samples/images/`、`data/handwriting_samples/strokes/` | 个人肖像、玩家上传内容或可能的个人书写记录 |
| `data/dance/dance_videos/`、`data/dance/dance_music/`、`data/dance/dance_outfits/*.jpg`、`data/dance/dance_backgrounds/` | 舞蹈、服饰、背景、音乐素材的公开传播授权和人物肖像授权未核实；服饰文件夹内的说明文字仍可提交 |
| `data/music/ensemble/`、`data/music/instruments/`、`data/music/videos/`、`data/music/曲谱/` | 录音、题目视频和曲谱可能受版权约束；保留安全的文字目录与 manifest |
| `data/glyphs/original/*.png`、`data/glyphs/original/*.import` | 标准字形图片来源与公开许可仍待确认；CSV/JSON 索引和空目录标识已提交 |
| `web/public/game_media/`、`web/public/godot/Assets/` | 从游戏迁出的图片、视频、音频、字体等公开再分发权未核实；前端代码及内容映射已提交 |
| `presentation/naxi-html/assets/references/`、`presentation/naxi-html/assets/game/`、`presentation/naxi-html/assets/evidence/*.png`、`*.jpg` | 参考背景、游戏图片与截图的公开权利/隐私待确认；HTML、CSS、JS、SVG、研究文本仍提交 |
| `docs/milestone6_design/`（含 `style-explorer.html`）、`.oil-ui/`、`html制作/` | 设计探索/本地工具工作区/原始 PPT 参考资料，不是正式运行依赖；可能含未审查的素材 |
| `.venv/`、`web/node_modules/`、`web/dist/`、`dist/`、`build/`、`.vite/`、`*.log`、缓存 | 可再生成的环境、依赖、构建产物和日志 |

未忽略整个 `data/` 或 `web/public/`。排除的音视频和图片会使全新克隆仓库缺少媒体内容；须在取得相应公开授权后，按现有相对目录补充素材并重建本机音乐索引。**前端可构建不等于相关视频或音频在克隆环境已可播放。** README 已补充此限制。

## 安全检查

- `.env.example` 中 API Key 等敏感变量为空，非敏感开关只有示例值；`.env` 已忽略，本轮未读取或输出真实密钥。
- 对拟提交文本执行了本地高置信度密钥模式扫描，未发现 OpenAI/GitHub/阿里云密钥或私钥正文；历史文件名检查未发现 `.env`、`secrets.toml`、私钥文件进入现有 Git 历史。模式扫描不能代替完整人工安全审计。
- 暂存区每组都以明确文件路径加入，检查过 `git diff --cached --check`，并检查暂存文件名无图片、视频、SQLite 或密钥文件。未使用 `git add .`、`reset --hard`、`clean` 或强制推送。
- `git check-ignore` 已确认个人照片目录、`.env`、音乐 SQLite、设计探索页及 `web/dist/` 仍被排除。

## 测试与限制

| 检查 | 结果 |
| --- | --- |
| Python `compileall`（相关模块） | 通过 |
| `python -m unittest discover -s tests -p "test_*.py"` | **75/75 通过** |
| Web Vitest | **11/11 通过**；更新了三条旧游戏流程测试，使其符合现有 Agent 登录跳转行为，未修改游戏业务逻辑 |
| Web TypeScript `tsc -b`、Vite 生产构建 | 通过，生成文件仅留在忽略的 `web/dist/` |
| `python -m unittest discover -s web/tools -p "test_*.py"` | 首次运行 **18 项中 11 通过，2 失败、5 错误**。修正旧测试夹具后重跑，**18/18 通过**；未修改业务代码，未调用付费 API |
| `python -m pytest` | 当前虚拟环境未安装 pytest；项目已有的 unittest 已运行，无额外安装 |

后端 Web API 原有的 7 处不通过分别来自旧测试仍假定可免登录调用 Agent、把旧服饰选项写死、以及生产来源测试漏传精确 Host 白名单。现已用临时账号、临时素材和显式 Host 配置更新离线测试，18 项全通过；修改仅限 `web/tools/test_agent_runtime.py` 和 `web/tools/test_accounts.py`。由于原始媒体未公开提交，GitHub 克隆环境仍需合法素材才能完成端到端媒体验收。

## GitHub 状态与待处理事项

- 当前 `origin`：`https://github.com/joyce531/2026.11.10.git`，为**公开空仓库**，GitHub 报告默认分支名 `main`，但分支列表为空。本地工作分支为 `master`。仓库所有者已在后续消息明确确认该仓库和当前分支为发布目标。
- 当前环境的 `git ls-remote` 无法连接 `github.com:443`；GitHub 连接器只用于只读确认仓库/分支，没有拿它重造与本地 SHA 不同的提交。没有修改 Remote、重置本地历史或强推。
- 仍需确认哪些文化/游戏素材拥有公开分发许可；合法补齐后才能进行完整媒体端到端验收。
