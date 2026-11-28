"""Regression gates for full-game evaluation, not tests that certify GTO."""
import json,math,os,random,unittest
from fractions import Fraction
from pathlib import Path
from gto.qualification.build import load
from gto.qualification.policy import ROOT,Profile,act,legal,sha
from gto.qualification.evaluate import Moments,gate,history_mass,rollout

class StatisticsAndEvidence(unittest.TestCase):
    def test_missing_and_single_samples_are_unknown(self):
        m=Moments();self.assertIsNone(m.result(-50,50)['mean']);m.add(1);self.assertIsNone(m.result(-50,50)['halfwidth'])
    def test_interval_covers_constant_and_is_bounded(self):
        m=Moments()
        for _ in range(16384):m.add(1)
        x=m.result(-50,50);self.assertLessEqual(x['interval'][0],1);self.assertGreaterEqual(x['interval'][1],1);self.assertGreater(x['halfwidth'],0)
    def test_absence_of_exploit_does_not_certify(self):
        report={'gain_bb':{'interval':[-1,1]},'hands':{'AA':{'baseline':{'halfwidth':None}}}}
        result=gate(report);self.assertFalse(result['ordinary_registry_admission']);self.assertIn('FULL_NATIVE_BR_UPPER_BOUND_MISSING',result['reasons'])
        report['gain_bb']['interval']=[.1,1];self.assertIn('FEASIBLE_DEVIATION_REFUTES_PROPOSED_GAIN_LIMIT',gate(report)['reasons'])
    def test_receipt_and_frozen_proposal(self):
        folder=ROOT/'docs/qa/preflop-qualification-20261117';receipt=json.loads((folder/'results.json').read_text())
        self.assertEqual(receipt['protocol_sha256'],sha(folder/'PROTOCOL.md'))
        for p,digest in receipt['source_sha256'].items():self.assertEqual(sha(ROOT/p),digest,p)
        pins=json.loads((folder/'runtime-source-pins.json').read_text())['sha256']
        for path,digest in pins.items():self.assertEqual(sha(ROOT/path),digest,path)
        proposal=json.loads((folder/'proposal.json').read_text());self.assertEqual(proposal['proposal_sha256'],sha(ROOT/'docs/specs/GTO_PREFLOP_RELEASE_PROPOSAL_20261117.md'))
        self.assertEqual(proposal['status'],'PENDING_APPROVAL');self.assertEqual(receipt['ordinary_verified_rfi_vsopen_strategies'],0)
        for report in receipt['reports']:
            p=Profile(report['model']);self.assertEqual(p.digest,report['totalized_policy_digest']);self.assertEqual(len(report['hands']),169)
            self.assertEqual(report['accepted_deals'],16384);self.assertEqual(report['native_python_rank_and_settlement_crosschecks_per_arm'],256)
            self.assertGreater(report['gain_bb']['interval'][0],.05);self.assertFalse(report['qualification']['ordinary_registry_admission'])
            self.assertEqual(report['qualification']['full_native_nashconv_bb'],None)
    def test_conditional_posterior_is_not_uniform_or_unconditional(self):
        p=Profile('learned_small');reach,posterior=history_mass(p)
        self.assertTrue(0<reach<1);self.assertAlmostEqual(sum(posterior),1,places=12)
        from gto.abstract.model import classes
        unconditional=[len(g)/1326 for g in classes()]
        self.assertGreater(max(abs(a-b) for a,b in zip(posterior,unconditional)),1e-5)

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'set QUALIFICATION_BUILD for native replay checks')
class IndependentNativeReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])
        from gto.native.training import NativeGame
        cls.game=NativeGame([100,100])
    def betting(self,stacks):
        r=self.rules.Rules(bb=2,ante_order='ante_first',stack_basis='before_ante',dead_eligibility='all_live',rake_rate=Fraction(0),rake_cap=None,no_flop_no_drop=True,cap_scope='whole_hand',rounding='floor',rake_ante=True)
        return self.rules.Betting(stacks,r)
    def test_own_public_only_policy_interface(self):
        p=Profile('learned_small');b=self.betting([100,100]);a=p.row(('pre',0,0),b,[48,49],[])
        # Different hidden worlds have exactly the same supplied observation.
        self.assertEqual(a,p.row(('pre',0,0),self.betting([100,100]),[48,49],[]))
        self.assertAlmostEqual(sum(w for _,w,_ in a),1)
        # actor is derived from preserved public ledger, not the supplied hidden world.
        self.assertEqual(p.row(None,b,[48,49],[]),[(0,1.,None)])
    def test_every_flop_teacher_is_seat_oriented(self):
        p=Profile('learned_small')
        for leaf,(nodes,offsets) in p.trees.items():
            parent=next(n for n in p.nodes if leaf in n['children']);self.assertEqual(p.hero_actor[leaf],parent['actor'])
            for node in nodes:
                if node['actor']>=0:self.assertEqual(node['seat'],p.hero_actor[leaf] if node['actor']==0 else 1-p.hero_actor[leaf])
    def test_short_one_chip_allin_has_unambiguous_id(self):
        b=self.betting([3,3]);act(b,1);act(b,1)
        self.assertEqual(b.round,1);self.assertEqual(legal(b),[1,3]);act(b,3)
        self.assertEqual(b.history[-1][2],-3);self.assertEqual(b.price,1)
        from gto.native.training import NativeGame
        s=self.native.NativeState(NativeGame([3,3]))
        for c in [0,1,2,3]:s.apply_action(c)
        s.apply_action(1);s.apply_action(1)
        for c in [4,5,6]:s.apply_action(c)
        self.assertEqual(s.legal_actions(),[1,3]);s.apply_action(3)
        self.assertEqual(s.audit()['history'],[list(x) for x in b.history])
    def test_all_legal_sizes_and_fold_refund(self):
        b=self.betting([100,100]);self.assertEqual(len(legal(b)),99);self.assertIn(8,legal(b))
        act(b,8);act(b,0);self.assertEqual(b.settle([[0],[0]],False)['net'],[2,-2])
    def test_independent_real_paths_both_contexts_and_arms(self):
        rng=random.Random(511)
        for name in ('learned_small','learned_large'):
            p=Profile(name)
            for context in ('rfi','vs_open'):
                for _ in range(48):
                    deck=rng.sample(range(52),9);tape={'seed':rng.getrandbits(128)}
                    for deviation in (False,True):
                        net,_=rollout(p,self.rules,self.native,self.game,deck,tape,context,deviation,True)
                        self.assertEqual(sum(net),0);self.assertTrue(all(-50<=v<=50 for v in net))

if __name__=='__main__':unittest.main()
