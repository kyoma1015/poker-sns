import unittest
from gto.native.build_response_controls import patched_source
from gto.native.build_reconstructed import decode
class SourceScope(unittest.TestCase):
 def test_source_pinned_hook_leaves_native_fast_path_unchanged(self):
  original=decode('g12_next_solver_disk.cc').decode();patched=patched_source()
  start=' double native_episode(';end=' void run()'
  def native(source):return source[source.index(start):source.index(end,source.index(start))]
  self.assertEqual(native(original),native(patched))
  self.assertEqual(patched.count('exact_controls=s.attr("exact_action_values")()'),1)
  self.assertLess(patched.index('exact_controls=s.attr'),patched.index('s.attr("apply_action")(sampled_action)'))
if __name__=='__main__':unittest.main()
