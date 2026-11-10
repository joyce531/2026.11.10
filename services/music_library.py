"""Read-only audio analysis; SQLite metadata and limited sample maps, never edit originals."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/music/music_library.sqlite3'
DIRECTORIES = ('data/music/ensemble/baisha', 'data/music/ensemble/dongjing', 'data/music/instruments')


def audio_path(relative, root=ROOT):
    path = (root / relative).resolve()
    if not path.is_relative_to((root / 'data/music').resolve()) or not path.is_file():
        raise ValueError('音乐素材路径无效或文件缺失。')
    return path


def read_segment(path, start=0, duration=1, rate=22050):
    with sf.SoundFile(path) as f:
        f.seek(min(max(0, round(start*f.samplerate)), len(f)))
        samples = f.read(round(duration*f.samplerate), dtype='float32', always_2d=True).mean(axis=1)
        source_rate = f.samplerate
    if not len(samples):
        return np.zeros(0, dtype=np.float32)
    if source_rate != rate:
        samples = np.interp(np.arange(round(len(samples)*rate/source_rate))*source_rate/rate,
                            np.arange(len(samples)), samples).astype(np.float32)
    return samples


def pitch_frame(samples, rate=11025):
    """Autocorrelation candidate, NOT instrument/content recognition."""
    x = samples.astype(float) - samples.mean()
    if np.sqrt(np.mean(x*x)) < .008:
        return None
    x *= np.hanning(len(x))
    spectrum = np.fft.rfft(x, n=2*len(x))
    ac = np.fft.irfft(spectrum*spectrum.conj())[:len(x)]
    lo, hi = int(rate/1200), min(int(rate/70), len(x)//2)
    peaks = [i for i in range(lo+1,hi-1) if ac[i] >= ac[i-1] and ac[i] > ac[i+1]]
    if not peaks or ac[0] <= 0:
        return None
    best = max(peaks,key=lambda i:ac[i])
    confidence = float(ac[best]/ac[0])
    if confidence < .78:
        return None
    offset = .5*(ac[best-1]-ac[best+1])/(ac[best-1]-2*ac[best]+ac[best+1]+1e-12)
    midi = 69+12*np.log2((rate/(best+offset))/440)
    return float(midi), confidence


def analyze(path, kind):
    # Full streaming decode verifies every block; feature and candidate analysis uses first 60 s.
    with sf.SoundFile(path) as f:
        meta = dict(duration_seconds=round(len(f)/f.samplerate,3), sample_rate=f.samplerate,
                    channels=f.channels, format=f.format, subtype=f.subtype)
        frames, peak, total = 0, 0., 0.
        for block in f.blocks(blocksize=65536,dtype='float32',always_2d=True):
            if not np.isfinite(block).all():
                raise ValueError('音频包含非有限数值。')
            frames += len(block)
            peak = max(peak,float(np.abs(block).max(initial=0)))
            total += float(np.square(block.astype(float)).sum())
        if frames != len(f) or not frames:
            raise ValueError('音频未完整解码或为空。')
    x = read_segment(path,0,min(60,meta['duration_seconds']),11025)
    hop = 1102
    envelope = np.array([np.sqrt(np.mean(x[i:i+hop]**2)) for i in range(0,len(x),hop)])
    onset = np.maximum(np.diff(envelope),0)
    pulse = None
    if len(onset)>40 and onset.max(initial=0)>.002:
        centered = onset-onset.mean()
        ac = np.correlate(centered,centered,mode='full')[len(centered)-1:]
        lag = max(range(4,16),key=lambda i:ac[i])
        pulse = round(60/(lag*hop/11025),1)
    spectral = np.abs(np.fft.rfft(x[:min(len(x),11025*10)]))
    hz = np.fft.rfftfreq(min(len(x),11025*10),1/11025)
    meta['features'] = {'rms':round(np.sqrt(total/(frames*meta['channels'])),5),'peak':round(peak,5),
                        'spectral_centroid_hz':round(float((spectral*hz).sum()/(spectral.sum()+1e-12)),1),
                        'pulse_bpm_candidate':pulse,'window_seconds':min(60,meta['duration_seconds']),
                        'caution':'自动声学统计，不等于曲种鉴定；节拍候选可能有倍频/半频误差。'}
    mapping = None
    if kind == 'instrument':
        # Require several consecutive stable voiced frames; limit pitch shifting to +/- 3 semitones.
        for start in np.arange(0,max(0,len(x)/11025-.55),.15):
            estimates = [pitch_frame(x[int((start+offset)*11025):int((start+offset+.1)*11025)])
                         for offset in (0,.1,.2,.3)]
            if all(e is not None for e in estimates):
                pitches = np.array([e[0] for e in estimates])
                if pitches.std() < .18 and 35 <= pitches.mean() <= 95:
                    mapping = dict(mode='limited_pitch',start_seconds=round(float(start),3),duration_seconds=.45,
                                   root_midi=round(float(pitches.mean()),3),max_semitones=3,
                                   confidence=round(min(e[1] for e in estimates),3),
                                   status='automatic_candidate_unverified',
                                   note='自动稳定音高候选；未核实单音纯净度和乐器身份，不是完整可演奏音源。')
                    break
        if mapping is None and peak>.01:
            # A real recording excerpt, not a note sample; do not pitch or label it a known phrase.
            index = int(np.argmax(envelope))
            mapping = dict(mode='phrase',start_seconds=round(max(0,index*.1-.1),3),
                           duration_seconds=min(2.,meta['duration_seconds']),root_midi=None,max_semitones=0,
                           status='automatic_excerpt_unverified',note='原录音短片段，内容待听审；不作为逐音音源。')
    return meta, mapping


def scan_library(root=ROOT, db=DB):
    records = []
    for directory in DIRECTORIES:
        folder = root/directory
        if not folder.exists():
            continue
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            kind = 'instrument' if directory.endswith('instruments') else 'ensemble'
            row = dict(asset_id=hashlib.sha256(relative.encode()).hexdigest()[:16],path=relative,
                       label=path.stem,material_type=kind,
                       category=('未知' if kind=='instrument' else '白沙' if '/baisha' in directory else '洞经'),
                       instrument_name=path.stem if kind=='instrument' else None,
                       identity_status='文件/目录标签，内容待核实',extension=path.suffix.lower(),
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       purpose='风格统计参考，不作为独立乐器音源' if kind=='ensemble' else '有限音高候选或真实片段；待听审',
                       analysis_status='failed',sample_mapping=None)
            try:
                meta,mapping = analyze(path,kind)
                row.update(meta,analysis_status='decoded_full_content_unverified',sample_mapping=mapping)
            except (ValueError,RuntimeError,OSError):
                row['error']='无法完整解码；不参与编排，请检查音频格式或文件。'
            records.append(row)
    for row in records:
        duplicates = [r['asset_id'] for r in records if r['asset_id']!=row['asset_id'] and r['sha256']==row['sha256']]
        row['duplicates'] = duplicates
        if row['material_type']=='instrument' and any(r['material_type']=='ensemble' and r['sha256']==row['sha256'] for r in records):
            row['sample_mapping'] = None
            row['identity_status'] = '与合奏文件字节完全相同；禁止用作独立乐器音源'
            row['purpose'] = '仅参考；需补充真正独立录音'
    db.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(db)) as conn,conn:
        conn.execute('CREATE TABLE IF NOT EXISTS assets (asset_id TEXT PRIMARY KEY, path TEXT UNIQUE, metadata_json TEXT NOT NULL)')
        for row in records:
            conn.execute('INSERT OR REPLACE INTO assets VALUES (?,?,?)',(row['asset_id'],row['path'],json.dumps(row,ensure_ascii=False)))
    return records


def list_assets(db=DB):
    if not Path(db).exists():
        return []
    with closing(sqlite3.connect(db)) as conn:
        return [json.loads(r[0]) for r in conn.execute('SELECT metadata_json FROM assets ORDER BY path')]


def find_asset(asset_id, db=DB):
    row = next((r for r in list_assets(db) if r['asset_id']==asset_id),None)
    if row is None:
        raise ValueError('素材 ID 不存在，请重新扫描音乐库。')
    return row
