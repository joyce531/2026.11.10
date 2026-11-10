"""Bounded MIDI and partwise MusicXML parsing; notes use seconds and MIDI pitches."""
from collections import defaultdict, deque
from io import BytesIO
import math
from pathlib import Path
import zipfile

from defusedxml import ElementTree as ET
import mido

MAX_BYTES = 2*1024*1024


def parse_score(data, filename):
    if not data or len(data)>MAX_BYTES:
        raise ValueError('曲谱须非空且不超过 2 MB。')
    suffix = Path(filename).suffix.lower()
    try:
        if suffix in ('.mid','.midi'):
            score = _midi(data)
        elif suffix in ('.xml','.musicxml','.mxl'):
            score = _xml(_unzip(data) if suffix=='.mxl' else data)
        else:
            raise ValueError('仅支持 MIDI、MusicXML/MXL；PDF、图片曲谱识别尚未实现。')
        notes = score['notes']
        if not notes or len(notes)>10000:
            raise ValueError('曲谱没有可用有音高音符，或超过 10000 音符限制。')
        if any(not all(math.isfinite(n[k]) for k in ('start','duration','pitch')) or n['duration']<=0
               or n['start']<0 or not 0<=n['pitch']<=127 for n in notes):
            raise ValueError('曲谱含无效时间或音高。')
        parts = defaultdict(list)
        for n in notes:
            parts[n['part']].append(n)
        # Transparent heuristic, not a claim to have recognized a pop melody.
        melody = max(parts,key=lambda p:(sum(n['pitch'] for n in parts[p])/len(parts[p]),len(parts[p])))
        score.update(melody_part=melody, duration_seconds=round(max(n['start']+n['duration'] for n in notes),3),
                     note_count=len(notes),parts=list(parts),
                     melody=sorted(parts[melody],key=lambda n:(n['start'],-n['pitch'])))
        score['warnings'].append('自动选择平均音高最高的非打击声部作为旋律候选；复杂配器请先导出旋律 MIDI。未识别主歌/副歌等语义结构。')
        return score
    except ValueError:
        raise
    except Exception:
        raise ValueError('曲谱无法安全解析，请检查格式、完整性和支持范围。') from None


def _midi(data):
    midi = mido.MidiFile(file=BytesIO(data))
    if midi.type not in (0,1) or midi.ticks_per_beat<=0:
        raise ValueError('仅支持同步 MIDI 0/1 与 PPQ 时基，不支持 Type 2 或 SMPTE。')
    events=[]
    for i,track in enumerate(midi.tracks):
        tick=0
        for msg in track:
            tick+=msg.time
            events.append((tick,i,msg))
            if len(events)>100000:
                raise ValueError('MIDI 事件过多。')
    events.sort(key=lambda e:e[0])
    active=defaultdict(deque); notes=[]; tempos=[]; meters=[]; markers=[]; warnings=[]
    tempo=500000; seconds=0.; previous=0
    for tick,track,msg in events:
        seconds+=mido.tick2second(tick-previous,midi.ticks_per_beat,tempo);previous=tick
        if seconds>3600:
            raise ValueError('曲谱超过一小时，Demo 请先截取。')
        if msg.type=='set_tempo':
            tempo=msg.tempo
            if tempo<=0:raise ValueError('速度无效。')
            tempos.append({'time':seconds,'bpm':round(mido.tempo2bpm(tempo),3)})
        elif msg.type=='time_signature':
            meters.append({'time':seconds,'beats':msg.numerator,'beat_type':msg.denominator})
        elif msg.type in ('marker','cue_marker'):
            markers.append({'time':seconds,'label':msg.text[:100]})
        elif msg.type in ('note_on','note_off') and msg.channel!=9:
            key=(track,msg.channel,msg.note)
            if msg.type=='note_on' and msg.velocity>0:
                active[key].append((seconds,msg.velocity))
            elif active[key]:
                start,velocity=active[key].popleft()
                if seconds>start:
                    notes.append(dict(start=start,duration=seconds-start,pitch=msg.note,velocity=velocity,part=f'{track}:{msg.channel}'))
        elif msg.type in ('pitchwheel','control_change'):
            if 'MIDI 弯音/控制器（含延音踏板）未渲染，仅解析音符事件。' not in warnings:
                warnings.append('MIDI 弯音/控制器（含延音踏板）未渲染，仅解析音符事件。')
    if any(active.values()):
        raise ValueError('MIDI 有缺失 note_off 的音符，请修复后上传。')
    return dict(notes=notes,tempos=tempos or [{'time':0.,'bpm':120.}],meters=meters,markers=markers,warnings=warnings,format='MIDI')


