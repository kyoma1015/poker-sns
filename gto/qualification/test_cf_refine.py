import tempfile,unittest,random
from pathlib import Path
import numpy as np
from gto.qualification import active_chance as ac,stream_sampling as ss,public_chance_solver as pcs,cf_refine as cf,refine_checkpoint as codec
from gto.qualification.policy import sha
class Refine(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.lib=ac.build(cls.tmp.name)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def game(self):
  ns=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
  q=ss.Game(self.lib,ns,[dict(pcs.block(self.lib,[0,5,10,15,20],1.),stratum=(0,False,True))]);q.step();return q
 def test_prefix_projection_and_no_invented_split_history(self):
  for r in range(4):
   for ra in range(r+1):
    for public in (0,1,3,7):
     for signal in (0,139,655,1351):
      c=(public>>(3-r))*(169<<r)+(signal>>(3-r));self.assertEqual(cf.ancestor_code(c,r,ra),(public>>(3-ra))*(169<<ra)+(signal>>(3-ra)))
  q=self.game();rng=np.random.default_rng(19);q.R[:]=rng.random(q.S);q.A[:]=rng.random(q.S)
  class Parent:
   def values(self,k,key):
    key=cf.project(key,k,q.nodes,q.splits);j=q.keys[k].index(key);n=len(q.nodes[k]['children']);return q.policy()[q.base[k]+j*n:q.base[k]+(j+1)*n]
  chosen=(2,q.keys[2][0][0]);r=cf.change(q,[chosen],Parent())
  for k,n in enumerate(q.nodes):
   if n['actor']<0:continue
   size=len(q.keys[k])*len(n['children']);np.testing.assert_array_equal(q.R[q.base[k]:q.base[k]+size],r.R[r.base[k]:r.base[k]+size]);np.testing.assert_array_equal(q.A[q.base[k]:q.base[k]+size],r.A[r.base[k]:r.base[k]+size])
   for at,oldat in zip(r.active[:,k].ravel(),q.active[:,k].ravel()):np.testing.assert_allclose(r.policy()[at:at+len(n['children'])],q.policy()[oldat:oldat+len(n['children'])],atol=1e-14)
  self.assertTrue(np.all(r.R[r.base[2]+len(q.keys[2])*2:]==0))
 def test_delta_roundtrip_and_tamper_rejected(self):
  q=self.game();r=ss.Game(q.lib,q.nodes,q.blocks,q.splits,previous=q);r.step()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cp';meta=codec.encode(r,q,p);stub=ss.Game(q.lib,q.nodes,q.blocks,q.splits,previous=q);codec.decode(stub,q,p,meta)
   for f in ('R','A','prior','visits'):np.testing.assert_array_equal(getattr(r,f),getattr(stub,f))
   part=p/meta['records'][0]['parts'][0]['path'];part.write_bytes(part.read_bytes()+b'bad')
   with self.assertRaisesRegex(ValueError,'delta shard SHA'):codec.decode(stub,q,p,meta)
 def test_local_CF_gap_nonnegative_and_existing_split_not_reselected(self):
  q=self.game();rows=cf.scores(q,rounds=(3,));self.assertTrue(all(r['CF_gap']>0 and r['on_policy_reach']>=0 for r in rows))
  if rows:
   chosen=(rows[0]['node'],rows[0]['coarse']);q.splits.add(chosen);self.assertNotIn(chosen,[(r['node'],r['coarse']) for r in cf.scores(q,rounds=(3,))])
 def test_CF_gap_matches_independent_active_kernel_fine_gradients(self):
  q=self.game();pi=q.policy();allcodes=[(2,key[0]) for key in q.keys[2]]
  class Parent:
   def values(self,k,key):
    key=cf.project(key,k,q.nodes,q.splits);j=q.keys[k].index(key);n=len(q.nodes[k]['children']);return pi[q.base[k]+j*n:q.base[k]+(j+1)*n]
  r=cf.change(q,allcodes,Parent());r.evaluate_owner(r.policy(),1);expected={}
  for st,t,n,k in r.rows:
   if k!=2:continue
   for j,key in enumerate(r.keys[k]):
    if not key[1]:continue # obsolete unsplit rows have zero CF
    expected.setdefault(key[0],[]).append(r.grad[st+j*n:st+(j+1)*n])
  expected={c:float(np.max(v,axis=1).sum()-np.max(np.sum(v,axis=0))) for c,rows in expected.items() for v in [np.array(rows)]}
  actual={row['coarse']:row['CF_gap'] for row in cf.scores(q,rounds=(3,))}
  for c,v in expected.items():self.assertAlmostEqual(actual.get(c,0.),v,places=11)
