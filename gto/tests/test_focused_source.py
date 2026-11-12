import unittest
from gto.native.build_reconstructed import decode
from gto.native.build_focused import patched_source
from pathlib import Path
class FocusedSource(unittest.TestCase):
 def test_targeted_pin_and_true_vs_sampling_reach_are_explicit(self):
  # Reconstruct existing targeted transformation without build/network.
  source=decode('g12_next_solver_disk.cc').decode().replace('#include <vector>','#include <algorithm>\n#include <vector>',1)
  needle='auto sampling=current;for(auto& d:sampling)d=epsilon/sampling.size()+(1-epsilon)*d;';i=source.rindex(needle)
  replacement='std::vector<int64_t> proposal_actions;for(uint64_t a=0;a<copy.n;++a)proposal_actions.push_back(action(stored,a));int proposal_raises=0;for(auto row:s.engine.history)if(row[2]!=0&&row[2]!=1)++proposal_raises;auto sampling=ordinary_proposal(current,epsilon,proposal_actions,s.engine.round,proposal_raises);'
  source=source[:i]+replacement+source[i+len(needle):]
  source=source.replace('namespace pokerid11 {','namespace pokerid11 {\n'+Path('gto/native/targeted_sampling.h').read_text(),1)
  source=source.replace('PYBIND11_MODULE(pokerid_g12,m){','PYBIND11_MODULE(pokerid_targeted,m){\nm.def("targeted_sampling", &pokerid11::ordinary_proposal);',1)
  patched=patched_source(source)
  self.assertIn('multiply(opp,pq.first),multiply(reach,pq.second)',patched)
  self.assertIn('return ratio(child,pq.first,pq.second)',patched)
  # No change to native information/ledger/state header; generic path identical.
  def generic(s):return s[s.index(' double episode('):s.index(' double native_episode(')]
  self.assertEqual(generic(source),generic(patched))
if __name__=='__main__':unittest.main()
