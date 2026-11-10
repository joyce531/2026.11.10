"""Deterministic note arrangement and local sample/auxiliary WAV synthesis."""
from io import BytesIO
import math

import numpy as np
import soundfile as sf

from services.music_library import ROOT, audio_path, read_segment
from services.music_score import write_midi

RATE=22050


def arrange(score, assets, plan, preservation):
    duration=min(30.,score['duration_seconds'])
    melody=[n for n in score['melody'] if n['start']<duration]
    if not melody:raise ValueError('曲谱前 30 秒没有旋律候选。请先截取有音符的片段。')
    notes=[]
    roles=plan['roles']
    lead=next(i for i,r in enumerate(roles) if r['role']=='melody')
    # Deterministic thinning only; high preservation never changes pitch, start, or duration.
    keep=max(1,math.ceil(len(melody)*preservation/100))
    selected=set(np.linspace(0,len(melody)-1,keep,dtype=int).tolist())
    for j,n in enumerate(melody):
        if j in selected:
            notes.append({**n,'duration':min(n['duration'],duration-n['start']),'track':lead})
    for index,role in enumerate(roles):
        if index==lead or role['role']=='phrase':continue
        stride={'sparse':8,'medium':4,'dense':2}[plan['density']]
        for j,n in enumerate(melody):
            if j%stride:continue
            delay=.25 if role['role']=='echo' else 0.
            start=n['start']+delay
            if start>=duration:continue
            pitch=n['pitch']-12 if role['role']=='drone' and n['pitch']>=12 else n['pitch']
            length=min((1.5 if role['role']=='drone' else .18 if role['role']=='pulse' else n['duration']),duration-start)
            notes.append(dict(start=start,duration=length,pitch=pitch,velocity=45,track=index))
    return notes,duration,{'melody_notes_total':len(melody),'melody_notes_retained':keep,
                          'retained_fraction':round(keep/len(melody),3),
                          'method':'均匀保留所选比例的旋律音符；保留音符的音高/起点/时值不改动，附加声部另记。'}


def _envelope(x):
    x=x.copy();fade=min(len(x)//2,220)
    if fade:
        x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
    return x


def _extend(x,length):
    if len(x)<2:return np.zeros(length)
    if length<=len(x):return _envelope(x[:length])
    # Crossfade repeated sample tails; explicitly experimental, not a complete sustain library.
    cross=min(220,len(x)//4);step=len(x)-cross
    out=np.zeros(length+len(x))
    segment=x.copy();segment[:cross]*=np.linspace(0,1,cross);segment[-cross:]*=np.linspace(1,0,cross)
    for start in range(0,length,step):out[start:start+len(x)]+=segment
    return _envelope(out[:length])


def render(notes, duration, assets, plan, root=ROOT):
    mix=np.zeros(round(duration*RATE),dtype=np.float64)
    usage=[];cache={}
    for index,asset in enumerate(assets):
        mapping=asset.get('sample_mapping')
        counts={'asset_id':asset['asset_id'],'label':asset['label'],'sample_notes':0,'auxiliary_notes':0,'phrases':0,
                'sample_status':mapping['status'] if mapping else '不可用 / 辅助音源',
                'identity_status':asset['identity_status']}
        try:
            if mapping:
                cache[index]=read_segment(audio_path(asset['path'],root),mapping['start_seconds'],mapping['duration_seconds'],RATE)
                # Check file identity: stale DB never silently synthesizes from a replaced original.
                import hashlib
                if hashlib.sha256(audio_path(asset['path'],root).read_bytes()).hexdigest()!=asset['sha256']:
                    raise ValueError('素材已变化，请重新扫描素材库。')
        except (OSError,RuntimeError):
            cache.pop(index,None);counts['sample_status']='读取失败 / 辅助音源'
        for n in [n for n in notes if n['track']==index]:
            length=max(1,round(n['duration']*RATE));start=round(n['start']*RATE)
            x=None
            if mapping and mapping['mode']=='limited_pitch' and index in cache:
                semitones=n['pitch']-mapping['root_midi']
                if abs(semitones)<=mapping['max_semitones']:
                    raw=cache[index];factor=2**(semitones/12)
                    shifted=np.interp(np.arange(0,len(raw)-1,factor),np.arange(len(raw)),raw)
                    x=_extend(shifted,length);counts['sample_notes']+=1
            if x is None:
                t=np.arange(length)/RATE;hz=440*2**((n['pitch']-69)/12)
                # Clearly labelled generic auxiliary, never imitating a named traditional instrument.
                x=_envelope((np.sin(2*np.pi*hz*t)+.2*np.sin(4*np.pi*hz*t))*np.exp(-1.7*t))
                counts['auxiliary_notes']+=1
            peak=np.abs(x).max(initial=0)
            if peak:x=x/peak*.22*(n['velocity']/100)
            count=min(len(x),len(mix)-start)
            if count>0:mix[start:start+count]+=x[:count]
        if mapping and mapping['mode']=='phrase' and index in cache:
            # One original excerpt as an accent, never pitch-labelled or counted as MIDI notes.
            x=_envelope(cache[index]);peak=np.abs(x).max(initial=0)
            if peak:x=x/peak*.09
            start=round(min(duration*.5,max(0,duration-len(x)/RATE))*RATE)
            count=min(len(x),len(mix)-start)
            if count>0:mix[start:start+count]+=x[:count];counts['phrases']=1
        usage.append(counts)
    peak=np.abs(mix).max(initial=0)
    if peak<1e-8:raise ValueError('未产生可听音频，请检查曲谱。')
    mix*=.88/max(.88,peak)
    buffer=BytesIO();sf.write(buffer,mix,RATE,format='WAV',subtype='PCM_16')
    return buffer.getvalue(),usage


def produce(score,assets,plan,preservation,root=ROOT):
    notes,duration,retention=arrange(score,assets,plan,preservation)
    wav,usage=render(notes,duration,assets,plan,root)
    midi=write_midi(notes,duration,[a['asset_id'] for a in assets],score['tempos'])
    return dict(midi=midi,wav=wav,usage=usage,duration_seconds=duration,retention=retention,
                note_count=len(notes),sample_rate=RATE,
                midi_note='MIDI 保存音符与速度，通用播放器使用自己的 GM 音色；真实录音片段只在 WAV 中，未嵌入 MIDI。')
