import unittest
from gto.native.ev_audit import rank_five,independent_net,replay_debits
class Ledger(unittest.TestCase):
 def config(self):return {'stacks':[100,100],'rules':{'bba':0,'rake_rate':'0'}}
 def state(self,spent,folded,board=None,holes=None):return {'initial':[100,100],'remaining':[100-v for v in spent],
  'live':spent,'dead':[0,0],'folded':folded,'board':board or [],'holes':holes or [[],[]]}
 def test_blind_and_raise_fold_costs_counted_once(self):
  for spent,folded,expected in (([1,2],[True,False],[-1,1]),([5,2],[False,True],[2,-2]),([5,18],[True,False],[-5,5]),([100,18],[False,True],[18,-18])):
   self.assertEqual(independent_net(self.state(spent,folded),self.config()),expected)
 def test_showdown_refund_and_tie(self):
  # AA over KK on low unpaired board, no flush.
  self.assertEqual(independent_net(self.state([100,18],[False,False],[0,5,10,20,25],[[48,49],[44,45]]),self.config()),[18,-18])
  # Royal flush shared board; uncalled excess refunded before splitting.
  self.assertEqual(independent_net(self.state([100,18],[False,False],[32,36,40,44,48],[[0,1],[4,5]]),self.config()),[0,0])
 def test_public_history_replays_blinds_calls_and_street_costs(self):
  self.assertEqual(replay_debits([[0,0,0,2,2]],[100,100],2),([99,98],[True,False]))
  self.assertEqual(replay_debits([[0,0,5,5,3],[0,1,18,18,13],[0,0,0,18,13]],[100,100],2),([95,82],[True,False]))
  h=[[0,0,1,2,2],[0,1,1,2,2],[1,1,10,10,10],[1,0,1,10,10]]
  self.assertEqual(replay_debits(h,[100,100],2),([88,88],[False,False]))
  state=self.state([2,2],[True,False]);state['history']=[[0,0,0,2,2]]
  config=self.config();config['rules']['bb']=2
  with self.assertRaises(ValueError):independent_net(state,config)
 def test_rank_categories_and_wheel(self):
  examples=[[48,0,4,8,12],[48,49,50,51,0],[48,49,50,0,1],[0,8,20,32,44],
            [0,5,10,15,16],[0,1,2,8,13],[0,1,4,5,8],[0,1,8,13,18],[0,5,10,19,24]]
  self.assertEqual([rank_five(c)[0] for c in examples],[8,7,6,5,4,3,2,1,0])
  self.assertEqual(rank_five(examples[0]),(8,5))
 def test_unsupported_or_corrupted_ledger_refused(self):
  state=self.state([1,2],[True,False]);state['live']=[0,2]
  with self.assertRaises(ValueError):independent_net(state,self.config())
  config=self.config();config['rules']['bba']=2
  with self.assertRaises(ValueError):independent_net(self.state([1,2],[True,False]),config)
if __name__=='__main__':unittest.main()
