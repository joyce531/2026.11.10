"""Inspect a provided score image; --recognize invokes the actual selected engine, never Mock."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.score_image import load_score_image,preprocess,classify
from services.score_omr import recognize_jianpu,recognize_staff
from services.score_review import jianpu_rows,preview_audio


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--recognize',action='store_true')
    parser.add_argument('--crop',nargs=4,type=int,help='pixel rectangle after validated loading')
    parser.add_argument('--output',type=Path,default=Path(tempfile.gettempdir())/'naxi-score-omr')
    args=parser.parse_args()
    image=load_score_image(args.source.read_bytes(),args.source.name)
    if args.crop:image=image.crop(tuple(args.crop))
    processed,ink,meta=preprocess(image);detected=classify(ink)
    print(detected,meta,flush=True)
    if not args.recognize:return 0
    if detected['kind']=='unknown':print('Unknown notation; choose type manually in the page.');return 1
    try:doc=recognize_jianpu(processed) if detected['kind']=='jianpu' else recognize_staff(processed)
    except (ValueError,OSError) as exc:print(str(exc));return 1
    args.output.mkdir(parents=True,exist_ok=True)
    processed.save(args.output/'processed.png')
    if 'export_bytes' in doc:(args.output/doc['export_name']).write_bytes(doc['export_bytes'])
    safe={k:v for k,v in doc.items() if k!='export_bytes'}
    (args.output/'recognition.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Engine:',doc['engine'],'coverage:',doc['coverage'],'items:',len(doc.get('tokens',doc.get('rows',[]))),flush=True)
    if doc['notation']=='jianpu':print('Detected key:',doc['tonic_degree'],doc['tonic_note'],'BPM:',doc['bpm'],flush=True)
    print('Unsupported:',doc.get('unsupported_symbols',[]),'Output:',args.output,flush=True)
    print('UNREVIEWED: no MIDI generated; use page for human correction.')
    return 0


if __name__=='__main__':raise SystemExit(main())
