"""默认 Mock；--live 才请求模型。仅测试自同图/缩放副本与无关几何图，不保存学习记录。"""
import argparse
from pathlib import Path
import sys
from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from naxi_agents.dongba_agent import DongbaHandwritingAgent
from services.dongba_vision import EvaluationError
from tools.dongba_tools import get_reference_character


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    _,reference=get_reference_character('dongba_01')
    wrong=Image.new('RGB',(480,480),'white')
    ImageDraw.Draw(wrong).rectangle((80,80,400,400),outline='black',width=12)
    agent=DongbaHandwritingAgent(mock=not args.live)
    try:
        for label,image in [('reference_scaled',reference.resize((448,300))),('unrelated_rectangle',wrong)]:
            result=agent.evaluate('dongba_01',image,'photo_upload')
            print(label,result['source'],result['model'],result['status'],result['similarity_score'],flush=True)
            print(result['overall_feedback'],flush=True)
            print(result['tool_trace'],flush=True)
            if args.live and result['source'] != 'openai_responses':
                print('FAIL: real API unavailable; fallback:',result.get('fallback_reason','quality check'))
                return 1
            expected=('match','close') if label=='reference_scaled' else ('incorrect','uncertain')
            if result['status'] not in expected:
                print('FAIL: baseline classification did not meet expectation')
                return 1
    except EvaluationError as exc:
        print(str(exc));return 1
    print('PASS: target-conditioned baseline smoke test (not real handwriting accuracy)')
    return 0


if __name__=='__main__':raise SystemExit(main())
