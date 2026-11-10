# 东巴文字形与玩家样本采集指南

本版使用 CSV + 图片目录，无数据库服务、无自动采集、无 API 调用。当前五张图已按用户提供的名称建档，玩家样本表仍只有表头。

## 目录和路径

- `data/glyphs/original/`：保留有权使用的原始图，不覆盖原稿。
- `data/glyphs/processed/`：人工裁剪、去背景后的派生图，不能用生成式补画伪造示范。
- `data/glyphs/glyph_catalog.csv`：每行一份字形资料。
- `data/handwriting_samples/images/`：获得同意的玩家书写图片。
- `data/handwriting_samples/strokes/`：可选在线画布轨迹 JSON；照片没有轨迹，留空。
- `data/handwriting_samples/sample_annotations.csv`：每行一次书写样本。

CSV 用 UTF-8（支持 BOM）、英文逗号；包含逗号或换行的内容用双引号包围。字形表只使用下述七个字段，均需填写。编辑完请关闭 Excel/WPS，避免文件被占用导致无法同步。

路径相对于项目根目录，例如 `data/glyphs/processed/<glyph_id>.png`，不是相对于 CSV 所在目录。不要填写盘符、URL、`../`，也不能通过符号链接越界。示范图限于 data/glyphs 内 PNG/JPG/JPEG，10 MB、1600 万像素；服务返回白底 RGB 预览，最长边 1600，原图文件不变。

## 字形字段

| 字段 | 填写规则 |
| --- | --- |
| glyph_id | 唯一编号，当前 dongba_01 至 dongba_05 |
| chinese_meaning | 按用户提供的中文含义填写 |
| english_label | 对应英文名称 |
| image_file | 原始图片文件名 |
| image_path | 项目根目录相对路径 |
| image_width | 实际图片宽度（正整数） |
| image_height | 实际图片高度（正整数） |

JSON 索引保存这七个字段，另外记录实际格式、SHA-256、可读性、空白检查和深色像素数。没有书籍、页码、审核或授权状态字段，不设置额外审批门槛。

## 新字形添加步骤

1. 放置原图，明确编号和中英文名称；不根据图片猜测释义。
2. 使用 Pillow 验证并完整解码，读取实际尺寸和格式，检查是否空白。
3. 写入七字段 CSV，按原文件字节计算 SHA-256 后同步 JSON；保留原图不变。
4. 通过 `GlyphDataService.find_glyphs(glyph_id)` 查询并加载图片，再运行测试检查 CSV/JSON 一致性。修改 CSV 不会自动重写 JSON，更新时必须同步两份文件。

## 玩家样本字段与同意

| 字段 | 填写规则 |
| --- | --- |
| sample_id、character_id | 必填；sample_id 唯一，character_id 与目标字符对应 |
| input_method | 必填，约定 online_canvas 或 photo_upload |
| image_path | 必填，data/handwriting_samples/images 下的项目相对路径 |
| stroke_data_path | 可选，data/handwriting_samples/strokes 下 JSON 路径 |
| annotator_id | 人工标注者的化名/内部 ID，避免个人隐私 |
| human_rating | 未标注留空；约定 close/partial/mismatch/unreadable，不填模型计算分 |
| error_type | 可选，缺失、多余、比例、方向、位置等实际观察；多项用分号分隔 |
| annotation_status | pending / annotated / disputed，未审核不得填 annotated |
| notes | 目标 glyph_id、授权/同意记录位置、采集日期、标注依据、争议及保留期限 |

本版查询服务检查必要字段和路径，不执行人评语义或轨迹 JSON 内容验证。标注枚举是填写约定，不是专属模型训练标签校验器。学习保存与训练授权应分别取得同意，在 notes 引用记录；仅有文件不等于可用于训练。不得从照片推断笔顺。建议轨迹以后包含 schema_version、画布宽高、笔画顺序、坐标/时间；本轮不改画布、不自动写文件。

不要将玩家隐私提交 Git。本版不修改原 .gitignore，以上目录不是自动被忽略的目录；提交前检查暂存清单。玩家样本表中的 character_id 未来可对应本目录 glyph_id；本轮不修改样本表结构。

## 与现有页面的关系

`services/glyph_data.py` 是独立只读管理接口；`data/dongba/characters.json` 和 `services/dongba_data.py` 保持原样。本轮不做自动转换或同步，填写 CSV 不会让条目自动出现在 Streamlit 页面。后续 Agent 可按 glyph_id 获取 Pillow 参考图，具体示例见 `DONGBA_GLYPH_INVENTORY.md`。

返回对象包含 records/messages，图片结果包含 image/messages。缺图、损坏图、尺寸不符、表头缺失、无匹配记录都通过提示返回；一个缺图不会阻断其余条目。重复 glyph_id/sample_id 会拒绝整张表以避免歧义。调用方应始终显示 messages，而非仅查看 records。
