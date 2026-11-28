import copy,json,math,os,random,unittest
from gto.qualification.action_baseline import ActionBaselineSolver,general_updates,proposal
from gto.qualification.average_support import AverageSupportSolver
from gto.qualification.build import load

class GeneralOracle(unittest.TestCase):
    def test_general_pi_q_cf_and_average_with_zero_opponent_targets(self):
        from gto.abstract.matched_history import python_oracle
        ns=[dict(actor=0,children=[1,2]),dict(actor=1,children=[3,4]),
            dict(actor=-1,children=[],c0=2,c1=0),dict(actor=0,children=[5,6]),
            dict(actor=-1,children=[],c0=-3,c1=0),dict(actor=-1,children=[],c0=5,c1=0),dict(actor=-1,children=[],c0=-7,c1=0)]
        g=dict(nodes=ns,worlds=[dict(mass=1.,equity=0.)],info=[0,2,0,4,0,0,0])
        for pi in ([1.,0.,.3,.7,0.,1.],[0.,1.,.3,.7,.4,.6],[.3,.7,.4,.6,.2,.8]):
            oracle=python_oracle(g,pi)
            for owner in (0,1):
                gradients=[0.]*6;avg=[0.]*6
                def walk(k,mass,qprefix,reach,records,avgs):
                    n=ns[k]
                    if n['actor']<0:
                        for offset,row,delta,_ in general_updates(records,n['c0']*(1 if owner==0 else -1)):
                            for a,x in enumerate(delta):gradients[offset+a]+=mass*x
                        for offset,row,w in avgs:
                            for a,p in enumerate(row):avg[offset+a]+=mass*w*p
                        return
                    p=n['actor'];offset=g['info'][k];row=pi[offset:offset+2];q=[.45,.55]
                    av=avgs+[(offset,row,reach[p]/qprefix)] if p!=owner else avgs
                    for a,c in enumerate(n['children']):
                        r=reach[:];r[p]*=row[a]
                        rec=(offset,row,a,q[a],reach[1-owner]/qprefix,[1.3,-2.1],p==owner)
                        walk(c,mass*q[a],qprefix*q[a],r,records+[rec],av)
                walk(0,1.,1.,[1.,1.],[],[])
                for node in (0,1,3):
                    for a in (0,1):
                        i=g['info'][node]+a
                        if ns[node]['actor']==owner:self.assertAlmostEqual(gradients[i],oracle['grad'][i],places=11)
                        else:self.assertAlmostEqual(avg[i],oracle['avg'][i],places=11)

    def test_proposal_has_full_support_and_normalization(self):
        for target in (False,True):
            for owner in (False,True):
                q=proposal([1.,0.,0.],(0,1,8),'rfi',owner,target)
                self.assertAlmostEqual(sum(q),1)
                if owner or target:self.assertTrue(all(p>0 for p in q))

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class WarmResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def test_prior_action_predictions_are_used_without_hidden_cards(self):
        from gto.qualification.native_mccfr import betting
        from gto.qualification.public_response import observe
        from gto.qualification.action_baseline import public_spot
        from gto.qualification.policy import act
        s=ActionBaselineSolver(self.rules,self.native,baseline=True,targeted=True)
        b=betting(self.rules);o=observe(b,[48,49],[])
        self.assertEqual(public_spot(o),'rfi')
        self.assertEqual(s.baseline(o,0)[o.actions.index(102)],s.predictions['rfi']['AA']['action_ev_bb']['102']['mean'])
        act(b,8);self.assertEqual(public_spot(observe(b,[48,49],[])),'vs_3bb_open')
        act(b,22);self.assertEqual(public_spot(observe(b,[48,49],[])),'vs_10bb_3bet')

    def test_warm_preserves_corrected_R_S_and_exact_resume(self):
        old=AverageSupportSolver(self.rules,self.native)
        for _ in range(8):old.step()
        data=old.snapshot();before=copy.deepcopy(data)
        a=ActionBaselineSolver(self.rules,self.native,baseline=True,targeted=True);a.warm(data)
        self.assertEqual(a.rows,old.rows);self.assertEqual(a.rng.getstate(),old.rng.getstate());self.assertEqual(data,before)
        for _ in range(8):a.step()
        b=ActionBaselineSolver(self.rules,self.native,baseline=True,targeted=True);b.restore(json.loads(json.dumps(a.snapshot())))
        for _ in range(4):a.step();b.step()
        self.assertEqual(a.snapshot(),b.snapshot())

if __name__=='__main__':unittest.main()
