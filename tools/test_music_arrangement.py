"""Generate a clearly labelled synthetic 30-second pipeline check, or use --score PATH."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.music_library import list_assets
from services.music_score import write_midi
from services.music_service import arrange_music


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score',type=Path)
    parser.add_argument('--live',action='store_true',help='One paid OpenAI planning request; no audio upload')
    parser.add_argument('--output',type=Path,default=Path(tempfile.gettempdir())/'naxi-music-m5-demo')
    args=parser.parse_args()
    if args.score:
        data=args.score.read_bytes();name=args.score.name
    else:
        notes=[dict(start=i*.5,duration=.5,pitch=[64,67,69,67,64,62,60,62][i%8],velocity=80,track=0) for i in range(60)]
        data=write_midi(notes,30,['synthetic-pipeline-test']);name='synthetic-test.mid'
    ids=[a['asset_id'] for a in list_assets() if a['label'] in ('人面竹胡琴','曲项琵琶','口弦')]
    result=arrange_music(data,name,ids,'洞经音乐',100,real=args.live)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'input.mid' if not args.score else args.output/('input'+args.score.suffix)).write_bytes(data)
    (args.output/'arrangement.mid').write_bytes(result['midi'])
    (args.output/'arrangement.wav').write_bytes(result['wav'])
    report={k:v for k,v in result.items() if k not in ('midi','wav')}
    report['fixture_notice']='用户提供曲谱' if args.score else '人工非歌曲测试旋律，不是流行歌曲或纳西传统曲目'
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Mode:',result['mode'],'duration:',result['duration_seconds'],'output:',args.output)
    for row in result['usage']:print(row['label'],'sample',row['sample_notes'],'auxiliary',row['auxiliary_notes'],'phrase',row['phrases'])
    if args.live and result['mode']!='openai_plan':
        print(result['fallback_reason']);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
