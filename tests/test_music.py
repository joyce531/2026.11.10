from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import mido
import numpy as np
import soundfile as sf

from services.music_library import list_assets, analyze, audio_path
from services.music_score import parse_score, write_midi
from services.music_service import arrange_music
from naxi_agents.music_agent import local_plan, validate_plan


def setUpModule():
    patcher=patch('services.qwen_service.enabled',return_value=False)
    patcher.start();unittest.addModuleCleanup(patcher.stop)


def fixture_midi():
    # Synthetic test only: not a pop song or a traditional piece.
    notes=[dict(start=i*.5,duration=.4,pitch=[64,67,69,67,64,62,60,62][i%8],velocity=80,track=0) for i in range(60)]
    return write_midi(notes,30,['synthetic-test'])


XML=b'''<score-partwise version="4.0"><part-list><score-part id="P1"><part-name>Test</part-name></score-part></part-list><part id="P1"><measure number="1"><attributes><divisions>2</divisions><time><beats>4</beats><beat-type>4</beat-type></time></attributes><direction><sound tempo="120"/></direction><note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><tie type="start"/></note><note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><tie type="stop"/></note><note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration></note></measure></part></score-partwise>'''


class MusicTests(unittest.TestCase):
    def setUp(self):
        self.assets=[a for a in list_assets() if a['material_type']=='instrument']
        self.ids=[a['asset_id'] for a in self.assets if a['label'] in ('人面竹胡琴','曲项琵琶','口弦')]

    def test_existing_audio_library_decodes(self):
        rows=list_assets();self.assertEqual(len(rows),13)
        self.assertTrue(all(r['analysis_status'].startswith('decoded') for r in rows))
        for row in rows:
            with sf.SoundFile(audio_path(row['path'])) as f:
                self.assertGreater(f.read(100).size,0)
                self.assertEqual(f.samplerate,row['sample_rate'])
        flute=next(r for r in rows if r['label']=='笛子')
        self.assertIsNone(flute['sample_mapping'])
        self.assertTrue(flute['duplicates'])

    def test_midi_tempo_changes_and_polyphony(self):
        f=mido.MidiFile();t=mido.MidiTrack();f.tracks.append(t)
        t.extend([mido.Message('note_on',note=60,velocity=80,time=0),
                  mido.MetaMessage('set_tempo',tempo=1000000,time=480),
                  mido.Message('note_off',note=60,time=480)])
        b=BytesIO();f.save(file=b)
        score=parse_score(b.getvalue(),'x.mid')
        self.assertAlmostEqual(score['notes'][0]['duration'],1.5)

    def test_musicxml_ties_and_mxl(self):
        score=parse_score(XML,'test.musicxml')
        self.assertEqual(score['note_count'],2)
        self.assertEqual(score['notes'][0]['duration'],1)
        out=BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('META-INF/container.xml','<container><rootfiles><rootfile full-path="s.xml"/></rootfiles></container>')
            z.writestr('s.xml',XML)
        self.assertEqual(parse_score(out.getvalue(),'x.mxl')['notes'],score['notes'])
        self.assertEqual(len(arrange_music(XML,'x.xml',self.ids,'白沙细乐',100,real=False)['wav'])>44,True)

    def test_reject_unsupported_and_malformed(self):
        for data,name in [(b'fake','a.mid'),(b'fake','x.pdf'),(XML.replace(b'<note>',b'<note><grace/>',1),'x.xml'),
                          (b'<!DOCTYPE x [<!ENTITY a SYSTEM "file:///secret">]><score-partwise>&a;</score-partwise>','x.xml'),
                          (b'x'*(2*1024*1024+1),'x.mid')]:
            with self.subTest(name=name),self.assertRaises(ValueError):parse_score(data,name)

    def test_30_second_render_download_and_retention(self):
        result=arrange_music(fixture_midi(),'fixture.mid',self.ids,'洞经音乐',100,real=False)
        self.assertEqual(result['mode'],'local_rules')
        self.assertAlmostEqual(result['duration_seconds'],29.9)
        wave,rate=sf.read(BytesIO(result['wav']))
        self.assertEqual(rate,22050)
        self.assertGreater(np.sqrt(np.mean(wave**2)),.005)
        self.assertLess(np.abs(wave).max(),1)
        self.assertAlmostEqual(len(wave)/rate,result['duration_seconds'])
        parsed=parse_score(result['midi'],'output.mid')
        self.assertGreater(parsed['note_count'],0)
        self.assertEqual(result['retention']['retained_fraction'],1)
        self.assertGreater(sum(u['sample_notes'] for u in result['usage']),0)
        self.assertGreater(sum(u['auxiliary_notes'] for u in result['usage']),0)
        self.assertGreater(sum(u['phrases'] for u in result['usage']),0)
        reduced=arrange_music(fixture_midi(),'x.mid',self.ids,'白沙细乐',50,real=False)
        self.assertEqual(reduced['retention']['melody_notes_retained'],30)

    def test_plan_validation_and_mock_api(self):
        selected=[a for i in self.ids for a in self.assets if a['asset_id']==i]
        plan=local_plan(parse_score(fixture_midi(),'x.mid'),selected,'洞经音乐',[])
        calls=[]
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(status='completed',output_text=json.dumps(plan))
        client=SimpleNamespace(responses=SimpleNamespace(create=create))
        result=arrange_music(fixture_midi(),'x.mid',self.ids,'洞经音乐',100,real=True,client=client)
        self.assertEqual(result['mode'],'openai_plan')
        self.assertEqual(len(calls),1)
        self.assertFalse(calls[0]['store']);self.assertFalse(calls[0]['stream'])
        self.assertNotIn('base64',calls[0]['input'])
        bad={**plan,'roles':[{'asset_id':'other','role':'melody'}]}
        with self.assertRaises(ValueError):validate_plan(bad,selected)
        with patch('naxi_agents.music_agent.create_client',side_effect=ValueError('private')):
            result=arrange_music(fixture_midi(),'x.mid',self.ids,'洞经音乐',100,real=True)
        self.assertEqual(result['mode'],'local_rules')
        self.assertTrue(result['fallback_reason']);self.assertNotIn('private',result['fallback_reason'])

    def test_selection_validation(self):
        for ids in ([],['missing'],[self.ids[0],self.ids[0]]):
            with self.assertRaises(ValueError):arrange_music(fixture_midi(),'x.mid',ids,'洞经音乐',100,real=False)

    def test_analysis_and_path_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'tone.wav'
            sf.write(path,np.sin(2*np.pi*440*np.arange(22050)/22050)*.3,22050)
            meta,mapping=analyze(path,'instrument')
            self.assertEqual(meta['duration_seconds'],1)
            self.assertEqual(mapping['mode'],'limited_pitch')
            self.assertAlmostEqual(mapping['root_midi'],69,delta=.2)
        with self.assertRaises(ValueError):audio_path('.env')


if __name__=='__main__':unittest.main()
