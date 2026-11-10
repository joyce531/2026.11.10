# Milestone 7：三大 Agent Web 接入

日期：2026-11-09。保留原 Godot、游戏页面、Streamlit、既有 Python Agent 和 `.env`；未调用 Qwen、OpenAI 或 Wan 的真实生成接口，未提交 Git。

## 接入结果

| Web 入口 | 本地 API | 实际复用的服务 | 当前状态 |
| --- | --- | --- | --- |
| `/agent/dongba` | `POST /api/agents/dongba/evaluate` | `DongbaHandwritingAgent`、现有字形库、图片质量检查与双图视觉评价；`USE_REAL_AI=true` 才走真实视觉服务 | 真实调用路径已接通；真实返回尚待页面手动验收。Mock/质量拦截均独立标记 |
| `/agent/music` | `POST /api/agents/music/recognize`、`/review`、`/arrange` | 现有 MIDI/MusicXML 解析、OpenCV 预处理、Qwen 视觉识谱、人工校对门、`MusicArrangementAgent` 与本地 MIDI/WAV 合成 | 实际 WAV/MIDI 产出链路离线验证；Qwen 图片识谱及文本规划尚待手动验收 |
| `/agent/dance` | `POST /api/agents/dance/jobs`、`GET .../{task_id}`、`GET .../{task_id}/result` | `services/dance_service.py` 的 Wan 2.7 VideoEdit 上传、异步创建、查询与结果下载 | 异步接口接线及幂等流程离线验证；真实 Wan 任务尚未提交 |

三个入口都在现有首页下方的 Agent 区和统一导航中。东巴文可画布临摹或上传照片；音乐可上传 MIDI/MusicXML/印刷曲谱图、校对不确定音符并生成本地 WAV/MIDI；舞蹈可上传本人视频和照片、选择现有服饰与背景、明确同意后创建异步任务。任务状态查询不会再创建任务。`/works` 显示本机任务及实际保存的 WAV、MIDI、生成 MP4 的试听/播放和下载地址。数据库仅存任务元数据与结果说明，媒体保存在本机 `%LOCALAPPDATA%\NaxiAIStudio\web\artifacts`，用户原始上传不自动留存。

本地 API 继续沿用 `web/tools/mock_api.py`，只监听 `127.0.0.1:8765`，Vite `/api` 代理到它。新增 `agent_runtime.py` 负责调用边界、SQLite 任务记录和幂等键。密钥只由现有 Python 服务在服务端读取；浏览器不接触 `.env`。每次提交带独立任务键；重复请求返回原任务。Wan 创建响应不明确时保留任务键，不自动重试。服务端仅接受本机来源的 JSON 写入，媒体下载支持 HTTP Range。

## 模型与配置

当前 `.env` 检查结果（未输出密钥）：`USE_REAL_AI=true`，`DASHSCOPE_API_KEY` 已配置，`QWEN_VISION_MODEL=qwen3.8-flash`，`QWEN_TEXT_MODEL=auto-model-9e5f7930`；`OPENAI_API_KEY` 未配置。东巴文和图片识谱调用现有 Qwen 视觉配置；音乐规划调用现有 Qwen 文本智能路由；舞蹈服务使用现有北京百炼配置和代码中的 `wan2.7-videoedit`。未验证这些模型在当前账户的实时权限、额度或结果质量，也未更改模型 ID。东巴文在视觉服务失败时会明确回退 `source=mock`；音乐规划失败则明确标记 `mode=local_rules`；Wan 失败不伪造生成视频。

## 离线验证

- `python -m unittest web.tools.test_agent_runtime web.tools.test_mock_api -v`：8 项通过。覆盖东巴幂等与来源、MIDI 解析、图片识谱到人工校对路由、音乐作品保存、Wan 创建/轮询/下载替身、HTTP 路由与 Range，以及原 Mock 回归。
- 现有音乐引擎用合成测试 MIDI、`real=False` 真正输出了非空 MIDI（78 字节）与 WAV（22,094 字节）；没有模型费用。
- 现有音乐素材库可读，舞蹈服饰 4 张、背景 6 张可枚举。
- 受影响 Python 文件语法检查通过；`npm.cmd run build` 通过。
- 未进行真实 Qwen/Wan 调用、真实媒体上传、浏览器逐项人工操作或远程部署验收。

