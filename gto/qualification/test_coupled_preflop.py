"""Independent tiny-game and physical-card oracles for coupled payoffs."""
import itertools,os,unittest
import numpy as np
from gto.abstract import model
from gto.qualification.range_continuation import load_kernel,kernel,HOLES,INDEX
from gto.qualification.coupled_preflop import candidate

# Two private types, root SB decision followed by BB response; asymmetric chance.
NODES=[dict(actor=0,actions=['a','b'],children=[1,6]),dict(actor=1,actions=['c','d'],children=[2,5]),dict(actor=0,actions=['e','f'],children=[3,4])]+[dict(actor=-1,actions=[],children=[]) for _ in range(4)]
P=np.asarray([[.3,.2],[.1,.4]])
LEAF=np.zeros((7,2,2));LEAF[3]=[[3,-2],[1,4]];LEAF[4]=[[-1,2],[-3,1]];LEAF[5]=[[2,1],[-1,-2]];LEAF[6]=-.5

def oracle(iterations):
    regret=np.zeros((7,3,2));average=regret.copy();decisions=[0,1,2]
    paths={0:[],1:[(0,0)],2:[(0,0),(1,0)]}
    def value(v,i,j,s):
        if NODES[v]['actor']<0:return LEAF[v,i,j]
        h=i if NODES[v]['actor']==0 else j
        return sum(s[v,a,h]*value(c,i,j,s) for a,c in enumerate(NODES[v]['children']))
    def reach(v,owner,h,s):
        result=1.
        for parent,a in paths[v]:
            if NODES[parent]['actor']==owner:result*=s[parent,a,h]
        return result
    for _ in range(iterations):
        s=np.zeros_like(regret)
        for v in decisions:
            r=np.maximum(regret[v,:2],0);z=r.sum(axis=0);s[v,:2]=np.divide(r,z,out=np.full((2,2),.5),where=z>0)
        for v in decisions:
            owner=NODES[v]['actor']
            for h in range(2):
                cf=[]
                for child in NODES[v]['children']:
                    total=0.
                    for other in range(2):
                        i,j=(h,other) if owner==0 else (other,h)
                        total+=P[i,j]*reach(v,1-owner,other,s)*value(child,i,j,s)
                    cf.append(total)
                expected=np.dot(s[v,:2,h],cf)
                regret[v,:2,h]+=(1 if owner==0 else -1)*(np.asarray(cf)-expected)
                average[v,:2,h]+=reach(v,owner,h,s)*s[v,:2,h]
    result=np.zeros_like(regret)
    for v in decisions:result[v,:2]=average[v,:2]/average[v,:2].sum(axis=0)
    profile=sum(P[i,j]*value(0,i,j,result) for i in range(2) for j in range(2))
    br=[]
    for owner in (0,1):
        owned=[v for v in decisions if NODES[v]['actor']==owner];values=[]
        for choices in itertools.product(range(2),repeat=2*len(owned)):
            s=result.copy()
            for k,v in enumerate(owned):
                s[v]=0
                for h in range(2):s[v,choices[k*2+h],h]=1
            values.append(sum(P[i,j]*value(0,i,j,s) for i in range(2) for j in range(2)))
        br.append(max(values) if owner==0 else min(values))
    return result,profile,br

