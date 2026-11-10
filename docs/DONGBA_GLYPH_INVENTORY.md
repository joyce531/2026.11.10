# 五个基础东巴文字形建档检查

日期：2026-11-08。编号和中英文名称按用户提供的映射登记，未通过 AI 推断释义。原图只读，未裁剪、重编码或覆盖。original 中的 `.import` 文件是既有 Godot 辅助文件，不作为字形登记，也未修改。

| 图片 | 编号 | 中文 | 英文 | 实际尺寸（宽×高） | 格式 | 检查结果 |
| --- | --- | --- | --- | --- | --- | --- |
| ![人](../data/glyphs/original/dongba_01_person.png) | dongba_01 | 人 | person | 112×75 | PNG / 灰度 L | 正常读取，非空白 |
| ![山](../data/glyphs/original/dongba_02_mountain.png) | dongba_02 | 山 | mountain | 324×216 | PNG / 灰度 L | 正常读取，非空白 |
| ![水](../data/glyphs/original/dongba_03_water.png) | dongba_03 | 水 | water | 134×90 | PNG / 灰度 L | 正常读取，非空白 |
| ![火](../data/glyphs/original/dongba_04_fire.png) | dongba_04 | 火 | fire | 143×96 | PNG / 灰度 L | 正常读取，非空白 |
| ![太阳](../data/glyphs/original/dongba_05_sun.png) | dongba_05 | 太阳 | sun | 155×103 | PNG / 灰度 L | 正常读取，非空白 |

## 检查方法

逐张确认文件存在，执行 Pillow `verify()`，重新打开后 `load()` 完整解码。所有图片灰度范围均为 0–255。空白检测规则：灰度范围差小于 10，或灰度低于 200 的像素少于 20，则标记为空白/近空白。五张图深色像素数量依次为 824、6216、1560、2391、1985，均未触发该规则。该检查用于发现损坏或空白文件，不是文化含义或手写评价算法。

对原始文件字节计算 SHA-256，记录在 JSON；CSV 的七个字段与 JSON 同名字段一致（CSV 数值以文本存储）。路径均以项目根目录为基准。未加入书籍、页码、授权或专家审核字段。

| 编号 | SHA-256 |
| --- | --- |
| dongba_01 | `970f140dfd812d316da907b7cb17b2af33984ac177d0dcb33a4a1f4023bcb4c5` |
| dongba_02 | `ae13efec938ac79e29be25403937ff027ffd21970795e12f6952286529598428` |
| dongba_03 | `497c66b55885c945926aad7714ac2c1715f69ce9df8e050db805afbb7f746a1f` |
| dongba_04 | `bc60b3486c8ced6d5ac8609bf4f7a608775789e2695c0f35163f964f97ea75fc` |
| dongba_05 | `8698fa9d1500d00c31c8cfb0cc7b30b773d75838f674ac7812594092c2d9f857` |

## 后续 Agent 读取

```python
from services.glyph_data import GlyphDataService

service = GlyphDataService()
result = service.find_glyphs("dongba_01")
if result.messages:
    print(result.messages)
if result.records:
    record = result.records[0]
    loaded = service.load_reference_image(record)
    if loaded.image is not None:
        reference_image = loaded.image  # Pillow RGB 图像，供后续双图比较使用
        target_id = record["glyph_id"]
    else:
        print(loaded.messages)
```

也可以用标准库 json 读取 `data/glyphs/glyph_manifest.json` 的数组，按 glyph_id 查询，再从项目根目录拼接 image_path。当前五字目录用 glyph_id 作为目标 ID；未来 Agent 若使用 character_id 参数，可在调用边界传入同一值，不必在 CSV 重复增加字段。

本轮只完成数据建档和独立读取服务适配，没有修改 Agent、现有 Streamlit 页面或旧 `data/dongba/characters.json`，没有接入 AI 或训练模型。旧页面尚未切换到此目录。