## 本地启动与首次验收

在项目根目录打开终端一：

```powershell
.\.venv\Scripts\python.exe web\tools\mock_api.py
```

终端二：

```powershell
cd web
npm.cmd run dev
```

打开 `http://127.0.0.1:5173/`，向下进入三个 Agent。先用一张有权使用的清晰目标字临摹图验收东巴文，看结果来源是否为 `qwen_vision`；再用有权使用的清晰印刷曲谱验收识谱、校对和 WAV 下载；最后仅在确认视频额度及本人媒体授权后，提交一段符合现有 2–10 秒限制的个人 MP4 与本人照片，选择服饰/背景并创建一次 Wan 任务，按“查询任务状态”直至成功。真实请求由平台所有者承担费用。失败时查看页面明确错误与来源，不重复点击创建任务。

## 尚存限制

这是单机演示 API 与本机 SQLite；没有多用户身份隔离、线上反向代理或云端作品库，不能直接作为公网服务部署。现有服饰参考仍是带文字截图，来源与授权待核实；Wan 对身份、服饰与动作的一致性须真人验收。曲谱识别质量依赖印刷清晰度、调号和人工校对；MIDI/WAV 是现有采样和本地合成，不代表经专家验证的传统曲风。生产部署前还需用户隔离、持久任务恢复与服务端授权。

## 文件

新增：`web/tools/agent_runtime.py`、`web/tools/test_agent_runtime.py`、`web/src/agents/api.ts`、`MusicAgentPanel.tsx`、`DanceAgentPanel.tsx`、`WorksPanel.tsx`、`agents.css`、本报告。

修改：`web/tools/mock_api.py`、`web/src/MockDongbaPanel.tsx`、`web/src/main.tsx`。旧游戏文件、Python Agent 服务、`.env` 和 Godot 原工程未修改。

## 2026-11-09：本地 Vite 端口变化导致东巴文提交被拒

**根因。** Web 东巴文组件以 `POST /api/agents/dongba/evaluate` 发送 `Content-Type: application/json`；Vite 将 `/api` 代理到 `http://127.0.0.1:8765`。旧后端同时检查来源与 JSON 格式，但来源白名单仅列 5173、8765。当前浏览器页面在 5174 时，合法 `Origin: http://127.0.0.1:5174` 被拒绝，触发原来的“仅允许本机站点提交 JSON 请求。”403；请求尚未进入 Agent，因此该错误与 Qwen 配置无关。原实现不检查 `Referer`，也不设置 CORS 通配头。

**修复。** 仅修改 `web/tools/mock_api.py` 的来源判断：本地开发模式接受 `http://127.0.0.1:<本机端口>` 和 `http://localhost:<本机端口>` 的 Origin/Referer，Host 仍须为本机地址；外部主机、外部 Origin/Referer 和非 JSON POST 继续拒绝。来源错误返回 403，媒体类型错误单独返回 415。生产模式须设置 `NAXI_API_ENV=production` 与精确的 `NAXI_WEB_ALLOWED_ORIGINS`（逗号分隔），缺少白名单或 Origin 时默认拒绝；没有添加 `Access-Control-Allow-Origin: *`。生产部署仍应通过同源反向代理，并增加账户授权。

**定向验收。** 离线 HTTP 测试分别以 5173、5174 的 `127.0.0.1` Origin 和 5174 的 `localhost` Origin 提交东巴文 JSON，请求均到达替身服务并返回 200；外部 Origin/Referer 返回 403，非 JSON 返回 415；生产精确白名单、假冒子域和缺失 Origin 的规则也已测试。真实 Qwen/Wan 均未调用。改动文件仅 `web/tools/mock_api.py`、`web/tools/test_agent_runtime.py` 和本报告。

**明确端口启动。** 在项目根目录启动后端：`.\.venv\Scripts\python.exe web\tools\mock_api.py`（后端固定 `127.0.0.1:8765`）。另开终端进入 `web` 后运行 `npm.cmd run dev -- --host 127.0.0.1 --port 5174 --strictPort`，浏览器打开 `http://127.0.0.1:5174/agent/dongba`。若沿用默认 `npm.cmd run dev`，以 Vite 终端显示的实际端口为准；5173 被占用时可切至 5174。修改后需重启 Python 后端进程才能加载新校验逻辑。