@unittest.skipUnless(os.environ.get('RANGE_BUILD'),'compiled kernel required')
class Oracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lib=load_kernel(os.environ['RANGE_BUILD']+'/range.so')
    def test_regret_average_and_information_constrained_br(self):
        for iters in (1,2,7,100):
            s,ev,br=oracle(iters);actual=model.solve(self.lib,LEAF.ravel().tolist(),P.ravel().tolist(),NODES,iterations=iters,n=2)
            np.testing.assert_allclose(actual['strategy'],s.ravel(),atol=2e-14)
            np.testing.assert_allclose([actual['profile_sb_ev_bb'],actual['br_sb_ev_bb'],actual['br_bb_min_sb_ev_bb']],[ev/2,br[0]/2,br[1]/2],atol=2e-14)
    def test_sparse_card_removal_and_range_scaling(self):
        board=[40,41,42];r=[[0.]*1326 for _ in range(2)]
        for h,w in [((0,1),2),((2,3),3),((40,44),99)]:r[0][INDEX[h]]=w
        for h,w in [((0,4),5),((5,6),7)]:r[1][INDEX[h]]=w
        p,s,b,m=kernel(self.lib,board,r);expected=np.zeros(64);mass=0
        for i,x in enumerate(r[0]):
            for j,y in enumerate(r[1]):
                if x*y and not set(HOLES[i]+HOLES[j]).intersection(board) and not set(HOLES[i]).intersection(HOLES[j]):expected[b[i]*8+b[j]]+=x*y;mass+=x*y
        self.assertEqual(m,mass);np.testing.assert_allclose(p,expected/mass)
        pp,ss,_,mm=kernel(self.lib,board,[[x*17 for x in r[0]],r[1]])
        np.testing.assert_allclose(pp,p);np.testing.assert_allclose(ss,s);self.assertAlmostEqual(mm,m*17)
    @unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
    def test_actual_preflop_posterior_matches_bayes_with_blockers(self):
        from gto.qualification.preflop_release_solver import load_policy
        from gto.qualification.range_continuation import RangePolicy
        from gto.qualification.coupled_preflop import PRIOR
        from gto.qualification.native_mccfr import betting
        from gto.qualification.policy import act
        from gto.qualification.public_response import observe
        p=RangePolicy(load_policy(os.environ['QUALIFICATION_BUILD'],PRIOR),self.lib)
        b=betting(p.rules);expected=np.ones((2,1326))
        for action in (8,22,1):
            for i,h in enumerate(HOLES):
                o=observe(b,h,[]);expected[b.actor,i]*=p.base.row(o,True)[o.actions.index(action)]
            act(b,action)
        expected/=expected.sum(axis=1)[:,None]
        np.testing.assert_allclose(p.ranges(tuple(b.history),(40,41,42)),expected,atol=1e-15)
        own=(0,1);o=observe(b,own,(40,41,42));weights=expected[1-o.actor].copy()
        for i,h in enumerate(HOLES):
            if set(h).intersection(own+o.board):weights[i]=0
        weights/=weights.sum()
        np.testing.assert_allclose(p.posterior(o),weights,atol=1e-15)

    @unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
    def test_epoch_rebuilds_ranges_instead_of_reusing_stale_cache(self):
        from gto.qualification.preflop_release_solver import load_policy
        from gto.qualification.range_continuation import RangePolicy
        from gto.qualification.coupled_preflop import PRIOR
        from gto.qualification.native_mccfr import betting
        from gto.qualification.policy import act
        p=RangePolicy(load_policy(os.environ['QUALIFICATION_BUILD'],PRIOR),self.lib)
        b=betting(p.rules);act(b,8);hist=tuple(b.history)
        old=np.array(p.ranges(hist,())[0]);strategy=list(p.base.strategy)
        for j in range(3):strategy[j*169:(j+1)*169]=[float(j==2)]*169
        q=candidate(p,dict(strategy=strategy),1.,dict(schema='oracle'))
        updated=np.array(q.ranges(hist,())[0])
        np.testing.assert_allclose(updated,np.full(1326,1/1326))
        self.assertFalse(np.allclose(updated,old))
        np.testing.assert_array_equal(p.ranges(hist,())[0],old)
        self.assertNotEqual(p.policy_digest,q.policy_digest)

    def test_endogenous_response_changes_game_without_regret_bug(self):
        # Two-type Bayes posterior: action likelihood, not unweighted hand prior.
        prior=np.array([.5,.5]);old=np.array([.9,.1]);new=np.array([.1,.9])
        a=prior*old/(prior@old);b=prior*new/(prior@new)
        self.assertAlmostEqual(a[0],.9);self.assertAlmostEqual(b[0],.1)
        # A receiver guesses the more probable type. Updating sender frequencies
        # reverses the optimal continuation; fixed-payoff CFR cannot account for it.
        frozen_action=int(np.argmax(a));updated_action=int(np.argmax(b))
        self.assertNotEqual(frozen_action,updated_action)
        self.assertAlmostEqual(b[updated_action]-b[frozen_action],.8)

if __name__=='__main__':unittest.main()
