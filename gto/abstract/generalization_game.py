"""Same exact4arm game with public/own richer signals; no existing CFR writes."""
import ctypes as C
from gto.abstract import continuation_game as base
from gto.abstract.model import ints,doubles
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.flop_conditional import Observation
from gto.abstract.continuation_learning import ARMS,payoff
from gto.abstract.generalization_features import signal

def game(lib,m,pi,stage,strength):
 r=frozen_reach(stage,pi,after_call=True);pot,stack=r['post_call_pot_bb'],r['remaining_stack_bb'];actor=r['hero_actor'];keys=[[signal(Observation(p,m['flop'],seat,pot,stack),strength) for p in m['pairs']] for seat in (actor,1-actor)];hs,vs=[sorted(set(k)) for k in keys];hi=[hs.index(k) for k in keys[0]];vi=[vs.index(k) for k in keys[1]];bh,bv=len(hs),len(vs);out=(C.c_double*(bh*bv*2))()
 if lib.type_aggregate(m['n'],bh,bv,m['cards'],ints(m['labels']),ints(hi),ints(vi),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),out):raise ValueError('rich exact chance failed')
 low=[[payoff(0,a,b,actor,pot,stack) for b in ARMS] for a in ARMS];slope=[[payoff(1,a,b,actor,pot,stack)-low[i][j] for j,b in enumerate(ARMS)] for i,a in enumerate(ARMS)]
 tensor=[[[[out[(i*bv+j)*2]*low[a][b]+out[(i*bv+j)*2+1]*slope[a][b] for b in range(4)] for a in range(4)] for j in range(bv)] for i in range(bh)]
 return {'hkeys':hs,'vkeys':vs,'tensor':tensor,'stage':stage,'flop':list(m['flop']),'chance_mass':[out[i*2] for i in range(bh*bv)],'sampling_error_bb':0,'numerical_guard_bb':1e-7,'scope':'common rich own/public signal game,4whole plans; NO real-game GTO guarantee'}
