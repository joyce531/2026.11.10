"""Milestone 5B offline media, UI and Wan HTTP contract checks. No real API calls."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from services import dance_service as d


class DanceVideoTests(unittest.TestCase):
    def test_existing_media_are_readable(self):
        self.assertEqual(len(d.choices(d.OUTFIT_DIR)),4)
        self.assertEqual(len(d.choices(d.BACKGROUND_DIR)),6)
        self.assertEqual(d.inspect_video(d.bundled_video().read_bytes())['duration'],8.93)
        self.assertEqual(d.inspect_image(d.bundled_portrait().read_bytes())['format'],'JPEG')
        for path in (*d.choices(d.OUTFIT_DIR).values(),*d.choices(d.BACKGROUND_DIR).values()):
            self.assertEqual(d.inspect_image(path.read_bytes())['format'],'JPEG')

    def test_submit_uses_private_upload_and_one_async_creation(self):
        policy={'policy':'policy','signature':'signature','upload_dir':'dashscope-instant/abc',
            'upload_host':'https://dashscope-file-abc.oss-cn-beijing.aliyuncs.com',
            'oss_access_key_id':'access-id','x_oss_object_acl':'private',
            'x_oss_forbid_overwrite':'true'}
        session=Mock()
        session.get.return_value=SimpleNamespace(status_code=200,json=lambda:{'data':policy})
        session.post.side_effect=[SimpleNamespace(status_code=200),
            SimpleNamespace(status_code=200,json=lambda:{'output':{'task_id':'12345678-aaaa-bbbb-cccc-123456789abc','task_status':'PENDING'}})]
        req=d.DanceRequest('沿用参考视频舞步','女1','古城','自然写实',9,'')
        with (patch.object(d,'_settings',return_value=('unit-test-key','https://dashscope.aliyuncs.com/api/v1')),
              patch.object(d,'inspect_video',return_value={'duration':8.93}),
              patch.object(d,'inspect_image',return_value={'format':'JPEG'})):
            result=d.submit_videoedit(b'valid-video',b'photo',b'outfit',b'background',req,session)
        self.assertEqual(result['status'],'PENDING')
        self.assertEqual(session.post.call_count,2)
        self.assertEqual(session.get.call_args.args[0],'https://dashscope.aliyuncs.com/api/v1/uploads')
        upload= session.post.call_args_list[0]
        self.assertEqual(upload.args[0],policy['upload_host'])
        self.assertEqual(upload.kwargs['files'][-1][0],'file')
        call=session.post.call_args_list[1]
        self.assertEqual(call.kwargs['headers']['X-DashScope-Async'],'enable')
        self.assertEqual(call.kwargs['headers']['X-DashScope-OssResourceResolve'],'enable')
        self.assertEqual(call.kwargs['json']['model'],d.MODEL)
        media=call.kwargs['json']['input']['media']
        self.assertEqual([m['type'] for m in media],['video','reference_image','reference_image','reference_image'])
        self.assertTrue(media[0]['url'].startswith('oss://'))
        self.assertTrue(all(m['url'].startswith('data:image/jpeg;base64,') for m in media[1:]))
        self.assertNotIn('unit-test-key',json.dumps(call.kwargs['json']))

    def test_query_and_download_are_separate_from_creation(self):
        url='https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/output.mp4?token=hidden'
        session=Mock()
        session.get.return_value=SimpleNamespace(status_code=200,json=lambda:{'output':{
            'task_status':'SUCCEEDED','video_url':url}})
        with patch.object(d,'_settings',return_value=('unit-test-key','https://dashscope.aliyuncs.com/api/v1')):
            result=d.query_videoedit('12345678-aaaa-bbbb-cccc-123456789abc',session)
        self.assertEqual(result['status'],'SUCCEEDED')
        self.assertEqual(result['video_url'],url)
        self.assertEqual(session.get.call_count,1)
        with self.assertRaises(d.DanceVideoError):
            d.query_videoedit('../unsafe',session)

    def test_download_validates_mp4_without_real_api(self):
        fixture=d.bundled_video().read_bytes()
        session=Mock()
        session.get.return_value=SimpleNamespace(status_code=200,
            iter_content=lambda size: iter((fixture[:5000],fixture[5000:])))
        url='https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/result.mp4'
        self.assertEqual(d.download_videoedit(url,session),fixture)
        with self.assertRaises(d.DanceVideoError):
            d.download_videoedit('https://example.com/private.mp4',session)
        self.assertEqual(session.get.call_count,1)

    def test_page_load_never_calls_video_api(self):
        app_path=Path(__file__).resolve().parents[1]/'app.py'
        with patch('services.dance_service.submit_videoedit',side_effect=AssertionError('No button click')):
            app=AppTest.from_file(str(app_path)).run(timeout=20)
            app.switch_page('pages/dance.py').run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.selectbox[0].options),4)
            self.assertEqual(len(app.selectbox[1].options),6)
            self.assertTrue(app.button[0].disabled)

    def test_page_submit_refresh_play_download_offline(self):
        app_path=Path(__file__).resolve().parents[1]/'app.py'
        task='12345678-aaaa-bbbb-cccc-123456789abc'
        fixture=d.bundled_video().read_bytes()
        with (patch('services.dance_service.submit_videoedit',return_value={'task_id':task,'status':'PENDING','model':d.MODEL}) as submit,
              patch('services.dance_service.query_videoedit',return_value={'task_id':task,'status':'SUCCEEDED','video_url':'https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/x.mp4'}) as query,
              patch('services.dance_service.download_videoedit',return_value=fixture) as download):
            app=AppTest.from_file(str(app_path)).run(timeout=20)
            app.switch_page('pages/dance.py').run(timeout=20)
            app.checkbox[0].set_value(True).run(timeout=20)
            self.assertFalse(app.button[0].disabled)
            app.button[0].click().run(timeout=20)
            submit.assert_called_once()
            self.assertEqual(app.session_state['dance_video_job']['status'],'PENDING')
            app.button[1].click().run(timeout=20)
            query.assert_called_once();download.assert_called_once()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['dance_video_job']['video'],fixture)


if __name__=='__main__':unittest.main()
