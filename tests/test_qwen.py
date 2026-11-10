"""Offline contracts only. No real API or model IDs used by tests."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PIL import Image
from openai import APIConnectionError
import httpx2 as httpx

from services import qwen_service as q
from services.dongba_vision import EvaluationError, SCHEMA
from services.score_omr import recognize_jianpu, recognize_staff_vision
from services.score_review import preview_audio
from naxi_agents.dongba_agent import DongbaHandwritingAgent
from naxi_agents.music_agent import MusicArrangementAgent, local_plan
from services.music_library import list_assets
from services.music_score import parse_score
from tools.dongba_tools import get_reference_character
from tests.test_music import fixture_midi
from tests.test_score_omr import document


def client_for(data):
    client=Mock()
    client.chat.completions.create.return_value=SimpleNamespace(choices=[SimpleNamespace(
        finish_reason='stop',message=SimpleNamespace(content=json.dumps(data)))])
    return client


class QwenTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'AI_PROVIDER':'qwen','USE_REAL_AI':'true',
            'DASHSCOPE_API_KEY':'unit-test-not-a-key','DASHSCOPE_BASE_URL':'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'QWEN_TEXT_MODEL':'unit-text','QWEN_VISION_MODEL':'unit-vision'})
        self.env.start();self.addCleanup(self.env.stop)

    def test_missing_models_and_endpoint_validation(self):
        with patch.dict(os.environ,{'QWEN_TEXT_MODEL':''}):
            with self.assertRaisesRegex(EvaluationError,'QWEN_TEXT_MODEL'):q.configuration('text')
        for url in ('https://example.com/compatible-mode/v1','http://dashscope.aliyuncs.com/compatible-mode/v1',
                    'https://dashscope.aliyuncs.com:bad/compatible-mode/v1'):
            with patch.dict(os.environ,{'DASHSCOPE_BASE_URL':url}):
                with self.assertRaises(EvaluationError):q.configuration('vision')
        with patch.dict(os.environ,{'DASHSCOPE_BASE_URL':'https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1'}):
            self.assertEqual(q.configuration('vision')[2],'unit-vision')

    def test_single_call_dual_images_and_no_client_close(self):
        c=client_for({'ok':True})
        schema={'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok']}
        result,model=q.request_json(kind='vision',instructions='Compare',schema=schema,
            images=(Image.new('RGB',(10,10)),Image.new('RGB',(10,10))),client=c)
        self.assertTrue(result['ok']);self.assertEqual(model,'unit-vision')
        c.chat.completions.create.assert_called_once();c.close.assert_not_called()
        kw=c.chat.completions.create.call_args.kwargs
        self.assertFalse(kw['stream']);self.assertFalse(kw['extra_body']['enable_thinking'])
        self.assertEqual(len([i for i in kw['messages'][1]['content'] if i['type']=='image_url']),2)
        self.assertEqual(kw['response_format'],{'type':'json_object'})
        self.assertNotIn('max_tokens',kw)

    def test_invalid_json_truncation_and_network_errors(self):
        c=client_for({});c.chat.completions.create.return_value.choices[0].message.content='not json'
        with self.assertRaises(EvaluationError):q.request_json(kind='text',instructions='',schema={},client=c)
        c=client_for({});c.chat.completions.create.return_value.choices[0].finish_reason='length'
        with self.assertRaisesRegex(EvaluationError,'被截断'):q.request_json(kind='text',instructions='',schema={},client=c)
        c=client_for({});c.chat.completions.create.side_effect=APIConnectionError(request=httpx.Request('POST','https://example.com'))
        with self.assertRaisesRegex(EvaluationError,'网络连接'):q.request_json(kind='text',instructions='',schema={},client=c)
        c.chat.completions.create.assert_called_once()

    def test_dongba_source_and_labelled_mock_fallback(self):
        _,im=get_reference_character('dongba_01')
        result=dict(status='incorrect',similarity_score=12,overall_feedback='轮廓差异明显',
            differences=['下部位置不同'],improvement_suggestions=['先核对下部宽度'],confidence='high')
        c=client_for(result)
        out=DongbaHandwritingAgent(client=c).evaluate('dongba_01',im,'photo_upload')
        self.assertEqual(out['source'],'qwen_vision');self.assertFalse(out['mock_mode'])
        self.assertEqual(out['similarity_score'],12)
        c.chat.completions.create.side_effect=RuntimeError('do not expose secret')
        fallback=DongbaHandwritingAgent(client=c).evaluate('dongba_01',im,'photo_upload')
        self.assertEqual(fallback['source'],'mock')
        self.assertTrue(fallback['mock_mode'])
        self.assertTrue(fallback['fallback_reason'])
        self.assertNotIn('secret',fallback['fallback_reason'])

    def test_text_route_is_plain_text_and_rejects_images(self):
        c=client_for({'ok':True})
        schema={'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok']}
        q.request_json(kind='text',instructions='Return JSON',schema=schema,text='only metadata',client=c)
        kw=c.chat.completions.create.call_args.kwargs
        self.assertEqual(kw['model'],'unit-text')
        self.assertNotIn('max_tokens',kw)
        self.assertIsInstance(kw['messages'][1]['content'],str)
        self.assertNotIn('image_url',json.dumps(kw))
        with self.assertRaisesRegex(EvaluationError,'只接受文本'):
            q.request_json(kind='text',instructions='Return JSON',schema=schema,
                           images=(Image.new('RGB',(10,10)),),client=c)
        c.chat.completions.create.assert_called_once()
        with patch.dict(os.environ,{'QWEN_VISION_MODEL':'auto-model-some-route'}):
            with self.assertRaisesRegex(EvaluationError,'不能使用文本智能路由'):
                q.configuration('vision')

    def test_jianpu_key_and_uncertainty(self):
        c=client_for(document())
        out=recognize_jianpu(Image.new('RGB',(100,100)),c)
        self.assertEqual(out['engine'],'qwen_vision');self.assertEqual(out['tonic_note'],'A')
        self.assertEqual(c.chat.completions.create.call_count,1)
        self.assertNotIn('max_tokens',c.chat.completions.create.call_args.kwargs)

    def test_fenced_json_and_distinct_validation_errors(self):
        schema={'type':'object','additionalProperties':False,
                'properties':{'ok':{'type':'boolean'}},'required':['ok']}
        c=client_for({'ok':True})
        c.chat.completions.create.return_value.choices[0].message.content='```json\n{"ok": true}\n```'
        self.assertEqual(q.request_json(kind='text',instructions='Return JSON',schema=schema,client=c)[0],{'ok':True})
        c.chat.completions.create.return_value.choices[0].message.content='{}'
        with self.assertRaisesRegex(EvaluationError,r'\$\.ok'):
            q.request_json(kind='text',instructions='Return JSON',schema=schema,client=c)
        c.chat.completions.create.return_value.choices[0].message.content='{"ok":'
        with self.assertRaisesRegex(EvaluationError,'合法 JSON'):
            q.request_json(kind='text',instructions='Return JSON',schema=schema,client=c)
        c.chat.completions.create.return_value.choices[0].message.content=''
        with self.assertRaisesRegex(EvaluationError,'空内容'):
            q.request_json(kind='text',instructions='Return JSON',schema=schema,client=c)

    def test_owned_raw_response_diagnostics_are_metadata_only(self):
        schema={'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok']}
        response=SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',
            message=SimpleNamespace(content='{"ok": true}'))],
            usage=SimpleNamespace(prompt_tokens=23,completion_tokens=7))
        raw=SimpleNamespace(status_code=200,parse=Mock(return_value=response))
        c=Mock()
        c.chat.completions.with_raw_response.create.return_value=raw
        with patch.dict(os.environ,{'QWEN_DEBUG':'true'}),patch('services.qwen_service.OpenAI',return_value=c),\
             patch.object(q.DIAGNOSTIC_LOG,'warning') as log:
            self.assertEqual(q.request_json(kind='text',instructions='Return JSON',schema=schema)[0],{'ok':True})
        c.chat.completions.with_raw_response.create.assert_called_once()
        c.close.assert_called_once()
        event=json.loads(log.call_args.args[1])
        self.assertEqual(event['http_status'],200)
        self.assertEqual((event['input_tokens'],event['output_tokens']),(23,7))
        self.assertEqual(event['finish_reason'],'stop')
        self.assertEqual(event['content_type'],'str')
        self.assertTrue(event['json_parsed'] and event['schema_valid'])
        self.assertNotIn('unit-test-not-a-key',log.call_args.args[1])
        self.assertNotIn('data:image',log.call_args.args[1])

    def test_staff_unknowns_are_not_filled(self):
        doc=dict(coverage='partial',bpm=None,key_signature=None,meter=None,structure='一行片段',
                 events=[dict(start_beats=0,duration_beats=None,pitch=None,rest=False,
                              voice='1',position='第一小节',confidence='low',issue='模糊')],warnings=[],unsupported_symbols=[])
        out=recognize_staff_vision(Image.new('RGB',(100,100)),client_for(doc))
        self.assertIsNone(out['rows'][0]['pitch']);self.assertIsNone(out['rows'][0]['duration'])
        self.assertTrue(out['rows'][0]['uncertain'])
        with self.assertRaises(ValueError):preview_audio(out['rows'])

    def test_music_plan_reuses_local_renderer(self):
        data=fixture_midi();assets=[a for a in list_assets() if a['material_type']=='instrument'][:1]
        plan=local_plan(parse_score(data,'test.mid'),assets,'洞经音乐',[])
        c=client_for(plan)
        out=MusicArrangementAgent(c).run(data,'test.mid',[a['asset_id'] for a in assets],'洞经音乐',100,real=True)
        self.assertEqual(out['mode'],'qwen_plan');self.assertEqual(out['wav'][:4],b'RIFF')
        self.assertEqual(out['midi'][:4],b'MThd');c.chat.completions.create.assert_called_once()
        self.assertNotIn('image_url',json.dumps(c.chat.completions.create.call_args.kwargs))

    def test_music_failure_is_labelled_local_fallback(self):
        data=fixture_midi();asset=next(a for a in list_assets() if a['material_type']=='instrument')
        c=client_for({});c.chat.completions.create.side_effect=RuntimeError('private secret')
        out=MusicArrangementAgent(c).run(data,'test.mid',[asset['asset_id']],'洞经音乐',100,real=True)
        self.assertEqual(out['mode'],'local_rules')
        self.assertIn('不是 AI',out['fallback_reason'])
        self.assertNotIn('private',out['fallback_reason'])
        self.assertEqual(out['wav'][:4],b'RIFF')
        c.chat.completions.create.assert_called_once()

    def test_qwen_page_load_never_calls_api(self):
        from streamlit.testing.v1 import AppTest
        with patch('services.qwen_service.request_json',side_effect=AssertionError('No click')):
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
            for page in ('pages/dongba.py','pages/music.py'):
                app.switch_page(page).run()
                self.assertFalse(app.exception)


if __name__=='__main__':unittest.main()
