import base64
from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFilter
from components.handwriting_canvas import decode_canvas
from naxi_agents.dongba_agent import DongbaHandwritingAgent
from services.dongba_vision import EvaluationError, parse_result, create_client, request
from services.glyph_data import GlyphDataService
from services.learning_records import LearningRecords
from services.handwriting_quality import inspect_image
from tools.dongba_tools import get_reference_character
from tools.upload_validation import prepare_image


def setUpModule():
    patcher=patch('services.qwen_service.enabled',return_value=False)
    patcher.start();unittest.addModuleCleanup(patcher.stop)


def response_json(status='match'):
    return {'status':status,'similarity_score':95,'overall_feedback':'整体轮廓接近。',
            'differences':[],
            'improvement_suggestions':['保持顶部轮廓与下部线条的相对位置。'],'confidence':'medium'}


class FakeClient:
    def __init__(self, status='match'):
        self.calls=[]
        self.responses=self
        self.status=status

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(status='completed',output=[],output_text=json.dumps(response_json(self.status)))


class AgentTests(unittest.TestCase):
    def setUp(self):
        _,self.ref=get_reference_character('dongba_01')
        self.clear=self.ref.resize((448,300))
        self.wrong=Image.new('RGB',(480,480),'white')
        ImageDraw.Draw(self.wrong).rectangle((80,80,400,400),outline='black',width=12)

    def test_mock_clear_upload(self):
        data=BytesIO();self.clear.save(data,format='JPEG')
        image,_=prepare_image(data.getvalue(),'test.jpg')
        with patch('naxi_agents.dongba_agent.create_client',side_effect=AssertionError('no network')):
            result=DongbaHandwritingAgent(mock=True).evaluate('dongba_01',image,'photo_upload')
        self.assertIn(result['status'],('match','close'))
        self.assertEqual(result['source'],'mock')
        self.assertTrue(result['improvement_suggestions'])

    def test_canvas_payload_and_invalid_tracks(self):
        data=BytesIO();self.clear.save(data,format='PNG')
        payload={'png':'data:image/png;base64,'+base64.b64encode(data.getvalue()).decode(),
                 'version':1,'width':640,'height':480,'submission_id':'test',
                 'strokes':[{'width':10,'color':'#233d4a','points':[[1,2],[20,30]]}]}
        result=DongbaHandwritingAgent(mock=True).evaluate('dongba_01',decode_canvas(payload),'online_canvas')
        self.assertEqual(result['input_method'],'online_canvas')
        payload['strokes'][0]['points']=[[float('nan'),0]]
        with self.assertRaises(ValueError):decode_canvas(payload)

    def test_blank_dark_blur_and_tiny_no_network(self):
        tiny=Image.new('RGB',(480,480),'white');ImageDraw.Draw(tiny).rectangle((20,20,24,24),fill='black')
        for image in (Image.new('RGB',(480,480),'white'),Image.new('RGB',(480,480),'black'),
                      self.clear.filter(ImageFilter.GaussianBlur(15)),tiny):
            with self.subTest(size=image.size),patch('naxi_agents.dongba_agent.create_client',side_effect=AssertionError('no network')):
                result=DongbaHandwritingAgent().evaluate('dongba_01',image,'photo_upload')
                self.assertEqual(result['status'],'uncertain')
                self.assertEqual(result['source'],'quality_check')

    def test_unrelated_drawing(self):
        line=Image.new('RGB',(480,480),'white')
        ImageDraw.Draw(line).line((50,240,430,240),fill='black',width=12)
        self.assertTrue(inspect_image(line)[0]['usable'])
        self.assertEqual(DongbaHandwritingAgent(mock=True).evaluate('dongba_01',line,'photo_upload')['status'],'incorrect')
        result=DongbaHandwritingAgent(mock=True).evaluate('dongba_01',self.wrong,'photo_upload')
        self.assertEqual(result['status'],'incorrect')
        self.assertIn('无法判定为正确临摹',result['overall_feedback'])

    def test_missing_reference_stops_before_api(self):
        with patch('naxi_agents.dongba_agent.create_client',side_effect=AssertionError('no network')):
            with self.assertRaises(EvaluationError):
                DongbaHandwritingAgent().evaluate('missing',self.clear,'photo_upload')
            with patch.object(GlyphDataService,'load_reference_image',return_value=SimpleNamespace(image=None,messages=['文件不存在'])):
                with self.assertRaises(EvaluationError):
                    DongbaHandwritingAgent().evaluate('dongba_01',self.clear,'photo_upload')

    def test_missing_key(self):
        with patch('services.dongba_vision.settings',return_value=('','gpt-6-luna')):
            with self.assertRaisesRegex(EvaluationError,'OPENAI_API_KEY'):create_client()

    def test_single_request_and_two_image_payload(self):
        client=FakeClient()
        result=DongbaHandwritingAgent(client=client).evaluate('dongba_01',self.clear,'photo_upload')
        self.assertEqual(result['source'],'openai_responses')
        self.assertEqual(len(client.calls),1)
        content=client.calls[0]['input'][0]['content']
        self.assertEqual(len([v for v in content if v['type']=='input_image']),2)
        self.assertTrue(all(v['image_url'].startswith('data:image/png;base64,') for v in content if v['type']=='input_image'))
        self.assertFalse(client.calls[0]['store'])
        self.assertFalse(client.calls[0]['stream'])
        self.assertNotIn('tools',client.calls[0])
        self.assertEqual(set(client.calls[0]['text']['format']['schema']['required']),set(response_json()))

    def test_automatic_fallback_without_retry(self):
        with patch('naxi_agents.dongba_agent.create_client',side_effect=EvaluationError('Missing API Key')):
            result=DongbaHandwritingAgent().evaluate('dongba_01',self.clear,'photo_upload')
        self.assertEqual(result['source'],'mock')
        self.assertIn('Missing',result['fallback_reason'])
        for response in (RuntimeError('private-secret'),SimpleNamespace(status='failed',output_text=''),
                         SimpleNamespace(status='completed',output_text='bad json')):
            client=FakeClient()
            kwargs={'side_effect':response} if isinstance(response,Exception) else {'return_value':response}
            with patch.object(client,'create',**kwargs) as call:
                result=DongbaHandwritingAgent(client=client).evaluate('dongba_01',self.clear,'online_canvas')
            self.assertEqual(call.call_count,1)
            self.assertEqual(result['source'],'mock')
            self.assertTrue(result['mock_mode'])
            self.assertNotIn('private-secret',result['fallback_reason'])

    def test_real_ai_config(self):
        from services.dongba_vision import use_real_ai
        with patch('services.dongba_vision.dotenv_values',return_value={'USE_REAL_AI':'true'}), patch.dict('os.environ',{},clear=True):
            self.assertTrue(use_real_ai())
            with patch.dict('os.environ',{'USE_REAL_AI':'false'}):
                self.assertFalse(use_real_ai())
        with patch('services.dongba_vision.dotenv_values',return_value={}), patch.dict('os.environ',{},clear=True):
            self.assertFalse(use_real_ai())

    def test_failed_request_and_invalid_json(self):
        client=FakeClient()
        with patch.object(client,'create',side_effect=RuntimeError('private-value')):
            with self.assertRaises(EvaluationError) as caught:request(client,model='test')
            self.assertNotIn('private-value',str(caught.exception))
        for text in ('not json',json.dumps({**response_json(),'status':'yes'}),json.dumps({**response_json(),'similarity_score':101}),
                     json.dumps({**response_json(),'improvement_suggestions':[]})):
            with self.assertRaises(EvaluationError):parse_result(text)

    def test_save_and_idempotency(self):
        result=DongbaHandwritingAgent(mock=True).evaluate('dongba_01',self.clear,'photo_upload',submission_id='fixed')
        with tempfile.TemporaryDirectory() as directory:
            store=LearningRecords(Path(directory)/'records.sqlite3')
            store.save(result);store.save(result)
            self.assertEqual(len(store.recent()),1)
            self.assertEqual(store.recent()[0]['character_id'],'dongba_01')
            self.assertNotIn('image',store.recent()[0])

    def test_original_unchanged_and_exif(self):
        original=self.clear.tobytes()
        _,prepared=inspect_image(self.clear)
        self.assertEqual(prepared.size,(512,512))
        self.assertEqual(self.clear.tobytes(),original)
        exif=Image.Exif();exif[274]=6
        buffer=BytesIO();self.clear.save(buffer,format='JPEG',exif=exif)
        oriented,_=prepare_image(buffer.getvalue(),'photo.jpeg')
        self.assertEqual(oriented.size,(300,448))


if __name__=='__main__':unittest.main()