def _unzip(data):
    with zipfile.ZipFile(BytesIO(data)) as z:
        if len(z.infolist())>100 or sum(i.file_size for i in z.infolist())>MAX_BYTES:
            raise ValueError('MXL 解压大小或文件数超过限制。')
        container=ET.fromstring(z.read('META-INF/container.xml'))
        candidates=[e.get('full-path') for e in container.iter() if e.tag.split('}')[-1]=='rootfile']
        if not candidates:raise ValueError('MXL 缺少主曲谱。')
        return z.read(candidates[0])  # In memory only; never extract user paths.


def _xml(data):
    root=ET.fromstring(data)
    for e in root.iter():
        e.tag=e.tag.split('}')[-1]
    if root.tag!='score-partwise':
        raise ValueError('仅支持 score-partwise MusicXML。')
    # Reject rather than silently play the wrong melody/order.
    unsupported=('repeat','ending','grace','unpitched','microtone','multiple-rest','segno','coda')
    if any(root.find('.//'+tag) is not None for tag in unsupported):
        raise ValueError('当前 MusicXML 不支持反复/跳房/装饰小音符/无音高打击谱等；请在制谱软件展开并导出 MIDI。')
    notes=[]; tempos=[(0.,120.)]; meters=[]; measures=[]; warnings=[]
    stepmap={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
    for pi,part in enumerate(root.findall('part')):
        base=0.; divisions=1.; beats=4; beat_type=4; transpose=0; ties={}
        for measure in part.findall('measure'):
            pos=base; end=base; chord_start=base
            for e in measure:
                if e.tag=='attributes':
                    divisions=float(e.findtext('divisions',str(divisions)))
                    if divisions<=0:raise ValueError('MusicXML divisions 无效。')
                    beats=int(e.findtext('time/beats',str(beats)));beat_type=int(e.findtext('time/beat-type',str(beat_type)))
                    if beats<=0 or beat_type<=0:raise ValueError('拍号无效。')
                    tr=e.find('transpose')
                    if tr is not None:
                        transpose=int(tr.findtext('chromatic','0'))+12*int(tr.findtext('octave-change','0'))
                    if pi==0:meters.append({'beat':base,'beats':beats,'beat_type':beat_type})
                elif e.tag in ('backup','forward'):
                    pos+=float(e.findtext('duration','0'))/divisions*(-1 if e.tag=='backup' else 1)
                    if pos<base-1e-6:raise ValueError('MusicXML 声部回退超出小节。')
                    end=max(end,pos)
                elif e.tag=='direction':
                    sound=e.find('sound'); bpm=sound.get('tempo') if sound is not None else None
                    if sound is not None and any(k in sound.attrib for k in ('dacapo','dalsegno','tocoda','fine')):
                        raise ValueError('请先展开 MusicXML 跳转标记。')
                    if bpm is None:
                        met=e.find('direction-type/metronome')
                        if met is not None:
                            unit={'whole':4,'half':2,'quarter':1,'eighth':.5}.get(met.findtext('beat-unit'))
                            if unit is None:raise ValueError('不支持此节拍器单位。')
                            bpm=float(met.findtext('per-minute'))*unit*(1.5 if met.find('beat-unit-dot') is not None else 1)
                    if bpm is not None:
                        if not 10<=float(bpm)<=600:raise ValueError('MusicXML 速度超出范围。')
                        if pi==0:tempos.append((pos+float(e.findtext('offset','0'))/divisions,float(bpm)))
                elif e.tag=='note':
                    duration=float(e.findtext('duration','0'))/divisions
                    if duration<=0:raise ValueError('音符缺少有效时值。')
                    chord=e.find('chord') is not None
                    start=chord_start if chord else pos
                    if not chord:chord_start=start;pos+=duration
                    end=max(end,start+duration)
                    if e.find('rest') is not None:continue
                    pitch=e.find('pitch')
                    if pitch is None:raise ValueError('音符缺少 pitch。')
                    alter=float(pitch.findtext('alter','0'))
                    if not alter.is_integer():raise ValueError('暂不支持微分音。')
                    number=12*(int(pitch.findtext('octave'))+1)+stepmap[pitch.findtext('step')]+int(alter)+transpose
                    key=(e.findtext('voice','1'),e.findtext('staff','1'),number)
                    types={t.get('type') for t in e.findall('tie')}
                    if 'stop' in types:
                        if key not in ties:raise ValueError('延音线缺少起点。')
                        n=ties[key]
                        if abs(n['start']+n['duration']-start)>.001:raise ValueError('延音线时间不连续。')
                        n['duration']+=duration
                        if 'start' not in types:del ties[key]
                    else:
                        n=dict(start=start,duration=duration,pitch=number,velocity=80,part=f'{pi}:{key[0]}:{key[1]}')
                        notes.append(n)
                        if 'start' in types:ties[key]=n
                    if len(notes)>10000:raise ValueError('音符过多。')
            if pi==0:measures.append({'beat':base,'label':measure.get('number','')})
            base=max(end,base+(0 if measure.get('implicit')=='yes' else beats*4/beat_type))
            if base>100000:raise ValueError('曲谱过长。')
        if ties:raise ValueError('延音线未结束。')
    tempo_map=sorted(dict(tempos).items())
    def seconds(beat):
        total=0.;last=0.;bpm=120.
        for point,value in tempo_map:
            if point>beat:break
            total+=(point-last)*60/bpm;last=point;bpm=value
        return total+(beat-last)*60/bpm
    for n in notes:
        start=seconds(n['start']);stop=seconds(n['start']+n['duration'])
        n.update(start=start,duration=stop-start)
    return dict(notes=notes,tempos=[{'time':seconds(t),'bpm':b} for t,b in tempo_map],
                meters=[{'time':seconds(m['beat']),'beats':m['beats'],'beat_type':m['beat_type']} for m in meters],
                markers=[{'time':seconds(m['beat']),'label':'小节 '+m['label']} for m in measures],
                warnings=warnings,format='MusicXML')


def write_midi(notes, duration, track_names, tempos=None):
    """Use source tempo map; seconds -> ticks keeps MIDI timing aligned with rendered WAV."""
    tempo_map=sorted(tempos or [{'time':0.,'bpm':120.}],key=lambda x:x['time'])
    if not tempo_map or tempo_map[0]['time']>0:tempo_map.insert(0,{'time':0.,'bpm':120.})
    def ticks(second):
        total=0.;last=0.;bpm=120.
        for event in tempo_map:
            if event['time']>second:break
            total+=(event['time']-last)*bpm*8;last=event['time'];bpm=event['bpm']
        return round(total+(second-last)*bpm*8)
    midi=mido.MidiFile(type=1,ticks_per_beat=480)
    meta=mido.MidiTrack();midi.tracks.append(meta);last=0
    for event in tempo_map:
        if event['time']>=duration:break
        t=ticks(event['time']);meta.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(event['bpm']),time=t-last));last=t
    meta.append(mido.MetaMessage('end_of_track',time=max(0,ticks(duration)-last)))
    for index,name in enumerate(track_names):
        track=mido.MidiTrack();midi.tracks.append(track)
        track.append(mido.MetaMessage('track_name',name=name.encode('ascii','replace').decode(),time=0))
        channel=index if index<9 else index+1
        track.append(mido.Message('program_change',program=0,channel=channel,time=0))
        events=[]
        for n in notes:
            if n['track']!=index:continue
            events.extend([(ticks(n['start']),1,n),(ticks(min(duration,n['start']+n['duration'])),0,n)])
        last=0
        for t,on,n in sorted(events,key=lambda e:(e[0],e[1])):
            track.append(mido.Message('note_on' if on else 'note_off',note=n['pitch'],velocity=n['velocity'] if on else 0,channel=channel,time=t-last));last=t
        track.append(mido.MetaMessage('end_of_track',time=max(0,ticks(duration)-last)))
    output=BytesIO();midi.save(file=output);return output.getvalue()
