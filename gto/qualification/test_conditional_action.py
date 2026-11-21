import os,unittest
from gto.qualification.conditional_action import mixed_value,restricted_gain,AllinConditioner,integrated_rollout
from gto.qualification.build import load
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,legal
from gto.native.training import NativeGame

class IndependentFiniteOracle(unittest.TestCase):
    def test_mixture_conditioning_preserves_finite_distribution_expectation(self):
        weights=[.25,.75];calls=[.9,.2];values=[50.,-50.];fold=3.
        direct=sum(w*((1-c)*fold+c*v) for w,c,v in zip(weights,calls,values))
        mass=sum(w*c for w,c in zip(weights,calls))
        conditional=sum(w*c*v for w,c,v in zip(weights,calls,values))/mass
        self.assertAlmostEqual(direct,mixed_value(fold,mass,conditional),places=12)
        oldvar=sum(w*((1-c)*(fold-direct)**2+c*(v-direct)**2) for w,c,v in zip(weights,calls,values))
        newvar=sum(w*c/mass*(mixed_value(fold,mass,v)-direct)**2 for w,c,v in zip(weights,calls,values))
        self.assertLessEqual(newvar,mass*oldvar+1e-12)

    def test_restricted_br_integrates_hidden_worlds_before_max(self):
        from gto.abstract.matched_history import pure_response
        nodes=[dict(actor=0,children=[1,2]),dict(actor=-1,children=[],c0=-1,c1=2),dict(actor=-1,children=[],c0=1,c1=-2)]
        g=dict(nodes=nodes,worlds=[dict(mass=.5,equity=0.),dict(mass=.5,equity=1.)],info=[0,0,0,0,0,0])
        _,br=pure_response(g,[.5,.5],0)
        row=dict(sampled_frequencies={0:.5,1:.5},action_ev_bb={'0':{'interval':[0,0]},'1':{'interval':[0,0]}})
        result=restricted_gain({'AA':row},[0,1],[1.])
        self.assertEqual(br,0);self.assertEqual(result['gain_upper_bb'],0)
        self.assertIsNone(result['complete_br_upper_bb'])

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class NativeConditionalOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def test_call_posterior_mass_preserves_card_removal_and_source_open_weights(self):
        import itertools,random
        rules=self.rules;native=self.native
        def op(h):return .2 if max(c//4 for c in h)>=10 else .1
        def cb(h):return .75 if max(c//4 for c in h)>=10 else .25
        def cs(h):return .4 if h[0]//4==h[1]//4 else .2
        class Toy:
            id={'key':'exact-suit-orbit'}
            def __init__(self):self.rules=rules;self.native=native
            def row(self,o,average=True):
                if not o.history:return [1-op(o.own) if a==0 else op(o.own) if a==8 else 0 for a in o.actions]
                call=cb(o.own) if o.actor==1 else cs(o.own)
                return [1-call,call]
        model=AllinConditioner(Toy())
        for own in ((48,49),(0,4)):
            others=[h for h in itertools.combinations(range(52),2) if not set(h).intersection(own)]
            expected_rfi=sum(cb(h) for h in others)/1225
            expected_vs=sum(op(h)*cs(h) for h in others)/sum(op(h) for h in others)
            for context,expected in (('rfi',expected_rfi),('vs_3bb_open',expected_vs)):
                self.assertAlmostEqual(model.mass(own,context),expected,places=12)
                lo,hi=model.bounds(own,context)
                for seed in range(4):
                    value=model.value(own,context,random.Random(seed))
                    self.assertGreaterEqual(value,lo-1e-12);self.assertLessEqual(value,hi+1e-12)

    def test_terminal_allin_integral_equals_native_probability_weighted_payoffs(self):
        native=self.native;rules=self.rules
        class Toy:
            id={'key':'exact-suit-orbit'}
            def __init__(self):self.rules=rules;self.native=native
            def row(self,o,average=True):return [.25,.75] if tuple(o.actions)==(0,1) else [1/len(o.actions)]*len(o.actions)
        s=Toy()
        for deck in ([48,49,44,45,4,9,14,19,24],[48,49,0,1,8,13,18,23,28],[48,49,0,1,4,9,14,19,24]):
            payoffs=[]
            for action in (0,1):
                state=native.NativeState(NativeGame([100,100]))
                for c in deck[:4]:state.apply_action(c)
                state.apply_action(102);state.apply_action(action)
                while state.is_chance_node():state.apply_action(deck[4+len(state.audit()['board'])])
                payoffs.append(state.returns()[0]/2)
            expected=.25*payoffs[0]+.75*payoffs[1]
            import random
            self.assertEqual(integrated_rollout(s,deck,random.Random(1),[102])[0],expected)

if __name__=='__main__':unittest.main()
