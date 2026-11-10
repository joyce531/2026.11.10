# Milestone 8：评委账号、权限与 AI 费用控制

本轮沿用 `web/tools/mock_api.py` 的单一 Python API 和现有三项 Agent 服务，未改动 Godot、游戏章节、`.env` 或模型配置；未调用 Qwen/Wan，未提交 Git。

## 已实现

- 游客仍可浏览和游玩。`/login` 使用用户名、密码；登录后返回原页面，导航显示身份并可退出。`/admin` 只向管理员开放，所有管理路由同时在服务端验权。没有公开注册。
- 密码用随机盐 `scrypt`（32 MiB 内存参数）哈希；数据库只存随机会话 Token 的 SHA-256 哈希。会话有效期 8 小时，禁用、重置密码或撤销会话会立即使旧会话失效。生产 Cookie 为 `HttpOnly; Secure; SameSite`；状态修改需要 CSRF Token。登录失败按 IP 和账号在 15 分钟窗口限 5 次。
- 管理员可创建评委、查看一次性随机初始密码、重置密码、启用/禁用、设置到期时间、撤销会话、软删除；保留历史作品和审计记录。
- 东巴文真实模型请求默认每账号每天 10 次，古乐外部模型请求默认 3 次；管理员可调全局和个人额度。额度以 UTC 日计算并在 SQLite 事务内预留，避免并发超额。本地规则、MIDI/WAV 合成和明确的 Mock 结果不记作已验证真实模型用量。提供超额申请及管理员审批（批准增加 5 次）。供应商异常或回退前可能已发送的请求会暂占额度并显示为 `uncertain`，不伪称已计费；目前需人工核查，尚无自动释放流程。
- 视频上传先保存为私有本地审批申请 `pending_approval`，此时不调用 Wan。管理员看到申请人、时长、大小、服饰和背景；点击批准有浏览器二次确认，服务端还要求 `confirm=true`。数据库事务先锁定申请，随后只提交一次现有 Wan 服务；重复批准返回 409。拒绝与删除申请不会生成视频。任务轮询只查询原任务。未能可靠计算费用，因此后台不展示价格。
- 全局「暂停所有 AI 服务」阻止新外部模型请求与新视频批准；游戏、本地作品和已有异步任务查询保留。任务、作品、媒体读取按 `user_id` 在后端隔离；管理员可查看全部。旧的无归属 Milestone 7 记录仅管理员可见。
- API 对错误文本做敏感信息遮盖，不记录上传媒体请求体。开发环境允许本机 Vite 变动端口；生产需精确前端 Origin 和后端 Host 白名单，不使用通配 CORS。跨站静态前端可通过登录及 `/api/auth/me` 响应取得内存中的 CSRF Token，刷新后重新获取。

## 操作方法

从项目根目录先执行一次（交互输入管理员用户名和至少 12 位密码；无默认密码）：

```powershell
.\.venv\Scripts\python.exe -m web.tools.account_store init-admin
```

若已有数据库，迁移命令可单独运行；启动 API 时也会自动执行幂等迁移：

```powershell
.\.venv\Scripts\python.exe -m web.tools.account_store migrate
.\.venv\Scripts\python.exe web\tools\mock_api.py
```

另开终端启动前端：

```powershell
cd web
npm.cmd run dev -- --host 127.0.0.1
```

后端默认 `http://127.0.0.1:8765`，前端默认 `http://127.0.0.1:5173`（占用时 Vite 可能改用 5174）。访问 `/login`；管理员进入 `/admin` 创建评委，将页面仅显示一次的初始密码交给评委。评委登录后使用 Agent、查看 `/works` 和剩余额度。视频页面按钮是「申请生成视频」；管理员在 `/admin` 审批并二次确认后，才可能发生真实 Wan 调用。当前是否能实际生成仍取决于现有服务端百炼权限、模型配置和素材合法性，本轮未实测第三方 API。

## 数据与部署准备

本地沿用 `%LOCALAPPDATA%\NaxiAIStudio\web\works.sqlite3`；`NAXI_DATA_DIR` 可指定持久目录，私有申请媒体在同目录的 `private/approvals/`，生成作品在 `artifacts/`。`web/tools/account_store.py` 的 `migrate` 命令建立账号、会话、额度、申请、任务、作品、审计表，并给旧 `jobs` 增加 `user_id`，不删除已有任务。原有未归属记录不自动分配给评委。

