# Milestone 5 图片识谱验收记录

日期：2026-11-08。范围仅限音乐模块图片入口，不修改东巴文 Agent、打跳、Godot 或音乐素材数据库。

## 实现链路

图片上传 → 文件/像素限制与 EXIF 处理 → OpenCV 光照归一、轻微倾斜校正 → 五线等距线组与数字模板证据判别 → 对应真实识谱引擎 → 统一音符事件表 → 人工修改、辅助音试听 → 明确确认 → 复用既有 MIDI 写入、编曲与 WAV 合成。

- 输入支持 PNG/JPG/JPEG/WEBP，限 10 MB、1600 万像素；PDF 和手写谱不在本轮承诺内。可百分比裁剪，不写回原图。
- 判别不是「没有五线就视为简谱」。须有数字形状证据；混排或证据不足返回 unknown，才要求手动选择。启发式仍可能误判，不是通用分类模型。
- 五线谱：真实 Audiveris 本地命令行，导出 MusicXML/MXL，安全解析后复用已有 `music_score.py`。无逐音可信概率，所以所有音符标为待核对；休止通过事件间隔保留。
- 简谱：OpenCV 预处理后，一次真实 Responses 图片请求，JSON Schema 校验。读取数字、上下点、减时线、右侧附点、休止、增时横线、小节线与简单延音线。音符保留级数、八度、临时升降、基础拍长、附点、置信标签和问题说明。低/中置信与未知时值标记待校正。
- 调性：读取并允许修改 `1=A` / `6=A` 等，按参考音与自然音阶换算；缺少调号不默认 `1=C`。参考八度明确展示，需听辨；未知速度的 120 BPM 只是校对试听默认值，并非识别结论。
- 统一事件包含 start/duration（秒）、pitch（MIDI）、rest、voice、symbol、uncertain、issue、reviewed。可修改、增删并下载记录。草稿试听直接复用 WAV 渲染器，不提前生成 MIDI。
- 确认全部音符和调性后才生成 MIDI；未支持符号还需确认范围/处理方式。修改草稿或撤销确认使旧 MIDI 不再可用。全选确认只是用户声明，不是模型自动批准。
- 简谱只在按钮点击时调用一次、不重试、不降级 Mock；失败明示。五线谱无 API 消耗。后续改编继续原有本地/AI 规划设置。

## 真实素材测试

现有 `data/music/曲谱/` 共 8 张：两张简谱、六张五线谱。全部可读取；自动路由 8/8 与人工预期一致。这是小样本路由结果，不是音符准确率。

| 检查 | 实测结果 | 限制 |
|---|---|---|
| 《青花瓷》简谱前段，保留标题调号和第一谱行 | 真实 gpt-6-luna Responses 调用成功；34 个事件；读出 1=A、4/4、60 BPM | 已有中置信事件，仍需逐音核对；未声称完整转录全曲 |
| 《青花瓷》五线谱 p1 | 真实 Audiveris 5.11.0 导出 MXL，转换为 195 个待校对音符 | 发现反复/跳房，不自动展开；仅当前页印刷顺序 |
| 《兰亭序》简谱与其余五线谱图片 | 可读取并正确路由 | 尚未全部运行逐音识别或建立人工真值对照 |

真实测试结果存于本机临时目录 `TEMP/naxi-score-omr` 与 `TEMP/naxi-score-omr-staff`，不写入素材库。CLI 未替用户确认音符，也未自动生成歌曲 MIDI。图片识谱成功不等于节奏、声部或每个音符均正确。

## 依赖与运行

- 当前 `.venv` 新增 `opencv-python-headless==5.0.0.93`；复用现有 Pillow、NumPy、OpenAI、python-dotenv、jsonschema、defusedxml、mido、soundfile、Streamlit。未修改全局 Python。
- Audiveris 5.11.0 官方 Windows Console 包已校验 SHA-256，解压于 `%LOCALAPPDATA%/NaxiAIStudio/tools/audiveris-5.11.0/Audiveris/`，自带 Java，不替换系统 Java 8。
- `AUDIVERIS_EXE` 可指定 exe；不配置则自动查找上述工具目录和 PATH。缺少引擎给出安装提示，不冒充完成识谱。批处理固定参数、临时目录，180 秒超时。
- 简谱复用根 `.env` 的 `OPENAI_API_KEY`、`USE_REAL_AI=true`；独立模型变量 `MUSIC_OMR_MODEL` 默认 gpt-6-luna。未修改 `.env`、未输出密钥。
- 开发沙箱最初阻止 Java 读取自身 security 配置，授权后实际运行成功；这是测试沙箱权限限制，不是音符解析失败。

