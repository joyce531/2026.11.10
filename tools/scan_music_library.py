"""Scan existing directories; write only metadata database, manifest and report."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.music_library import ROOT, scan_library


def main():
    rows=scan_library()
    (ROOT/'data/music/music_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 音乐素材扫描报告','',
           '实际逐块解码所有文件；无音频上传、复制、移动或修改。名称/类别仅为目录标签，未据文件名确认声音身份。',
           '','| 标签 | 类型/类别 | 格式 | 时长(s) | 采样率/声道 | 解码 | 采样用途 |','|---|---|---|---:|---|---|---|']
    for r in rows:
        mapping=r.get('sample_mapping') or {}
        lines.append(f"| {r['label']} | {r['material_type']}/{r['category']} | {r.get('format',r['extension'])} | {r.get('duration_seconds','—')} | {r.get('sample_rate','—')}/{r.get('channels','—')} | {r['analysis_status']} | {mapping.get('mode','参考/无独立采样')} |")
    lines+=['','## 重要发现','',
            '笛子.mp3 与 baisha_01.mp3 哈希相同，禁止作为独立笛子音源。其余稳定音高候选只支持 ±3 半音实验性移调；短片段不当作逐音采样。没有完整音域/力度/奏法采样库。',
            '','## 分析边界','',
            '合奏前 60 秒提取 RMS、频谱重心及低分辨率节拍候选，完整文件另行流式解码验证。未识别具体乐器配合、传统调式、曲名或乐句语义；节拍候选可能有倍频误差。',
            '','## 文件详情（含 SHA-256）','']
    for r in rows:
        lines += [f"### {r['label']}",'',f"- ID：`{r['asset_id']}`",f"- 路径：`{r['path']}`",f"- SHA-256：`{r['sha256']}`",f"- 身份：{r['identity_status']}",f"- 用途：{r['purpose']}",'']
    (ROOT/'docs/MUSIC_ASSET_INVENTORY.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Scanned {len(rows)} files; decoded {sum(r["analysis_status"].startswith("decoded") for r in rows)}')


if __name__=='__main__':main()
