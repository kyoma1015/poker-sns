"""Recompute a specific complete-game certificate and emit its UI data.

No user-uploaded certificate is trusted. Source hashes, exact model, fixed seeds,
all raw counts and every derived value are checked. UI data must match this
reproducible generator; the statistical assumptions remain explicitly visible.
"""
from fractions import Fraction
import argparse
import hashlib
import json
from pathlib import Path
from gto.hand169 import CLASSES
from gto.native.onebb_certificate import evaluate_counts

ROOT=Path(__file__).resolve().parents[2]
ID='explicit-hu-onebb-forced-blind-v1'
CERTIFICATE_ID='whole-game-onebb-action-bound-v1'


def release(evidence_path):
    path=Path(evidence_path)
    if path.stat().st_size>1024*1024:raise ValueError('evidence exceeds1MiB')
    raw=path.read_text().rstrip('\n');data=json.loads(raw)
    if data.get('schema')!='pokerid-onebb-complete-game-evidence-v1' or data.get('formal_profile') is not False:
        raise ValueError('explicit calibration evidence required')
    expected_config={'schema':1,'stacks':[2,2],'fixture':None,'rules':{
        'version':'pokerid-nlhe-reference-1','bb':2,'bba':0,'ante_order':'ante_first',
        'stack_basis':'before_ante','dead_eligibility':'all_live','rake_rate':'0','rake_cap':None,
        'no_flop_no_drop':True,'cap_scope':'whole_hand','rounding':'floor','rake_ante':True,'collection':'terminal'}}
    if data.get('config')!=expected_config:raise ValueError('complete native oneBB model differs')
    expected_sources={
        'source_sha256':hashlib.sha256(Path(__file__).with_name('onebb_sampler.cc').read_bytes()).hexdigest(),
        'native_state_sha256':hashlib.sha256((ROOT/'handoff/gto/g12_next/g11_native_state.h').read_bytes()).hexdigest(),
        'rules_sha256':'870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'}
    if data.get('sources')!=expected_sources:raise ValueError('certificate native source identity differs')
    runs=data.get('runs')
    if not isinstance(runs,list) or len(runs)!=2 or [r.get('seed') for r in runs]!=[17,29]:
        raise ValueError('both prespecified independent-seed runs required')
    derived=[]
    for run in runs:
        for index,label in enumerate(CLASSES):
            row=run.get('counts',{}).get(label,{})
            if row.get('seed')!=run['seed']*1000+index or row.get('samples')!=10000:
                raise ValueError('sample/seed plan changed')
        proof=evaluate_counts(run['counts'])
        if proof!=run.get('evidence') or not proof['all_classes_call_dominant'] or proof['max_unilateral_gain_upper_bb']!=0:
            raise ValueError('full-game action dominance not reproduced')
        derived.append(proof)
    confidence=float(1-2*Fraction(1,10**9))
    if data.get('joint_confidence')!=confidence:raise ValueError('confidence accounting differs')
    query={'format':'mtt','players':2,'seat':0,'stackBb':'1','anteBb':'0','rakePct':'0',
        'rakeCapBb':None,'openBb':None,'threeBetBb':None,'fourBetBb':None,'stage':'forced_blind_allin'}
    policy={'config':expected_config,'nativeActions':[0,1],'all2652OrderedHeroHands':[0,1],
            'construction':'complete-game simultaneous action-dominance policy improvement'}
    config_digest=hashlib.sha256(json.dumps(expected_config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    policy_digest=hashlib.sha256(json.dumps(policy,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    hands={label:{'combinations':row['combinations'],'frequencies':row['frequencies'],
        'evBb':row['evBb'],'evIntervalBb':row['evIntervalBb']} for label,row in derived[0]['hands'].items()}
    record={'schema':'pokerid-verified-preflop-v1','id':ID,'query':query,
        'conditionClass':'explicit_test','conditionName':'検証用：HU・両者1BB・BB強制オールイン',
        'policyDigest':policy_digest,'configDigest':config_digest,'certificateId':CERTIFICATE_ID,
        'actions':['フォールド','コール（1BBオールイン）'],'hands':hands,
        'coverage':{'combinations':1326,'hands':169},'equilibriumVerified':True}
    certificate={'datasetId':ID,'queryKey':json.dumps(query,separators=(',',':')),
        'policyDigest':policy_digest,'configDigest':config_digest,
        'artifactSha256':hashlib.sha256(raw.encode()).hexdigest(),'scope':'complete_target_game',
        'continuation':'full_native_game','metric':'max_unilateral_deviation_gain',
        'upperBoundBb':0,'acceptedToleranceBb':0,'confidence':confidence,
        'verificationMethod':'simultaneous_full_game_action_bounds',
        'directHeroRepresentatives':169,'symmetryExpandedCombinations':1326,'strategicInformationSets':2652,
        'evSamplesPerClass':10000,
        'samplingAssumptions':'独立一様なカードサンプリングを仮定した統計的検証。厳密な全配布列挙ではありません。',
        'reviewReference':'docs/workers/GTO_ONEBB_FULL_GAME_PROOF_20261027.md と docs/qa/full-game-calibration-20261027/onebb-evidence.json を再計算して照合。',
        'policyConstruction':'全情報集合の行動価値比較による方策改善。CFR学習平均そのものではありません。'}
    return record,certificate


def render(evidence_path):
    record,certificate=release(evidence_path)
    return ("// Generated from full native-game evidence; do not edit by hand.\n"
        "// Explicit oneBB calibration only, not formal RFI/open/3bet range data.\n"
        "import type { ReviewedCertificate } from './rangeCatalog'\n\n"
        'export const oneBBRange = '+json.dumps(record,ensure_ascii=False,indent=2)+'\n\n'
        'export const oneBBCertificate: ReviewedCertificate = '+json.dumps(certificate,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path);group.add_argument('--check',type=Path)
    args=parser.parse_args();text=render(args.evidence)
    if args.check:
        if args.check.read_text()!=text:raise ValueError('UI data differs from recomputed full-game certificate')
        print('PASS full-game evidence/raw counts/source identity/UI data recomputation')
    else:
        with args.output.open('x') as out:out.write(text)
