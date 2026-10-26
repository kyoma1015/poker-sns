"""Bounded read-only exact action-report consumer. No model/DB/network operation.

CLI reads JSON from stdin and emits a sanitized view or static HTML. Identity pins
must come from a separately checked producer record; matching self-asserted hashes
are not a signature or proof of optimality. Frequencies and generic EV stay null.
"""
from fractions import Fraction
from itertools import combinations
import html
import json
import re
import sys
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name

DIGEST=re.compile(r'[0-9a-f]{64}\Z')
INTEGER=re.compile(r'(?:0|-?[1-9][0-9]{0,127})\Z')
ROOT={'schema','actions','hands','concrete_combinations','combo_provenance','observation_digest',
      'config_digest','policy_digest','weight_provenance','support_complete','native_infoset_ev',
      'hand169_ev','scope','strategy_convergence'}
HAND={'observed_combinations','eligible_combinations','coverage_complete','explicit_hero_mass',
      'observed_action_values','complete_class_action_values','ev'}
COMBO={'cards','hero_information_digest','support_digest','support_size','support_complete',
       'explicit_hero_mass','observation_evidence_mass','hero_counterfactual_mass'}


def _fail():raise ValueError('INVALID_ACTION_REPORT')
def _integer(x,low,high):
    if type(x) is not int or not low<=x<=high:_fail()
    return x

def _digest(x):
    if not isinstance(x,str) or not DIGEST.fullmatch(x):_fail()
    return x

def _fraction(x,*,nonnegative=False):
    if not isinstance(x,dict) or set(x)!={'rational'}:_fail()
    r=x['rational']
    if not isinstance(r,dict) or set(r)!={'numerator','denominator'}:_fail()
    n=r['numerator'];d=r['denominator']
    if (not isinstance(n,str) or not isinstance(d,str) or not INTEGER.fullmatch(n)
            or not INTEGER.fullmatch(d) or d.startswith('-') or d=='0'):_fail()
    value=Fraction(int(n),int(d))
    if nonnegative and value<0:_fail()
    return value

def _values(x,count):
    if x is None:return None
    if not isinstance(x,list) or len(x)!=count:_fail()
    return [_fraction(v) for v in x]

def _cards(x,count=None):
    if (not isinstance(x,list) or count is not None and len(x)!=count
            or len(x)>5 or any(type(c) is not int or not 0<=c<52 for c in x) or len(set(x))!=len(x)):_fail()
    return x

def _load(raw):
    if not isinstance(raw,(str,bytes)):_fail()
    if len(raw)>1048576:_fail()
    try:
        if isinstance(raw,bytes):raw=raw.decode('utf-8','strict')
        if len(raw.encode('utf-8'))>1048576:_fail()
        def pairs(items):
            out={}
            for k,v in items:
                if k in out:_fail()
                out[k]=v
            return out
        def number(text):
            if len(text)>8:_fail()
            return int(text)
        data=json.loads(raw,object_pairs_hook=pairs,parse_int=number,
                        parse_float=lambda _: _fail(),parse_constant=lambda _: _fail())
        pending=[(data,0)];count=0
        while pending:
            value,depth=pending.pop();count+=1
            if count>100000 or depth>24:_fail()
            if isinstance(value,dict):pending.extend((v,depth+1) for v in value.values())
            elif isinstance(value,list):pending.extend((v,depth+1) for v in value)
            elif isinstance(value,str) and len(value)>4096:_fail()
        return data
    except (UnicodeError,RecursionError,json.JSONDecodeError,OverflowError):_fail()


