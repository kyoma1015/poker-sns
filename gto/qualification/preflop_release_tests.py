"""Reduced preflop legality/identity tests; not a native-quality certificate."""
import gzip,json,math,os,unittest
from pathlib import Path
from gto.qualification.preflop_release_solver import tree,load_policy
from gto.qualification.build import load
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,legal,ROOT
from gto.qualification.public_response import observe
from gto.abstract import model
from gto.native.training import NativeGame

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class ReleaseRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=os.environ['QUALIFICATION_BUILD'];cls.rules,cls.native=load(cls.build)
        cls.path=ROOT/'docs/qa/release-route-20261118/strategy.json.gz'
        cls.policy=load_policy(cls.build,cls.path)
    def test_every_abstract_action_matches_independent_native_state(self):
        for n in tree(self.rules):
            if n['actor']<0:continue
            b=betting(self.rules);s=self.native.NativeState(NativeGame([100,100]))
            for c in (48,49,0,1):s.apply_action(c)
            for label in n['history']:
                a=0 if label=='fold' else 1 if label in ('call','check') else int(label.split('_')[-1])+2
                act(b,a);s.apply_action(a)
            self.assertEqual(s.current_player(),n['actor']);self.assertEqual(s.audit()['live'],n['contributions'])
            self.assertTrue(set(n['native_actions']).issubset(s.legal_actions()))
            self.assertEqual(legal(b),s.legal_actions())
    def test_all169_stage_policies_normalized_and_legal(self):
        for n in self.policy.nodes:
            if n['actor']<0:continue
            b=betting(self.rules)
            for label in n['history']:act(b,0 if label=='fold' else 1 if label in ('call','check') else int(label.split('_')[-1])+2)
            for group in model.classes():
                o=observe(b,group[0],[]);p=self.policy.row(o,True)
                self.assertEqual(len(p),len(o.actions));self.assertAlmostEqual(sum(p),1,places=12);self.assertTrue(all(x>=0 for x in p))
                self.assertTrue(all(a in n['native_actions'] for a,x in zip(o.actions,p) if x>0))
    def test_unknown_size_reuses_frozen_full_policy_not_fold_completion(self):
        b=betting(self.rules);act(b,9) # 3.5BB, absent from reduced3BB tree.
        o=observe(b,[48,49],[])
        self.assertEqual(self.policy.row(o,True),self.policy.fallback.row(o,True))
    def test_explicit_postflop_controller_has_no_future_card_input(self):
        b=betting(self.rules);act(b,1);act(b,1)
        o=observe(b,[48,49],[4,9,14]);p=self.policy.row(o,True)
        self.assertEqual(dict(zip(o.actions,p))[1],1.)
        self.assertEqual(sum(x for a,x in zip(o.actions,p) if a!=1),0.)
    def test_source_identity_and_blocker_are_preserved(self):
        a=json.loads(gzip.decompress(self.path.read_bytes()))
        self.assertEqual(a['policy_digest'],self.policy.policy_digest);self.assertFalse(a['ordinary_registry_admission'])
        self.assertEqual(a['formal_acceptance_complete'],0);self.assertIsNone(a['identity']['real_game_continuation_error_bb'])
        for stage in ('rfi','vs_open','vs_3bet'):
            self.assertEqual(len(a['model_ranges'][stage]['hands']),169)
        from gto.qualification.native_mccfr import digest
        p=self.policy;self.assertEqual(digest(dict(identity=p.id,nodes=p.nodes,strategy=p.strategy,fallback=p.fallback.policy_digest)),p.policy_digest)

if __name__=='__main__':unittest.main()
