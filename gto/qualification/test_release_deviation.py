import math,os,unittest
from gto.qualification.release_deviation import binomial_lower,nuts
class Binomial(unittest.TestCase):
    def test_independent_closed_form_endpoints_and_one_success(self):
        self.assertEqual(binomial_lower(0,100),0)
        for n in (1,10,100,8192):
            self.assertAlmostEqual(binomial_lower(n,n),.001**(1/n),places=12)
            self.assertAlmostEqual(binomial_lower(1,n),1-(1-.001)**(1/n),places=12)
    def test_counts_rejected(self):
        with self.assertRaises(ValueError):binomial_lower(2,1)
@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class Nuts(unittest.TestCase):
    def test_no_hidden_card_input_and_independent_all_opponent_enumeration(self):
        import itertools
        from gto.qualification.build import load
        _,native=load(os.environ['QUALIFICATION_BUILD'])
        for own,board in [([48,44],[40,36,32,1,6]),([0,5],[8,13,18,23,28]),([48,49],[0,5,10,15,20])]:
            available=set(range(52))-set(own)-set(board);r=native.rank7(own+board)
            expected=max(native.rank7(list(h)+board) for h in itertools.combinations(available,2))<=r
            self.assertEqual(nuts(native,own,board),expected)
        with self.assertRaises(ValueError):nuts(native,[0,1],[0,4,8,12,16])
if __name__=='__main__':unittest.main()
