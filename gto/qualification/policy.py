"""Evaluation-only totalization; observations contain own cards and public state only."""
import hashlib,json,math
from pathlib import Path
from gto.abstract import model,street_tree,fullsupport
from gto.abstract.factorial_transfer import category
from gto.hand169 import hand_class,CLASSES
from gto.native.hand169_bridge import card_name
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def hand(cards):return CLASSES.index(hand_class([card_name(c) for c in cards]))

def legal(b):
    if b.done or b.actor is None:return []
    p=b.actor;out=[0,1] if b.price>b.street[p] else [1]
    ceiling=b.street[p]+b.remaining[p]
    if b.has_raise_right(p) and any(q!=p and not b.folded[q] and b.remaining[q]>0 for q in range(b.n)) and ceiling>b.price:
        minimum=b.price+b.last_full
        out.extend(3 if target==1 else target+2 for target in (range(minimum,ceiling+1) if ceiling>=minimum else [ceiling]))
    return out

def act(b,action):
    if action not in legal(b):raise ValueError('illegal normalized action')
    if action in (0,1):b.act(action)
    else:
        p=b.actor;target=1 if action==3 else action-2;old=b.price
        b._pay_live(p,target-b.street[p]);b.price=target
        if target-old>=b.last_full:b.last_full=target-old
        b.seen[p]=b.price;b.history.append((b.round,p,-3 if action==3 else target,b.price,b.last_full))
        b._choose_pending((p+1)%b.n,include_start=True)
    while not b.done and b.actor is None:b.next_round()

class Profile:
    RECIPE='total-native-evaluation-v1:ceil-chip-wagers;public-min-alias-child;unknown-check-fold;turn-river-check-fold'
    def __init__(self,name):
        self.name=name
        self.paths=['docs/qa/suit-exact-preflop-20261106/results.json','docs/qa/independent-preflop-20261105/teacher.json','docs/qa/independent-preflop-20261105/protocol.json']
        source=json.loads((ROOT/self.paths[0]).read_text());teacher=json.loads((ROOT/self.paths[1]).read_text())
        self.pi=source['complete_preflop_policies'][name];self.teacher=teacher['profiles'][name];self.nodes=model.tree();self.trees={};self.hero_actor={}
        fractions=json.loads((ROOT/self.paths[2]).read_text())['variants'][name]
        for i,node in enumerate(self.nodes):
            if node['actor']<0 and node['matched'] and node['value']<100:
                parent=next(p for p in self.nodes if i in p['children']);self.hero_actor[i]=parent['actor']
                nodes=street_tree.tree(node['value'],50-node['value']/2,parent['actor'],fractions)['nodes'];offset=[];n=0
                for row in nodes:offset.append(n);n+=8*len(row['actions'])
                self.trees[i]=(nodes,offset)
        self.identity={'model':name,'recipe':self.RECIPE,'sources':{p:sha(ROOT/p) for p in self.paths},'policy_source_sha256':sha(Path(__file__)), 'rules_source_sha256':sha(ROOT/'handoff/gto/compressed/g11_rules_embed.h.zlib.b64'),'native_state_sha256':sha(ROOT/'handoff/gto/g12_next/g11_native_state.h')}
        self.digest=hashlib.sha256(json.dumps(self.identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def row(self,cursor,b,own,board):
        """No opponent/future-card argument is available to the policy."""
        if cursor is None or b.round>=2:return [(0 if b.price>b.street[b.actor] else 1,1.,cursor)]
        phase,index,local=cursor
        if phase=='pre':
            node=self.nodes[index]
            if node['actor']<0:return [(0 if b.price>b.street[b.actor] else 1,1.,cursor)]
            if b.round!=0 or node['actor']!=b.actor:raise AssertionError('public cursor/actor mismatch')
            h=hand(own);weights=[self.pi[(index*3+a)*169+h] for a in range(len(node['actions']))]
            actions=[0 if a=='fold' else 1 if a in ('call','check') else int(a.split('_')[-1])+2 for a in node['actions']]
            children=[('pre',c,0) for c in node['children']]
        else:
            nodes,offset=self.trees[index];node=nodes[local]
            if node['actor']<0:return [(0 if b.price>b.street[b.actor] else 1,1.,cursor)]
            if b.round!=1 or node['seat']!=b.actor:raise AssertionError('flop cursor/actor mismatch')
            h=fullsupport.groups({'pairs':[own],'flop':board[:3]})[0];table=self.teacher[str(index)+'|'+category(board[:3])]
            weights=table[offset[local]+h*len(node['actions']):offset[local]+(h+1)*len(node['actions'])]
            actions=[]
            for a in node['actions']:
                if a['kind']=='fold':actions.append(0)
                elif a['kind'] in ('check','call'):actions.append(1)
                else:
                    ceiling=b.street[b.actor]+b.remaining[b.actor];target=min(ceiling,max(b.price+b.last_full,math.ceil(2*a['amount']-1e-12)))
                    actions.append(3 if target==1 else target+2)
            children=[('flop',index,c) for c in node['children']]
        merged={}
        for action,weight,child in zip(actions,weights,children):
            if action not in legal(b):raise AssertionError(('source action cannot be totalized',action,legal(b)))
            if action in merged:merged[action][0]+=weight # first public alias wins; never retain hidden sampled arm
            else:merged[action]=[weight,child]
        if not math.isclose(sum(x[0] for x in merged.values()),1,abs_tol=1e-10):raise AssertionError('not normalized')
        return [(a,w,c) for a,(w,c) in merged.items()]
    def advance(self,child,b):
        if child is None:return None
        phase,index,local=child
        if phase=='pre' and self.nodes[index]['actor']<0 and self.nodes[index]['matched'] and index in self.trees and b.round==1:return ('flop',index,0)
        return child
    def shadow(self,cursor,win):
        if cursor is None:return None
        phase,index,local=cursor;node=self.nodes[index] if phase=='pre' else self.trees[index][0][local]
        if node['actor']>=0:return None
        if phase=='flop':
            hero_win=win if self.hero_actor[index]==0 else 1-win
            value=node['c0']+node['c1']*hero_win
            return value if self.hero_actor[index]==0 else -value
        return node['value']/2*(2*win-1) if node['matched'] else node['value']/2
