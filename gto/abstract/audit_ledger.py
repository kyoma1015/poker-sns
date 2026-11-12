"""Independent actual Betting ledger versus abstract continuation settlement."""
import ctypes as C,hashlib,importlib.util,itertools,json,random,subprocess,sys,tempfile
from pathlib import Path
from gto.native.build_reconstructed import decode,AUXILIARY
from gto.abstract.model import tree,ints,IP,ROOT
from gto.native.ev_audit import rank_five
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--build-directory',type=Path,required=True)
args=parser.parse_args()
source=decode('pokerid_rules.py');assert hashlib.sha256(source).hexdigest()==AUXILIARY['pokerid_rules.py'][1]
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);path=root/'audit_rules.py';path.write_bytes(source)
 spec=importlib.util.spec_from_file_location('abstract_audit_rules',path);rules=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rules;spec.loader.exec_module(rules)
 checked_edges=0
 for node in tree():
  if node['actor']<0:continue
  b=rules.Betting([100,100],rules.Rules(bb=2,bba=0,ante_order='ante_first',stack_basis='before_ante',dead_eligibility='all_live',rake_rate=__import__('fractions').Fraction(0),rake_cap=None,no_flop_no_drop=True,cap_scope='whole_hand',rounding='floor',rake_ante=True))
  for action in node['history']:b.act(1 if action=='call' else int(action.split('_')[-1]))
  assert b.actor==node['actor'] and b.street==node['contributions']
  for action in node['actions']:
   raw=0 if action=='fold' else 1 if action in ('check','call') else int(action.split('_')[-1])
   assert raw in b.legal();checked_edges+=1
 wrapper=root/'audit.cc';wrapper.write_text('#include "'+str(ROOT/'gto/abstract/core.cc')+'"\nextern "C" double audit(const int*c,int x){V a(c,c+2),b(c+2,c+4),board(c+4,c+9),aa=a,bb=b;aa.insert(aa.end(),board.begin(),board.end());bb.insert(bb.end(),board.begin(),board.end());auto ra=rank7(aa),rb=rank7(bb);int sign=(ra>rb)-(ra<rb);return x==100?100*sign:continuation(a,b,board,sign,x);}')
 target=root/'audit.so';subprocess.run(['c++','-std=c++17','-O2','-shared','-fPIC',str(wrapper),'-I'+str(args.build_directory.resolve()),'-o',str(target)],check=True)
 lib=C.CDLL(str(target));lib.audit.argtypes=[IP,C.c_int];lib.audit.restype=C.c_double
 def strong(h,board):
  cs=h+board[:3];return rank_five(cs)[0]>=1 or max(sum(c%4==s for c in cs) for s in range(4))>=4
 rng=random.Random(880017);checked=0
 for _ in range(200):
  cards=rng.sample(range(52),9)
  for swapped in (False,True):
   h0,h1=cards[:2],cards[2:4]
   if swapped:h0,h1=h1,h0
   board=cards[4:];world=h0+h1+board
   ranks=[max(rank_five(list(c)) for c in itertools.combinations(h+board,5)) for h in (h0,h1)]
   for x,path in ((2,[1,1]),(5,[5,1]),(18,[5,18,1]),(42,[5,18,42,1]),(100,[5,18,42,100,1])):
    b=rules.Betting([100,100],rules.Rules(bb=2,bba=0,ante_order='ante_first',stack_basis='before_ante',dead_eligibility='all_live',rake_rate=__import__('fractions').Fraction(0),rake_cap=None,no_flop_no_drop=True,cap_scope='whole_hand',rounding='floor',rake_ante=True))
    for action in path:b.act(action)
    if x<100:
     b.next_round();bb_bet=strong(h1,board);sb_call=strong(h0,board)
     sb_bet=sb_call or min(c//4 for c in h0)>max(c//4 for c in board[:3])
     if bb_bet:b.act(x);b.act(1 if sb_call else 0)
     else:
      b.act(1);b.act(x if sb_bet else 1)
      if sb_bet:b.act(1 if strong(h1,board) else 0)
    while not b.done:
     if b.actor is None:b.next_round()
     else:b.act(1)
    net=b.settle(ranks,True)['net'];assert sum(net)==0
    actual=lib.audit(ints(world),x)
    assert actual==net[0],(x,world,net,actual)
    checked+=1
 print(json.dumps({'result':'PASS','legal_preflop_edges':checked_edges,'native_controller_vs_independent_ledger_payoffs':checked,'allin_included':True,'cost_basis':'before posting blinds','seed':880017}))
