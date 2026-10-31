"""Common uniform+reached-range own signal for every compared policy."""
import ctypes as C
from gto.abstract.model import ints,doubles
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.flop_conditional import Observation
from gto.abstract.continuation_learning import ARMS,payoff
from gto.abstract.range_features import signal

def game(lib,m,pi,stage,book):
 r=frozen_reach(stage,pi,after_call=True);pot,stack=r['post_call_pot_bb'],r['remaining_stack_bb'];actor=r['hero_actor'];keys=[[signal(Observation(p,m['flop'],seat,pot,stack),book) for p in m['pairs']] for seat in (actor,1-actor)];hs,vs=[sorted(set(ks)) for ks in keys];hm={k:i for i,k in enumerate(hs)};vm={k:i for i,k in enumerate(vs)};hi=[hm[k] for k in keys[0]];vi=[vm[k] for k in keys[1]];bh,bv=len(hs),len(vs);out=(C.c_double*(bh*bv*2))()
 if lib.type_aggregate(m['n'],bh,bv,m['cards'],ints(m['labels']),ints(hi),ints(vi),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),out):raise ValueError('range-signal chance aggregation failed')
 lo=[[payoff(0,a,b,actor,pot,stack) for b in ARMS] for a in ARMS];slope=[[payoff(1,a,b,actor,pot,stack)-lo[i][j] for j,b in enumerate(ARMS)] for i,a in enumerate(ARMS)];tensor=[[[[out[(i*bv+j)*2]*lo[a][b]+out[(i*bv+j)*2+1]*slope[a][b] for b in range(4)] for a in range(4)] for j in range(bv)] for i in range(bh)]
 return {'hkeys':hs,'vkeys':vs,'tensor':tensor,'stage':stage,'flop':list(m['flop']),'sampling_error_bb':0,'numerical_guard_bb':1e-7,'scope':'same union23own/public/range-signal4plan game for all methods; NOT fullNLHE exploitability'}
