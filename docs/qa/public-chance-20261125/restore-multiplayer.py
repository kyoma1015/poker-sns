import copy,gzip,json,gc
from pathlib import Path
from gto.qualification.multiplayer_joint import SparseJoint
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
_,native=load('/tmp/native-qualification');records=[]
for n in (6,9):
 for seed in (17124101,17124102):
  p=Path(f'docs/qa/sparse-generalization-20261124/multiplayer-lazy/{n}max-{seed}-final.json.gz');state=json.loads(gzip.decompress(p.read_bytes()));old=copy.deepcopy(state['identity']);assert state['digest']==digest({k:v for k,v in state.items() if k!='digest'});assert old['source_sha256']==sha(Path('gto/qualification/multiplayer_joint.py'))
  game=NativeGame(old['config']['stacks'],bba=2,rake_num=1,rake_den=20)
  q=SparseJoint(native,game,seed=seed,average_mode='lazy',max_nodes=20000,max_infosets=20000,max_seconds=2)
  for k,v in q.identity.items():
   if k!='native_binary_sha256':assert old[k]==v,k
  migrated=dict(old,native_binary_sha256=sha(Path(native.__file__)),migration=dict(checkpoint_file_sha256=sha(p),old_native_binary=old['native_binary_sha256']))
  state['identity']=migrated;state['digest']=digest({k:v for k,v in state.items() if k!='digest'});q.identity=migrated;q.restore(state)
  other=SparseJoint(native,game,seed=seed,average_mode='lazy',max_nodes=20000,max_infosets=20000,max_seconds=2);other.identity=migrated;other.restore(state)
  q.step();other.step();assert q.state()==other.state()
  records.append(dict(players=n,seed=seed,old_iterations=state['t'],checkpoint_file_sha256=sha(p),source_match=True,actual_R_A_RNG_parents_history_restored=True,new_binary_next_step_bit_exact=True,strict_old_binary_resume=False,new_native_binary_sha256=migrated['native_binary_sha256']))
  del state,q,other;gc.collect()
atomic('docs/qa/public-chance-20261125/multiplayer-recovery.json',dict(records=records));print(records)
