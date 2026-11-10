"""Editable absolute-note draft, key-aware jianpu conversion, confirmation gate."""
import hashlib
import json
import math
from services.music_score import write_midi
from services.music_render import render

SEMITONES={'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
SCALE=(0,2,4,5,7,9,11)


def jianpu_rows(document,tonic,reference_degree,octave,bpm):
    if tonic not in SEMITONES:raise ValueError('调号未知：请明确 1=A 或 6=A 等调性，不会默认 1=C。')
    if reference_degree not in range(1,8) or octave not in range(1,7) or not 20<=bpm<=300:
        raise ValueError('调号参考级数、八度或速度无效。')
    root=12*(octave+1)+SEMITONES[tonic]-SCALE[reference_degree-1]
    rows=[];beat=0.;measure=1;pending_tie=False
    for i,t in enumerate(document['tokens']):
        if t['kind']=='barline':measure+=1;continue
        duration=t['base_beats']*(2-2**(-t['dots'])) if t['base_beats'] is not None else None
        pitch=None;rest=t['kind']=='rest'
        if t['kind']=='note' and t['degree'] is not None:
            pitch=root+SCALE[t['degree']-1]+12*t['octave_shift']+t['accidental']
        issue=t['issue'];uncertain=t['confidence']!='high' or t['kind']=='unknown' or duration is None
        if t['kind']=='extend':
            if rows and duration is not None and rows[-1]['duration'] is not None and not rows[-1]['rest']:
                rows[-1]['duration']+=duration*60/bpm
                rows[-1]['symbol']+=' —'
                rows[-1]['uncertain'] |= uncertain
                rows[-1]['issue']+=' '+issue
                if beat is not None:beat+=duration
                continue
            uncertain=True;issue+=' 无有效前音的延长线，需手工校正。'
        if pending_tie:
            if rows and rows[-1]['pitch']==pitch and pitch is not None and duration is not None and rows[-1]['duration'] is not None:
                rows[-1]['duration']+=duration*60/bpm
                rows[-1]['uncertain'] |= uncertain;rows[-1]['symbol']+=' (延音)'
                pending_tie=t['tie_to_next']
                if beat is not None:beat+=duration
                continue
            uncertain=True;issue+=' 延音线连接不同/未知音高。'
        rows.append({'start':round(beat*60/bpm,6) if beat is not None else None,
                     'duration':round(duration*60/bpm,6) if duration is not None else None,
                     'pitch':pitch,'rest':rest,'voice':'melody',
                     'symbol':f"小节{measure} #{i+1} {t['degree'] if t['kind']=='note' else t['kind']} octave={t['octave_shift']} dots={t['dots']}",
                     'uncertain':uncertain,'issue':issue,'reviewed':False})
        beat=beat+duration if beat is not None and duration is not None else None
        pending_tie=t['tie_to_next']
    if pending_tie and rows:
        rows[-1]['uncertain']=True;rows[-1]['issue']+=' 末尾延音线未闭合。'
    return rows


def validate_rows(rows, require_review=False):
    if not isinstance(rows,list) or not 1<=len(rows)<=2000:raise ValueError('草稿须含 1–2000 个事件。')
    notes=[];voices=[]
    for i,r in enumerate(rows,1):
        for k in ('start','duration'):
            v=r.get(k)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                raise ValueError(f'第 {i} 行 {k} 未确定，请补正。')
        if r['start']<0 or r['duration']<=0 or r['start']+r['duration']>600:
            raise ValueError(f'第 {i} 行时间无效；本版最多 10 分钟。')
        if require_review and r.get('uncertain',True) and not r.get('reviewed',False):
            raise ValueError(f'第 {i} 行有不确定标记，尚未勾选已校对。')
        voice=str(r.get('voice','melody'))
        if voice not in voices:voices.append(voice)
        if len(voices)>15:raise ValueError('声部数超过 15。')
        if r.get('rest'):continue
        pitch=r.get('pitch')
        if isinstance(pitch,bool) or not isinstance(pitch,(int,float)) or not math.isfinite(pitch) or int(pitch)!=pitch or not 0<=pitch<=127:
            raise ValueError(f'第 {i} 行音高未确定或不是 0–127 整数。')
        notes.append(dict(start=float(r['start']),duration=float(r['duration']),pitch=int(pitch),velocity=80,track=voices.index(voice)))
    if not notes:raise ValueError('没有可试听的有音高音符。')
    return notes,voices,max(r['start']+r['duration'] for r in rows)


def review_hash(rows,tempos):
    return hashlib.sha256(json.dumps([rows,tempos],sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def preview_audio(rows):
    notes,voices,duration=validate_rows(rows)
    notes=[{**n,'track':0,'duration':min(n['duration'],30-n['start'])} for n in notes if n['start']<30]
    if not notes:raise ValueError('前30秒没有有声事件。')
    # Reuse the existing renderer, auxiliary timbre only, no MIDI before confirmation.
    asset={'asset_id':'review','label':'校对辅助音','sample_mapping':None,'identity_status':'通用合成音，不是纳西乐器'}
    return render(notes,min(30,duration),[asset],{})[0]


def confirm_midi(rows,tempos,*,confirmed=False,limitations_accepted=False,has_limitations=False):
    if not confirmed:raise ValueError('请先确认已校对，再生成 MIDI。')
    if has_limitations and not limitations_accepted:raise ValueError('请确认片段范围和不支持符号的处理，或裁剪重识别。')
    notes,voices,duration=validate_rows(rows,require_review=True)
    return write_midi(notes,duration,voices,tempos)
