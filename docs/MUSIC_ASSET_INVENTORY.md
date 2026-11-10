# 音乐素材扫描报告

实际逐块解码所有文件；无音频上传、复制、移动或修改。名称/类别仅为目录标签，未据文件名确认声音身份。

| 标签 | 类型/类别 | 格式 | 时长(s) | 采样率/声道 | 解码 | 采样用途 |
|---|---|---|---:|---|---|---|
| baisha_01 | ensemble/白沙 | MP3 | 36.153 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| baisha_02 | ensemble/白沙 | MP3 | 43.584 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| dongjing_01 | ensemble/洞经 | MP3 | 99.985 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| dongjing_02 | ensemble/洞经 | MP3 | 62.044 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| dongjing_03 | ensemble/洞经 | MP3 | 63.739 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| 人面竹胡琴 | instrument/未知 | MP3 | 29.994 | 48000/1 | decoded_full_content_unverified | limited_pitch |
| 十面云锣 | instrument/未知 | MP3 | 41.13 | 48000/1 | decoded_full_content_unverified | limited_pitch |
| 口弦 | instrument/未知 | MP3 | 118.357 | 48000/1 | decoded_full_content_unverified | phrase |
| 曲项琵琶 | instrument/未知 | MP3 | 14.165 | 48000/1 | decoded_full_content_unverified | limited_pitch |
| 波伯 | instrument/未知 | MP3 | 71.275 | 48000/1 | decoded_full_content_unverified | limited_pitch |
| 碰铃 | instrument/未知 | MP3 | 10.346 | 48000/1 | decoded_full_content_unverified | limited_pitch |
| 笛子 | instrument/未知 | MP3 | 36.153 | 44100/2 | decoded_full_content_unverified | 参考/无独立采样 |
| 苏古笃 | instrument/未知 | MP3 | 13.61 | 48000/1 | decoded_full_content_unverified | phrase |

## 重要发现

笛子.mp3 与 baisha_01.mp3 哈希相同，禁止作为独立笛子音源。其余稳定音高候选只支持 ±3 半音实验性移调；短片段不当作逐音采样。没有完整音域/力度/奏法采样库。

## 分析边界

合奏前 60 秒提取 RMS、频谱重心及低分辨率节拍候选，完整文件另行流式解码验证。未识别具体乐器配合、传统调式、曲名或乐句语义；节拍候选可能有倍频误差。

## 文件详情（含 SHA-256）

### baisha_01

- ID：`3a4cd6a9870d2c0d`
- 路径：`data/music/ensemble/baisha/baisha_01.mp3`
- SHA-256：`2f99883675abc22e71a5a6aa6dc985ca869b0aaafb674683523faae16b6ca543`
- 身份：文件/目录标签，内容待核实
- 用途：风格统计参考，不作为独立乐器音源

### baisha_02

- ID：`b57c6b66d0c7567a`
- 路径：`data/music/ensemble/baisha/baisha_02.mp3`
- SHA-256：`506a517c7a6d68cedd957716ef2d07ca83028d8f376a5304eed4a32244694392`
- 身份：文件/目录标签，内容待核实
- 用途：风格统计参考，不作为独立乐器音源

### dongjing_01

- ID：`fca542f818899860`
- 路径：`data/music/ensemble/dongjing/dongjing_01.mp3`
- SHA-256：`d9cd0ec7cb6d95f40f6d135551a7416dee8fa719e325dab35ab6c338e6ff6b1d`
- 身份：文件/目录标签，内容待核实
- 用途：风格统计参考，不作为独立乐器音源

### dongjing_02

- ID：`3cc9048af86a932d`
- 路径：`data/music/ensemble/dongjing/dongjing_02.mp3`
- SHA-256：`ce344f45f330d49523c2173a696737bd3f3873054abc79e5221e3130d65bfcc1`
- 身份：文件/目录标签，内容待核实
- 用途：风格统计参考，不作为独立乐器音源

### dongjing_03

- ID：`bb4501b6353f6a5b`
- 路径：`data/music/ensemble/dongjing/dongjing_03.mp3`
- SHA-256：`dea4d7997a672baa92368dc1291f761ba4ed2d96b615a6c043f0df2774e31b12`
- 身份：文件/目录标签，内容待核实
- 用途：风格统计参考，不作为独立乐器音源

### 人面竹胡琴

- ID：`a36b2e1aedd40166`
- 路径：`data/music/instruments/人面竹胡琴.mp3`
- SHA-256：`11a1577339ef14a0add995bcca529b3ead25433b5a052a7a0a47d8665359314b`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 十面云锣

- ID：`e1decae571770189`
- 路径：`data/music/instruments/十面云锣.mp3`
- SHA-256：`c7bdf8c2d4866cc0e0fd02b2526188b7eb07bc03a7ddbcd4157a569fff63c197`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 口弦

- ID：`662f1f04b2505d75`
- 路径：`data/music/instruments/口弦.mp3`
- SHA-256：`8cafa3a025947eb710070651b02dcc9573269f327cfc5e7663ef8e91bc385bbb`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 曲项琵琶

- ID：`22217d2f03c9ae8e`
- 路径：`data/music/instruments/曲项琵琶.mp3`
- SHA-256：`f2da95ba7690867e7382b4a50a9a5ad0c01ee925282e44a1a602ce2dea8241fe`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 波伯

- ID：`6750af014e9196df`
- 路径：`data/music/instruments/波伯.mp3`
- SHA-256：`aa08e3dd0b644786a837238dc3fdcf4908ad31cbc57431d528b18d98c08019ed`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 碰铃

- ID：`734d863aecb2a602`
- 路径：`data/music/instruments/碰铃.mp3`
- SHA-256：`b01bb806b81c1cb4e563269ce5647bffecbfaecd2edacc0d8c8149a2dfa88554`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审

### 笛子

- ID：`14000b149dfd6412`
- 路径：`data/music/instruments/笛子.mp3`
- SHA-256：`2f99883675abc22e71a5a6aa6dc985ca869b0aaafb674683523faae16b6ca543`
- 身份：与合奏文件字节完全相同；禁止用作独立乐器音源
- 用途：仅参考；需补充真正独立录音

### 苏古笃

- ID：`596fff7e8137db7c`
- 路径：`data/music/instruments/苏古笃.mp3`
- SHA-256：`d253b035723e3f82391a432fbc1e9b46d3e766c6ae281c14d6ed45d35ddd1075`
- 身份：文件/目录标签，内容待核实
- 用途：有限音高候选或真实片段；待听审