新增 `Dockerfile`、`.dockerignore`、`.env.example` 中的 `NAXI_API_ENV`、`NAXI_WEB_ALLOWED_ORIGINS`、`NAXI_API_ALLOWED_HOSTS`、`NAXI_DATA_DIR`、`NAXI_COOKIE_SAMESITE`、`VITE_API_BASE_URL`。生产必须挂载持久卷、配置精确 HTTPS 来源和后端 Host；优先让前后端经同源 `/api` 代理访问，以减少第三方 Cookie 限制；确需跨站时在 HTTPS 下设 `NAXI_COOKIE_SAMESITE=None`，并做实际浏览器验收。`GET /api/health` 可供健康检查。网站后端应只配置普通按量付费百炼 Key，不能使用 Token Plan `sk-sp-` Key；本轮未读取或修改现有密钥。

腾讯云静态托管、CloudBase 云托管、持久化云数据库和私有对象存储尚未部署。当前 SQLite 和私有磁盘文件适合单实例演示；多实例生产部署还需迁移至共享数据库/私有对象存储，并明确媒体保留与删除策略。浏览器游客游戏存档仍在原有 localStorage，未改成云存档。API 不提供原始申请视频的公开下载地址。

## API 路由

| 用途 | 路由 |
| --- | --- |
| 健康、登录、身份、退出 | `GET /api/health`；`POST /api/auth/login`；`GET /api/auth/me`；`POST /api/auth/logout` |
| 评委额度与申请 | `GET /api/quotas/me`；`POST /api/quotas/requests` |
| Agent（保留现有） | `POST /api/agents/dongba/evaluate`；`POST /api/agents/music/recognize`；`POST /api/agents/music/review`；`POST /api/agents/music/arrange` |
| 舞蹈申请与状态 | `POST/GET /api/agents/dance/requests`；`GET /api/agents/dance/requests/{id}`；`GET /api/agents/dance/requests/by-key/{key}`；`GET /api/agents/dance/jobs/{id}`；`GET /api/agents/dance/jobs/{id}/result`；`POST /api/agents/dance/jobs` 被拒绝 |
| 作品与素材 | `GET /api/works`；`GET /api/artifacts/{id}/{midi\|wav\|mp4}`；`GET /api/agents/music/assets`；`GET /api/agents/dance/options`；`GET /api/agents/dance/assets/{kind}/{name}` |
| 管理 | `GET/POST /api/admin/users`；`POST /api/admin/users/{id}/{reset\|disable\|enable\|delete\|revoke\|expire}`；`POST /api/admin/users/{id}/quota`；`GET/POST /api/admin/settings`；`GET /api/admin/approvals`；`POST /api/admin/approvals/{id}/{approve\|reject\|delete}`；`GET /api/admin/usage`；`GET /api/admin/quotas/requests`；`POST /api/admin/quotas/requests/{id}/{approve\|reject}` |

## 文件与验证

新增：`web/tools/account_store.py`、`web/tools/test_accounts.py`、`web/src/agents/LoginPanel.tsx`、`AdminPanel.tsx`、`QuotaPanel.tsx`、`Dockerfile`、`.dockerignore`、本报告。修改：`web/tools/mock_api.py`、`agent_runtime.py`、`web/src/agents/api.ts`、`DanceAgentPanel.tsx`、`WorksPanel.tsx`、`MusicAgentPanel.tsx`、`agents.css`、`web/src/main.tsx`、`web/tsconfig.json`、`.env.example`。

定向离线测试：`python -m unittest web.tools.test_accounts -v` **4/4 通过**，覆盖登录、密码哈希、Judge/Admin 隔离、禁用、CSRF、严格生产 Origin/Host、额度、全局暂停、作品隔离、视频申请零调用和重复批准只提交一次（Wan 由测试替身代替）。相关 Python 文件 `py_compile` 通过。前端 `npm.cmd run build` 通过。构建产物扫描未发现 `DASHSCOPE_API_KEY`、`OPENAI_API_KEY`、`sk-sp-` 或会话 Cookie 名称。未执行历史全量测试、浏览器端到端验收或真实 Qwen/Wan 调用；真实服务权限和费用须在现场由管理员单次手动验证。
