# Milestone 4B：Qwen 视觉 JSON 故障修复记录

日期：2026-11-08。**本轮完成代码修复与离线验证；真实 API 成功返回和页面展示尚未验收。** 沙箱内的两次单次测试都在网络连接阶段失败，沙箱外重试申请被自动审批拒绝，因此不能把离线测试写成远端成功。

## 原因与修复

生产代码此前已经使用 `response_format={"type":"json_object"}`、明确的 JSON 提示、`enable_thinking=false`、`choices[0].message.content` 和视觉模型直连。与此前成功的小请求相比，生产共享服务还设置了 `max_tokens=4096`，识谱另设 `max_tokens=12000`。百炼[结构化输出说明](https://help.aliyun.com/zh/model-studio/qwen-structured-output)要求 JSON Object 请求不要设置 `max_tokens`，以免对象被截断；多模态图片也不能使用 JSON Schema 模式，应使用 JSON Object 并在本地校验。因此已移除 Qwen 请求中的 `max_tokens`，保留本地严格 Schema。此前把无内容、截断、JSON 解析失败与字段校验失败合并成一个笼统报错，导致历史页面故障无法精确归因。**由于没有保存当时失败响应的安全诊断，不能证明历史每次失败都由截断引起。**

共享服务现在对文本智能路由只发送纯字符串，对视觉模型发送图片；没有换模型、换 Key、重试或增加模型调用。生产 HTTP 响应通过 SDK 原始响应包装读取状态码，再读取 `choices[0].message.content`；兼容单一文本内容块与 Markdown JSON 围栏。`QWEN_DEBUG=true` 时只记模型、HTTP 状态、`finish_reason`、输入/输出 Token、内容类型、JSON 解析、Schema 结果、失败类别、字段路径与 Mock 回退；不记密钥、图片 Base64、提示词、完整响应或请求地址。API 连接、HTTP 错误、空内容、截断、JSON 语法、Schema 字段和下游业务校验分别提示。

东巴文仍是标准图和玩家图一次双图请求；本地质量拦截仍先执行。六字段校验成功才标记 `source=qwen_vision`；失败则明确标记 `source=mock` 并显示回退原因。简谱/五线谱沿用 OpenCV 分类、Qwen 视觉识谱、未知项 `null`/低置信、校对表和人工确认后生成 MIDI 的门槛。Qwen 识谱失败不生成模拟音符。文本编曲规划、MIDI/WAV 合成、真实采样与下载链路没有改动。

## 文件

- 修改 `services/qwen_service.py`：移除 Qwen `max_tokens`、解析和错误分类、安全开发诊断。
- 修改 `services/dongba_vision.py`：区分 Dongba JSON、Schema、业务校验错误。
- 修改 `naxi_agents/dongba_agent.py`：记录真实 AI 失败后的 Mock 回退与下游业务校验失败。
- 修改 `services/score_omr.py`：移除两类 Qwen 图片识谱的 `max_tokens`，记录不可用草稿的业务校验失败。
- 修改 `tests/test_qwen.py`：断言 JSON Object、无 `max_tokens`、双图和文本分流、围栏/空内容/字段路径、原始 HTTP 元数据与无敏感日志。
- 修改 `README.md`：开发诊断方法。
- 新增本报告。没有修改 `.env`、游戏、舞蹈、字形、音乐素材或音乐数据库；没有 Git 提交。

## 验证结果

| 检查 | 结果 |
| --- | --- |
| 离线单元/页面回归 | 69/69 通过；包括 Qwen 假客户端双图、识谱草稿、Mock 标签、文本编曲与本地 WAV/MIDI 生成 |
| Python 语法 | 34 个相关 Python 文件均通过 AST 解析 |
| 依赖 | 当前虚拟环境 `pip check` 通过，未安装新依赖 |
| 东巴真实双图单次受限环境测试 | `failure_type=api_connection`，无 HTTP 响应；页面/Agent 回退 `source=mock`，因此**未通过真实 AI 验收** |
| 简谱真实单次受限环境测试 | OpenCV 判为简谱，29 个数字候选；`failure_type=api_connection`，未产生音符草稿，**未通过真实 AI 验收** |
| 实际 Token | 两次均未收到 HTTP 响应；服务端 Token 用量不可获取，不能填 0 或推断扣费 |

API Key、Base URL、模型 ID 保持现有配置；本轮无法远端确认账户和模型服务状态。历史报告记录过同一配置下文本、视觉最小请求、双图、简谱片段和音乐规划成功，不能据本轮受限网络失败推断配置错误。即使联网后 Schema 通过，简谱的附点、减时线、调号和局部遮挡仍需人工逐音核对；模型视觉相似度也不是经过标定的准确率。

## 启动与现场验收

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
$env:QWEN_DEBUG='true'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

在允许访问百炼的本机终端、已有 `.env` 配置和 `USE_REAL_AI=true` 下，进入 `/dongba` 选字并提交一次清晰画布/照片，确认来源显示“阿里云百炼 Qwen 视觉 AI”且 `source=qwen_vision`；进入 `/music` 上传清晰简谱片段，点击一次“开始图片识谱”，确认得到带置信度的待校对音符表。终端诊断应出现 HTTP 200、`finish_reason=stop`、`json_parsed=true`、`schema_valid=true` 及实际 Token 用量。若出现 Mock 或无音符，先按 `failure_type` 和 `schema_error_path` 排查；不要把 Mock 结果当真实输出。
