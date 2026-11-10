"""Synthetic fixtures test mechanics, never represent real recognition results."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image, ImageDraw
from streamlit.testing.v1 import AppTest

from services.score_image import preprocess, classify, load_score_image
from services.score_omr import recognize_jianpu, staff_document, audiveris_executable
from services.score_review import jianpu_rows, confirm_midi, preview_audio, review_hash
from services.music_score import parse_score
from tests.test_music import XML


def setUpModule():
    patcher=patch('services.qwen_service.enabled',return_value=False)
    patcher.start();unittest.addModuleCleanup(patcher.stop)


def token(kind='note', **kw):
    return dict(kind=kind, degree=1 if kind=='note' else None, octave_shift=0,
                accidental=0, base_beats=1, dots=0, tie_to_next=False,
                confidence='high', issue='', **kw) if not kw else {**token(kind), **kw}


def document():
    return dict(coverage='complete',tonic_note='A',tonic_degree=1,bpm=60,
                meter='4/4',tokens=[token(),token('rest'),token(degree=3)],
                warnings=[],unsupported_symbols=[])


class ScoreOmrTests(unittest.TestCase):
    def test_key_degree_octave_and_no_default_c(self):
        doc=document()
        self.assertEqual(jianpu_rows(doc,'A',1,4,60)[0]['pitch'],69)
        doc['tokens']=[token(degree=6),token(degree=1,octave_shift=1,accidental=-1)]
        rows=jianpu_rows(doc,'A',6,4,60)
        self.assertEqual([r['pitch'] for r in rows],[69,71])
        with self.assertRaisesRegex(ValueError,'调号未知'):jianpu_rows(doc,None,1,4,60)

    def test_dots_rest_extend_tie_and_unknown_time(self):
        doc=document();doc['tokens']=[token(dots=1),token('extend'),token('rest',base_beats=.5),
                                    token(tie_to_next=True),token()]
        rows=jianpu_rows(doc,'A',1,4,60)
        self.assertEqual([r['duration'] for r in rows],[2.5,.5,2])
        self.assertEqual(rows[-1]['start'],3)
        doc['tokens']=[token(base_beats=None),token()]
        rows=jianpu_rows(doc,'A',1,4,60)
        self.assertTrue(rows[0]['uncertain']);self.assertIsNone(rows[1]['start'])
        with self.assertRaises(ValueError):preview_audio(rows)

    def test_confirmation_uncertainty_and_roundtrip(self):
        rows=jianpu_rows(document(),'A',1,4,60);rows[0]['uncertain']=True
        with self.assertRaises(ValueError):confirm_midi(rows,[])
        with self.assertRaises(ValueError):confirm_midi(rows,[],confirmed=True)
        rows[0]['reviewed']=True
        with self.assertRaises(ValueError):confirm_midi(rows,[],confirmed=True,has_limitations=True)
        midi=confirm_midi(rows,[],confirmed=True,has_limitations=True,limitations_accepted=True)
        score=parse_score(midi,'review.mid')
        self.assertEqual([n['pitch'] for n in score['notes']],[69,73])
        self.assertEqual(preview_audio(rows)[:4],b'RIFF')
        before=review_hash(rows,[]);rows[0]['pitch']=70
        self.assertNotEqual(before,review_hash(rows,[]))

    def test_staff_xml_uncertainty_and_linear_repeats(self):
        xml=XML.replace(b'</measure>',b'<barline><repeat direction="backward"/></barline></measure>')
        result=staff_document(xml,'x.musicxml')
        self.assertTrue(result['unsupported_symbols'])
        self.assertTrue(all(r['uncertain'] and not r['reviewed'] for r in result['rows']))
        self.assertEqual(len(result['rows']),2)
        with self.assertRaisesRegex(ValueError,'装饰'):staff_document(XML.replace(b'<note>',b'<note><grace/>',1),'x.xml')

    def test_image_validation_and_routing(self):
        with self.assertRaises(ValueError):load_score_image(b'bad','a.png')
        with self.assertRaises(ValueError):preprocess(Image.new('RGB',(600,400),'white'))
        im=Image.new('RGB',(800,400),'white');d=ImageDraw.Draw(im)
        for y in range(100,151,10):
            if y<150:d.line((30,y,770,y),fill='black',width=2)
        _,ink,_=preprocess(im)
        self.assertEqual(classify(ink)['kind'],'staff')
        self.assertEqual(classify(np.zeros((400,800),dtype='uint8'))['kind'],'unknown')

    def test_actual_supplied_images_routing(self):
        root=Path('data/music/曲谱')
        if not root.exists():self.skipTest('Local score collection absent')
        for p in root.rglob('*'):
            if p.suffix.lower() not in ('.jpg','.webp','.png'):continue
            with self.subTest(path=p):
                _,ink,_=preprocess(load_score_image(p.read_bytes(),p.name))
                expected='jianpu' if '简谱' in str(p) else 'staff'
                self.assertEqual(classify(ink)['kind'],expected)

    def test_real_api_contract_single_call_and_errors(self):
        client=Mock();client.responses.create.return_value=SimpleNamespace(status='completed',output_text=json.dumps(document()))
        def config(k,default=''):return 'true' if k=='USE_REAL_AI' else default
        with patch('services.score_omr.config_value',side_effect=config):
            result=recognize_jianpu(Image.new('RGB',(60,60)),client)
            self.assertEqual(result['tonic_note'],'A');client.responses.create.assert_called_once()
            kwargs=client.responses.create.call_args.kwargs
            self.assertFalse(kwargs['stream']);self.assertFalse(kwargs['store'])
            client.responses.create.side_effect=RuntimeError('secret should never appear')
            with self.assertRaisesRegex(ValueError,'请求失败'):recognize_jianpu(Image.new('RGB',(60,60)),client)
        with patch('services.score_omr.config_value',return_value='false'):
            with self.assertRaisesRegex(ValueError,'不会用 Mock'):recognize_jianpu(Image.new('RGB',(60,60)),client)

    def test_missing_engine(self):
        with patch('services.score_omr.config_value',return_value='Z:/missing/Audiveris.exe'):
            with self.assertRaisesRegex(ValueError,'AUDIVERIS_EXE'):audiveris_executable()

    def test_review_ui_no_request_on_rerun_and_confirm_gate(self):
        image=Image.new('RGB',(500,200),'white');ImageDraw.Draw(image).text((40,40),'1234567',fill='black')
        b=BytesIO();image.save(b,format='PNG')
        prepared=(image,image,{},dict(kind='jianpu'))
        doc={**document(),'engine':'test_fixture','notation':'jianpu'}
        script="from components.score_review import image_score_review\nresult=image_score_review(b'fixture','fixture.png')\n"
        with patch('components.score_review.prepare_upload',return_value=prepared),patch('components.score_review.recognize_jianpu',return_value=doc) as recognize:
            app=AppTest.from_string(script).run()
            self.assertFalse(app.exception);recognize.assert_not_called()
            app.button[0].click().run();recognize.assert_called_once()
            self.assertFalse(app.exception)
            final=next(x for x in app.button if x.label=='确认校对并生成 MIDI')
            self.assertTrue(final.disabled)
            app.run();recognize.assert_called_once()
            app.checkbox[0].check().run()
            next(x for x in app.button if x.label=='确认校对并生成 MIDI').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('已生成 MIDI' in x.value for x in app.success))
            app.checkbox[0].uncheck().run()
            self.assertFalse(any('已生成 MIDI' in x.value for x in app.success))


if __name__=='__main__':unittest.main()
