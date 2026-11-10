# 音乐素材数据库与采样映射

现有原始素材目录保持原样：

```text
data/music/
  ensemble/baisha/         # 2 个原 MP3，按目录标为白沙
  ensemble/dongjing/       # 3 个原 MP3，按目录标为洞经
  instruments/            # 8 个乐器标签 MP3，内容身份待听审
  music_library.sqlite3   # 可供 Python / Agent 查询的元数据数据库
  music_manifest.json     # 人类可读的相同扫描结果、声学统计与采样映射
```

只新增两个索引文件，不复制或提取音频到新素材目录。合成直接读取原文件的指定时间区间；旋律作品和 WAV 下载在会话内生成，默认不落盘。

## 建库与查询

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tools/scan_music_library.py
```

同时生成 [素材清单](MUSIC_ASSET_INVENTORY.md)。扫描会逐块解码每个文件，实际读取格式、时长、采样率及声道，不假设扩展名。无法解码的文件仍登记失败状态，不参与生成。

```python
from services.music_library import list_assets, find_asset, audio_path
assets = list_assets()
item = find_asset(assets[0]['asset_id'])
path = audio_path(item['path'])  # 相对项目根目录；限制在 data/music 内
```

SQLite 表：`assets(asset_id TEXT PRIMARY KEY, path TEXT UNIQUE, metadata_json TEXT NOT NULL)`。这是本地元数据数据库，不存音频 BLOB。JSON 文档字段：

| 字段 | 意义 |
|---|---|
| asset_id | 相对路径 SHA-256 前 16 位，稳定素材 ID |
| path / label / extension | 相对路径、原文件名标签、实际扩展名 |
| material_type | ensemble / instrument，来源目录 |
| category | 洞经 / 白沙 / 未知，目录标签而非声音鉴定 |
| instrument_name | 文件标签，合奏为 null，不代表已确认内容 |
| identity_status | 待核实或已发现的重复合奏冲突 |
| duration_seconds / sample_rate / channels / format / subtype | 实际解码元数据 |
| sha256 / duplicates | 内容哈希及重复素材 ID |
| purpose / analysis_status | 用途与完整解码结果，身份审核另列 |
| features | RMS、峰值、频谱重心、节拍候选、分析窗口与局限 |
| sample_mapping | 有限音高候选 / 短片段 / null |

`decoded_full_content_unverified` 表示完整可解码，不是内容鉴定或专家审核。`笛子.mp3` 与 `baisha_01.mp3` 字节相同，因此强制 `sample_mapping=null`，只可参考，不能作为独立笛子音源。

## 当前采样映射

映射保存在数据库 JSON 中，字段为 `mode`、`start_seconds`、`duration_seconds`、`root_midi`、`max_semitones`、`status`、`note`；稳定音高候选另有自相关 `confidence`。全部标记为自动候选、内容待核实。

- `limited_pitch`：连续四帧音高稳定才生成候选，允许相对根音 ±3 半音。通过重采样移调；短音裁切、长音交叉淡化循环。不能冒充完整音域、力度与奏法采样库。
- `phrase`：取原录音可听区间作为一次短片段点缀，不把它当作可控音符，不声称已经识别出音乐学意义的乐句。
- `null`：无可用单件录音，包括与合奏重复的“笛子”；逐音使用通用辅助合成音并在作品报告计数。

当前没有完整单音采样库。增加录音后重新扫描即可增加素材；未来可把一个素材的 `sample_mapping` 扩展为多音高/力度映射列表，并在渲染器中增加精确采样选择。该扩展接口是数据设计，不宣称当前已实现完整采样器。无需为每种乐器收集完整音域才能使用当前有限采样/片段模式。

## 风格分析与合成边界

合奏录音仅提供前 60 秒的声学测量。节拍候选可能倍频/半频，频谱重心不等同于音色身份；没有据此认定传统调式、旋律语法或乐器配合。洞经/白沙选择决定读取哪组参考证据；本地规则据脉冲候选决定伴奏疏密，AI 可给出受约束的声部分工。所有作品均是素材参考实验。

辅助合成是普通正弦谐波包络，不命名为纳西乐器；实际使用情况逐轨记录。MIDI 保存音符与速度，WAV 才含真实录音声音。短片段不是 MIDI 音符，通用 MIDI 播放器无法复现 WAV 的采样音色。

技术依据：[SoundFile 本地解码](https://python-soundfile.readthedocs.io/en/latest/)、[Mido MIDI 时间与消息](https://mido.readthedocs.io/en/latest/api.html)、[W3C MusicXML 结构](https://www.w3.org/2021/06/musicxml40/tutorial/structure-of-musicxml-files/)。这些是工程资料，不是纳西音乐文化来源。
