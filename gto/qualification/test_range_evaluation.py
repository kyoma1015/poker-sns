"""Sampler/checkpoint regression with a tiny deterministic payoff oracle."""
import json,random,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gto.qualification import range_followup as follow
from gto.qualification import range_study as study

class Resume(unittest.TestCase):
    def test_partial_EV_sampler_resume_exactly_matches_uninterrupted(self):
        old=object();p=SimpleNamespace(base=old,native=None,policy_digest='a'*64)
        def value(s,native,game,deck,tape):return ((sum(deck)+tape%17)%101-50)/2+(0.125 if s is p else 0)
        with tempfile.TemporaryDirectory() as d,patch.object(follow,'load',lambda *a:p),patch.object(follow,'native_value',value),patch.object(follow,'NativeGame',lambda *a:None):
            root=Path(d);follow.ev('', '',root/'full.json')
            rng=random.Random(17118204);a=[];b=[]
            for _ in range(64):
                deck=rng.sample(range(52),9);tape=rng.getrandbits(128);a.append(value(old,None,None,deck,tape));b.append(value(p,None,None,deck,tape))
            q=root/'partial.json';q.write_text(json.dumps(dict(policy_digest=p.policy_digest,rng=rng.getstate(),old=a,new=b,seconds=0)))
            follow.ev('','',root/'resumed.json',q)
            x=json.loads((root/'full.json').read_text());y=json.loads((root/'resumed.json').read_text())
            for key in ('n','old_EV_bb','new_EV_bb','EV_change_bb','policy_digest'):self.assertEqual(x[key],y[key])
    def test_conditional_sampler_resume_keeps_samples_rng_and_counters(self):
        receipt=json.loads(study.BASELINE.read_text());old=SimpleNamespace(native=None,policy_digest=receipt['source_policy_digest'])
        ps=[SimpleNamespace(base=old,native=None,policy_digest=str(i)*64,buckets=b) for i,b in [(1,8),(2,16)]]
        class Dev:
            def __init__(self,base):self.base=base;self.jams=0
        def value(s,native,game,deck,tape):
            if isinstance(s,Dev):
                event=deck[0]%3==0
                if event:s.jams+=1
                return (-40 if s.base is old else -1) if event else 0.
            return 0.
        with tempfile.TemporaryDirectory() as d,patch.object(study,'policies',lambda *a:ps),patch.object(study,'RiverNuts',Dev),patch.object(study,'native_value',value),patch.object(study,'NativeGame',lambda *a:None):
            root=Path(d);study.conditional('','',root/'full.json')
            checkpoint=Path(str(root/'full.json')+'.progress.json')
            # Recreate a genuine first16-event checkpoint, then resume the rest.
            full=json.loads(checkpoint.read_text());rng=random.Random(17118202);worlds=[];attempts=0
            while len(worlds)<16:
                attempts+=1;deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
                if deck[0]%3==0:worlds.append(dict(deck=deck,tape=tape))
            q=root/'partial.json';q.write_text(json.dumps(dict(accepted=16,attempts=attempts,seconds=0,rng=rng.getstate(),worlds=worlds,
                old_gains=[40.]*16,new_gains=[[1.]*16 for _ in ps],differences=[[39.]*16 for _ in ps],new_deviation_jams=[16,16],policy_digests=[p.policy_digest for p in ps])))
            study.conditional('','',root/'resumed.json',q)
            x=json.loads((root/'full.json').read_text());y=json.loads((root/'resumed.json').read_text())
            for key in ('profiles','worlds','raw_old_gains','raw_new_gains','attempts','source_event_count'):self.assertEqual(x[key],y[key])
if __name__=='__main__':unittest.main()
