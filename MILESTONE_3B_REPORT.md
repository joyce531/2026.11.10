# Milestone 3B：东巴文临摹评价 Agent

验收日期：2026-11-08。目标是指定标准字形与玩家作品的比较，不是 OCR，也不输出未经核实的文化解释。

## 实现范围

- 五字目录直接接入页面。现有 CSV 的真实字段为 glyph_id、chinese_meaning、english_label、image_file、image_path、image_width、image_height；接口 character_id 映射到 glyph_id，没有改 CSV。
- 保留原 JavaScript Canvas，鼠标/触屏、笔宽、颜色、撤销、清空均继续使用。提交 PNG 与有序笔画坐标，增加载荷校验、报告和轨迹下载；不从照片推断笔顺。
- 照片支持 PNG/JPG/JPEG，10 MB/1600 万像素限制、EXIF 方向、旋转和裁剪。原始字节保留会话；生成带留白的 512×512 ROI 副本，不改原始字形。
- Pillow/NumPy 做空白、过暗、过小和明显模糊检查，复用原有形态测量服务。未安装 OpenCV 或大型训练依赖。
- 输出 match/close/incorrect/uncertain、相似度估计、结构说明、差异、具体建议和置信度。明显错误显示明确的重新临摹提示；质量不足不调用 API。
- 默认 Mock，无网络费用；真实结果、Mock、质量检查来源分别标记，不静默降级。
- SQLite 保存学习评价元数据，默认位于 `%LOCALAPPDATA%/NaxiAIStudio/learning.sqlite3`，不保存图片和轨迹，不进入项目 Git。保存失败仍保留页面结果并提示下载。

## 实际 Agent 和 API

环境已安装 openai 3.46.0、python-dotenv 1.2.4，未安装 openai-agents。旧顶层 agents/ 保留，新增 naxi_agents/ 避免未来 SDK 导入命名冲突。没有声称已使用 Agents SDK。

当前采用 OpenAI Responses API，默认 gpt-6-luna，DONGBA_VISION_MODEL 可覆盖。从根目录 .env 读取 OPENAI_API_KEY，环境变量优先；不打印密钥。每次评价最多两次请求、单次超时 45 秒、关闭自动重试、store=False。

执行链：读取并验证目标 → 验证玩家图像 → 同时发送明确标注的标准图与玩家图 → 模型发起 measure_structure 函数调用 → Python 执行本地形态测量并回传 → 模型输出严格 JSON → 后端校验并展示/保存。

这是有界的模型工具调用工作流，不是仅给页面包装 AI 标签，也不是复杂自主多 Agent 系统。工具分来自覆盖、比例、重心和区域分布计算；视觉分是模型估计，二者不是科学标定准确率。

## 文件清单

新增：

- naxi_agents/__init__.py、naxi_agents/dongba_agent.py
- tools/dongba_tools.py、tools/test_dongba_agent.py
- services/dongba_vision.py、services/handwriting_quality.py、services/learning_records.py
- tests/test_dongba_agent.py
- MILESTONE_3B_REPORT.md

修改：

- pages/dongba.py：五字选择与完整评价流程。
- components/handwriting_canvas.js、components/handwriting_canvas.py：PNG/轨迹提交及校验。
- app.py：仅更新能力说明，保留首页布局和导航。
- tests/test_app.py、tests/browser_smoke.py：页面和真实浏览器回归。
- .env.example、README.md、AGENTS.md：配置说明、架构边界与体验方法。

保留：requirements.txt、.gitignore、.env、七字段 CSV、JSON 索引、五张原图、旧本地评价服务、Godot/古乐/打跳页面及服务。没有操作原始 Godot 工程，没有提交或推送 Git。当前大量未跟踪文件来自之前里程碑，不能把 git status 中所有文件算作本轮新增。

## 验证记录

- 当前虚拟环境运行全部 37 项单元/页面测试通过，覆盖清晰上传、画布 PNG/轨迹、空白、模糊、过暗、过小、无关图形、缺标准图、缺 Key、请求失败、JSON 校验、双图工具调用和 SQLite 幂等保存。
- 32 个 Python 文件 AST 语法检查通过；pip check 无依赖冲突；git diff --check 通过。
- Streamlit 实际启动成功，健康检查 HTTP 200。Chrome Mock 完整回归退出码 0：验证首页其他模块导航、鼠标画线、提交、错误反馈、撤销、清空、空白拒绝、照片预处理及相同/错误图片提交、切换目标清除旧结果、独立 /dongba 访问。
- 真实 API 测试已执行：标准图缩放副本得到 close/92；无关矩形得到 incorrect/2。两组都真实执行 measure_structure 工具调用并返回结构化结果。不是玩家数据集准确率，也不是所有五个字的全面评测。
- 原图和目录与改动前备份对比一致。测试夹具在临时目录；数据库单元测试使用临时 SQLite，浏览器测试关闭记录保存以免污染学习历史。

开发时修复了质量检查紧包围盒导致实心线误判模糊的问题，并添加清晰水平线回归断言。浏览器测试期间的文件热更新提示干扰等待，因此最终浏览器验收服务器关闭文件监听；正常使用仍可按常规命令启动。

## 启动

```powershell
Set-Location D:\Projects\Naxi_AI_Demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

打开 http://localhost:8501，进入东巴文模块或 `/dongba`。默认 Mock；真实体验需要根目录 .env 的 OPENAI_API_KEY，关闭 Mock 后选择目标并提交。模型可配置为 `DONGBA_VISION_MODEL=gpt-6-luna`。

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B tools/test_dongba_agent.py
# 下面命令会产生真实 API 费用：两组图片，最多四次请求
.\.venv\Scripts\python.exe -X utf8 tools/test_dongba_agent.py --live
```

## 限制与后续

仅五个已有字形；无专属模型训练、专家标定、可靠读音或规范笔顺数据。照片背景、透视和阴影会影响启发式质量门槛及模型判断。相同字形缩放后仍被模型指出细节偏差，说明需要真实手写样本和人工标签验证。触屏使用现有 Pointer Events 实现，本轮浏览器自动验收使用鼠标，不等同于实体手机测试。

学习记录仅适合本机单用户，不做账户隔离；沙箱可能限制用户数据目录写入，页面会提示保存失败，临时数据库测试已验证存取逻辑。没有把未测试的真实用户目录写入宣称为成功。

后续可收集经用户同意的真实笔迹与人工评价，校准误判/拒绝阈值，评估复杂背景处理，再引入 Agents SDK 或专属度量模型。音乐与视频仍是界面骨架，不声称接入生成 API。
