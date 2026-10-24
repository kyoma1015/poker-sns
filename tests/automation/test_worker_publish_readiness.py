"""Force source-publication latency without weakening inherited assertions."""
from pathlib import Path
import sys,time,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/automation')]
import test_worker_tree_boundaries as inherited
class WorkerPublishReadiness(unittest.TestCase):
 def test_partial_write_cannot_be_observed_as_complete_source(self):
  original=Path.write_text
  def delayed(path,data,*args,**kwargs):
   if path.name=='owned-worker':
    for name in ('source.py','source.pending'):
     target='Path("'+name+'").write_text("uncommitted=1\\n")'
     replacement='p=Path("'+name+'");f=p.open("w");time.sleep(.15);f.write("uncommitted=1\\n");f.close()'
     data=data.replace(target,replacement)
   return original(path,data,*args,**kwargs)
  test=inherited.WorkerTreeBoundaries('test_parent_death_during_stdin_retains_file_and_unknown_worker')
  read=Path.read_bytes;reads=[]
  def snapshot(path):
   if path.name=='source.py':
    reads.append(True)
    if len(reads)==2:time.sleep(.2)
   return read(path)
  with patch.object(Path,'write_text',delayed),patch.object(Path,'read_bytes',snapshot):test.test_parent_death_during_stdin_retains_file_and_unknown_worker()
if __name__=='__main__':unittest.main()
