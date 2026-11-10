# 东巴目标字数据接口

`characters.json` 当前为 **空数组**。项目中没有真实东巴字形或已核验教学条目；不把几何工程自测图形加入字库。

正式启用前，请提供：

1. 每个字独立的清晰 PNG/JPEG 示范图，白底深色字、完整留白、无标题/水印干扰；须有合法使用权。
2. 稳定字符 ID、中文释义、构形说明、学习提示。
3. 可核查的数据来源，例如教材名称、作者、页码或授权资料标识。
4. 审核者、审核日期和使用授权确认；可靠读音及其来源可选，没有就留空，不猜测。

图片放在本目录下，例如 `references/<character_id>.png`，JSON 中使用相对于本目录的路径。不得使用绝对路径、外部 URL 或 `../` 路径。正式图片与字段需要人工审核；程序的 `verified` 只是审核记录，不会替你核实文化真实性。

字段定义见 `characters.schema.json`。只有 `review_status = verified` 且 `usage_permission = authorized` 的条目进入学习列表；待审核和拒绝的条目不展示。每个 ID 必须唯一，有读音就必须有 `pronunciation_source`。可以用 `alternative_interpretations` 保存不同可靠来源的解释。

## 从 Godot 导入

当前提供的是标准数据契约和加载器，不是已经适配某个 Godot 项目的转换器。不要修改原游戏。

从原教学游戏单独导出有权使用的字形 PNG/JPEG 和元数据，将原资源 ID 映射为 `character_id`、原示范图映射为 `reference_image`、释义映射为 `chinese_meaning`。补齐构形、来源与授权字段，先设 `pending` / `unknown`；经人工核验后再设置 `verified` / `authorized`，填写审核者和日期。不要直接导入 Godot `.import` 缓存或未授权资源。

完成后刷新应用。加载器会检查 Schema、重复 ID、图片格式、文件大小及目录边界。任何已审核条目存在损坏图片或非法字段时会提示错误，不会静默展示错误数据。

## 未来训练记录

`training_record.schema.json` 预留：

| 字段 | 含义 |
| --- | --- |
| character_id | 已知目标字 ID |
| reference_image | 示范图片路径/受控资源标识 |
| user_handwriting_image | 玩家书写图片路径/受控资源标识 |
| similarity_label | 人工审核标签 0–1；未标注必须为 null |
| structure_errors | 结构问题列表 |
| evaluation_feedback | 修改建议列表 |
| data_source | 来源及采集方式 |
| consent | 是否已获得训练使用同意 |
| label_source | unlabeled / human_reviewed |
| prototype_score | 可选的原型计算分，不能作为人工真值标签 |
| algorithm_version | 可选的算法版本 |

当前不会自动保存图片、创建训练集或训练模型。未来采集程序必须检查同意状态、用途和保留期限，只用获准样本。Siamese Network / 度量学习需在积累真实正负样本及人工标签后研究，并按用户/目标字划分验证集以避免数据泄漏。
