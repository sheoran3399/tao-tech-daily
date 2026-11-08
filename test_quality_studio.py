import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import quality_studio as q


def brief():
    return {'story_id':18,'kind':'fictional','headline':'The city learns to share',
            'intended_story':'Light reaches ordinary homes','art_prompt':'A small person opens a gate',
            'captions':['The city built its smartest tower yet.',
                        'But the people below were left in the dark.',
                        'What if progress were measured by whom it reaches?'],
            'quote_zh':'上善若水。水善利萬物而不爭。',
            'quote_en':'The highest goodness is like water: it benefits all things without competing.',
            'quote_source':'Dao De Jing · Chapter 8','quote_source_url':'https://ctext.org/dao-de-jing',
            'quote_reviewed':True}


def judgment(score=8):
    return {'scores':{key:{'score':score,'evidence':'Visible example'} for key in q.WEIGHTS},
            'blockers':[],'preserve':['Palette'],'fixes':[], 'confidence':.8,'uncertainties':[]}


class QualityTests(unittest.TestCase):
    def test_timing(self):
        self.assertEqual(q.planned_seconds(brief()),[6,6,7,14])

    def test_long_captions_expand(self):
        b=brief(); b['captions'][0]='word '*30
        self.assertEqual(q.planned_seconds(b)[0],16)

    def test_low_clarity_blocks_good_total(self):
        j=judgment(10);j['scores']['story_clarity']['score']=6
        r=q.score_report(j,brief())
        self.assertGreaterEqual(r['weighted_score'],80)
        self.assertEqual(r['decision'],'revise')

    def test_pass_still_not_published(self):
        r=q.score_report(judgment(),brief())
        self.assertEqual(r['decision'],'ready_for_human_review')
        self.assertFalse(r['automatic_publication'])

    def test_news_verification_gate(self):
        b=brief();b['kind']='news'
        self.assertTrue(q.human_gates(b))

    def test_quote_verification_gate(self):
        b=brief();b['quote_reviewed']=False
        self.assertEqual(q.score_report(judgment(10),b)['decision'],'revise')

    def test_confidence_gate(self):
        j=judgment(10);j['confidence']=.4
        self.assertEqual(q.score_report(j,brief())['decision'],'revise')

    def test_bad_schema_rejected(self):
        j=judgment();j['scores']['artfulness']['score']=11
        with self.assertRaises(ValueError):q.score_report(j,brief())

    def test_call_limit(self):
        with tempfile.TemporaryDirectory() as td:
            b=q.Budget(Path(td)/'budget.json',2)
            b.reserve('a');b.reserve('b')
            with self.assertRaises(q.StudioError):b.reserve('c')
            self.assertEqual(b.calls,2)

    def test_paid_opt_in(self):
        with self.assertRaises(q.StudioError):
            q.main(['judge','--image','missing.png','--brief','missing.json','--out','missing-output.json'])

    def test_four_states(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.gif'
            frames=[Image.new('RGB',(20,20),color) for color in ['red','blue','green','yellow']]
            frames[0].save(p,save_all=True,append_images=frames[1:],duration=100)
            self.assertEqual(len(q.load_frames(p)),4)

    def test_best_candidate_kept_and_calls_capped(self):
        scores=iter([75,70,72])
        def fake_create(b,fixes,keep,budget,path):
            budget.reserve('creator');Image.new('RGB',(20,20)).save(path)
        def fake_render(frames,seconds,d):
            (d/'movie.mp4').write_bytes(b'test')
        def fake_judge(frames,b,budget,art):
            budget.reserve('observer');budget.reserve('judge')
            return {'decision':'revise','weighted_score':next(scores),
                    'fixes':[{'target':'art','observation':'Dark','change':'Light it'}],
                    'preserve':['Palette']}
        with tempfile.TemporaryDirectory() as td, \
             patch.object(q,'compose',return_value=[Image.new('RGB',(20,20))]*4), \
             patch.object(q,'create_art',side_effect=fake_create), \
             patch.object(q,'render_frames',side_effect=fake_render), \
             patch.object(q,'judge',side_effect=fake_judge), \
             patch.object(q.shutil,'which',return_value='/usr/bin/tool'):
            folder=Path(td)/'run'
            result=q.improve(brief(),3,folder)
            self.assertTrue(result['best_candidate'].endswith('candidate_01'))
            self.assertEqual(json.loads((folder/'api_usage.json').read_text())['calls'],9)
            self.assertEqual(result['status'],'stopped_no_progress')

    def test_non_art_issue_stops_loop(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(q,'compose',return_value=[]), \
             patch.object(q,'create_art',side_effect=lambda b,f,k,budget,p:Image.new('RGB',(20,20)).save(p)), \
             patch.object(q,'render_frames',side_effect=lambda f,s,p:(p/'movie.mp4').write_bytes(b'fake')), \
             patch.object(q,'judge',return_value={'decision':'revise','weighted_score':72,
                 'fixes':[{'target':'facts','observation':'Unknown','change':'Verify it'}],'preserve':[]}), \
             patch.object(q.shutil,'which',return_value='/usr/bin/tool'):
            result=q.improve(brief(),3,Path(td)/'run')
            self.assertEqual(result['status'],'needs_editorial_review')
            self.assertEqual(len(result['candidates']),1)

if __name__=='__main__':unittest.main()