官方依据：[Audiveris 命令行](https://audiveris.github.io/audiveris/_pages/guides/advanced/cli/)、[官方二进制安装说明](https://audiveris.github.io/audiveris/_pages/tutorials/install/binaries/)。安装辅助脚本只从官方 GitHub 发行下载并验证固定哈希。

## 测试与文件

57 项 unittest 全部通过（含新增 9 项识谱测试）：实际 8 图路由、无调号拒绝、1=A/6=A、八度与升降、附点/休止/延长/简单延音、不确定时值阻断、人工确认门槛、试听 WAV、MIDI 往返、API 单次调用与错误、缺引擎、MusicXML 反复提示、页面重绘不重复请求与确认撤销。API 单元测试使用明确测试替身；以上真实引擎实测单独列出，不混淆。

本机 Chrome 浏览器验收通过：真实五线谱文件上传 → 自动路由 → Audiveris → 校对确认门槛 → HTML 音频实际播放 → 校对 MIDI 实际下载/解析 → 原有本地改编成功。浏览器测试中的确认仅用于验证交互，不代表人工音乐校验完成。截图位于 `TEMP/naxi-music-omr.png`。

相关 Python 文件 AST 语法检查通过；32 个受保护文件（音乐资源/库/曲谱、关键其他模块、`.env`、`.gitignore`）哈希未改变。没有 Git 提交。

新增：

- `services/score_image.py`：安全读图、OpenCV 预处理与类型判别。
- `services/score_omr.py`：真实视觉简谱、Audiveris 与统一导入适配。
- `services/score_review.py`：调性换算、事件校验、试听与确认门槛。
- `components/score_review.py`：上传后的识别、校对、试听与下载界面。
- `tools/test_score_omr.py`：实际图片路由/引擎验证。
- `tools/setup_audiveris.py`：官方本机工具安装辅助。
- `tests/test_score_omr.py` 与本报告。

修改：`pages/music.py`、`requirements.txt`、`.env.example`、`README.md`、`tests/browser_smoke.py`；`ui.py` 仅增加可选关闭旧占位提示的参数，只有音乐页使用，其他页默认行为不变。复用原有音乐解析/编曲/合成，不改其算法或素材映射。

## 未支持与仍需完善

- 简谱最多 128 个事件/次，建议一至两行；复杂多声部、换调、跳房/反复、装饰小音符、三连音等需标注为部分识别，人工补正或裁剪。五线谱沿用 MusicXML 解析范围；装饰小音符明确拒绝，反复/跳房只提供线性顺序并警告，复杂演奏法不还原。
- 没有跨页自动拼接、曲谱排版编辑器或专门训练的 OMR 模型。人工编辑目前使用秒与 MIDI 音高，不是拖拽五线谱。
- 自动判别依赖本机 Windows 字体模板，非 Windows 无这些字体时简谱可能转人工选择。严重透视、阴影、混排、低分辨率小点/减时线仍可能出错。
- 模型标记 high 也可能错，全部事件均要求用户核对。未建立逐音准确率基准，未证明完整《青花瓷》转录正确，不把未校对草稿宣传为成品。
- 现有图片已经足够测试入口；建议补充清晰高分辨率印刷谱（尤其低分辨率《兰亭序》简谱）以及对应正确 MIDI/MusicXML，便于建立节奏、调号、音高的人工真值测试。无需补充乐器音频即可使用本轮识谱功能。

启动：`.\.venv\Scripts\python.exe -m streamlit run app.py`，进入古乐页上传图片，按「识别 → 校对试听 → 确认生成 MIDI → 改编」操作。