def consume_report(raw,*,expected):
    """Check pinned identities and recompute coverage/mass/means where supplied.

    Legacy v1 without board/per-combo values is viewable only as unverified
    structure; all action values are withheld. Never derive action frequencies.
    """
    r=_load(raw)
    if not isinstance(r,dict) or set(r) not in (ROOT,ROOT|{'public_cards'}):_fail()
    if r['schema']!='pokerid-explicit-belief-action169-v1':_fail()
    pins=('observation_digest','config_digest','policy_digest')
    if not isinstance(expected,dict) or set(expected)!=set(pins):_fail()
    for key in pins:
        if _digest(r[key])!=_digest(expected[key]):_fail()
    actions=r['actions']
    if (not isinstance(actions,list) or not 1<=len(actions)<=64
            or any(type(a) is not int or not 0<=a<=2**31-1 for a in actions) or len(set(actions))!=len(actions)):_fail()
    if (r['support_complete'] is not False or r['native_infoset_ev'] is not None
            or r['hand169_ev'] is not None or r['strategy_convergence']!='UNKNOWN'
            or r['weight_provenance']!='explicit caller-supplied exact hero reach; not inferred from visits'
            or r['scope']!='finite explicit-belief action values, not full-strategy or equilibrium EV'):_fail()
    hands=r['hands'];combos=r['combo_provenance'];total=_integer(r['concrete_combinations'],1,1326)
    if not isinstance(hands,dict) or set(hands)!=set(CLASSES) or not isinstance(combos,list) or len(combos)!=total:_fail()
    enhanced='public_cards' in r and all(isinstance(c,dict) and 'action_values' in c for c in combos)
    board=_cards(r['public_cards']) if 'public_cards' in r else []
    if 'public_cards' in r and len(board) not in (0,3,4,5):_fail()
    eligible={label:0 for label in CLASSES};rows={label:[] for label in CLASSES};seen=set()
    if enhanced:
        for pair in combinations([c for c in range(52) if c not in board],2):
            eligible[hand_class([card_name(c) for c in pair])]+=1
    for c in combos:
        if not isinstance(c,dict) or set(c) not in (COMBO,COMBO|{'action_values'}):_fail()
        cards=_cards(c['cards'],2);identity=tuple(sorted(cards))
        if identity in seen or set(cards)&set(board):_fail()
        seen.add(identity);_digest(c['support_digest'])
        if c['hero_information_digest'] is not None:_digest(c['hero_information_digest'])
        _integer(c['support_size'],1,10000)
        if c['support_complete'] is not False:_fail()
        mass=_fraction(c['explicit_hero_mass'],nonnegative=True)
        evidence=_fraction(c['observation_evidence_mass'],nonnegative=True)
        cf=_fraction(c['hero_counterfactual_mass'],nonnegative=True)
        if evidence>cf or cf>1:_fail()
        values=_values(c['action_values'],len(actions)) if 'action_values' in c else None
        if values is not None and (not evidence or c['hero_information_digest'] is None):_fail()
        rows[hand_class([card_name(x) for x in cards])].append((mass,values))
    output=[];partial=False
    for label in CLASSES:
        h=hands[label]
        if not isinstance(h,dict) or set(h)!=HAND or h['ev'] is not None:_fail()
        observed=_integer(h['observed_combinations'],0,16);available=_integer(h['eligible_combinations'],0,16)
        if observed!=len(rows[label]) or observed>available or type(h['coverage_complete']) is not bool:_fail()
        if h['coverage_complete']!=(observed==available):_fail()
        if enhanced and available!=eligible[label]:_fail()
        mass=_fraction(h['explicit_hero_mass'],nonnegative=True)
        if mass!=sum((m for m,_ in rows[label]),Fraction()):_fail()
        values=_values(h['observed_action_values'],len(actions));complete=_values(h['complete_class_action_values'],len(actions))
        if enhanced:
            known=mass>0 and all(v is not None for m,v in rows[label] if m)
            calculated=([sum((m*v[a] for m,v in rows[label] if m),Fraction())/mass for a in range(len(actions))] if known else None)
            if values!=calculated or complete!=(calculated if observed==available else None):_fail()
        if not enhanced:values=complete=None
        partial|=observed!=available
        output.append({'hand':label,'observed_combinations':observed,'eligible_combinations':available,
            'coverage_complete':observed==available,'observed_action_values':[str(v) for v in values] if values is not None else None,
            'complete_class_action_values':[str(v) for v in complete] if complete is not None else None,
            'frequencies':None,'ev':None})
    warnings=['EXPLICIT_BELIEF_NOT_EQUILIBRIUM','FREQUENCIES_NOT_PROVIDED','NATIVE_AND_169_EV_UNKNOWN']
    if partial:warnings.append('PARTIAL_COVERAGE')
    if not enhanced:warnings.append('LEGACY_PROVENANCE_NOT_RECOMPUTABLE')
    return {'schema':'pokerid-action-report-view-v1','validation':'recomputed_arithmetic_and_pinned_identity' if enhanced else 'structure_and_pinned_identity_only',
            'actions':actions,'hands':output,'warnings':warnings,'native_infoset_ev':None,'hand169_ev':None,
            **{key:r[key] for key in pins}}


def render_html(view):
    """Static offline document: no scripts, external links or network requests."""
    esc=lambda value:html.escape(str(value),quote=True)
    def values(v):return '未計算' if v is None else ' / '.join(esc(x) for x in v)
    body=''.join('<tr><th>'+esc(row['hand'])+'</th><td>'+esc(str(row['observed_combinations'])+'/'+str(row['eligible_combinations']))+'</td><td>'+values(row['observed_action_values'])+'</td><td>'+values(row['complete_class_action_values'])+'</td></tr>' for row in view['hands'])
    return '<!doctype html><html lang="ja"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; base-uri \'none\'; form-action \'none\'"><title>有限beliefアクション値</title><h1>有限beliefアクション値</h1><p>部分coverageを含みます。実ポーカー均衡・収束・完全EVの証明ではありません。</p><p>アクション頻度：未提供。native EV／169 EV：未計算。</p><p>'+esc(', '.join(view['warnings']))+'</p><p>action順序：'+esc(view['actions'])+'</p><p>policy：'+esc(view['policy_digest'])+'</p><table><thead><tr><th>手札</th><th>観測／対象</th><th>観測部分の条件付き値</th><th>全対象コンボの条件付き値</th></tr></thead><tbody>'+body+'</tbody></table></html>'


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('observation','config','policy'):parser.add_argument('--expected-'+name,required=True)
    parser.add_argument('--format',choices=['json','html'],default='json');args=parser.parse_args()
    try:
        raw=sys.stdin.buffer.read(1048577)
        view=consume_report(raw,expected={name+'_digest':getattr(args,'expected_'+name) for name in ('observation','config','policy')})
        print(render_html(view) if args.format=='html' else json.dumps(view,ensure_ascii=False,sort_keys=True))
    except ValueError:
        print('INVALID_ACTION_REPORT',file=sys.stderr);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
