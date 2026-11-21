"""Actual-chance stratified intervals for a fixed RESTRICTED game.

Computed physical-board probability is separate from statistical population
coverage. Local BR intervals are valid regardless of local CFR convergence.
Confidence assumes the preregistered within-stratum IID PRNG draws; no external
GTO or real-poker approximation guarantee follows.
"""
import hashlib,json,math,os
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def cache_load(path,identity):
 if not path.exists():return None
 data=json.loads(path.read_text())
 if data.get('status')!='complete' or data.get('identity')!=identity or data.get('checksum')!=digest(data.get('row')):raise ValueError('population cache identity/checksum mismatch; keep file for inspection')
 return data['row']


def cache_write(path,identity,row):
 path.parent.mkdir(parents=True,exist_ok=True);data={'status':'complete','identity':identity,'row':row,'checksum':digest(row)};temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n');os.replace(temp,path)


def sample_row(metrics,pot,guard=1e-7):
 profile=metrics['profile_hero_ev_bb'];lo=max(-pot/2,metrics['villain_br_hero_ev_bb']-guard);hi=min(pot/2,metrics['hero_br_ev_bb']+guard)
 if not math.isfinite(profile+lo+hi) or not -50-guard<=profile<=50+guard or lo>hi+guard:raise ValueError('invalid local BR/value bracket')
 if lo>hi:lo=hi=(lo+hi)/2
 return {'profile_hero_ev_bb':profile,'game_value_lower_bb':lo,'game_value_upper_bb':hi,'local_nashconv_bb':metrics['restricted_nashconv_bb'],'target_game':'one-street public-history game; not fullNLHE'}


def interval(strata,weights,pot,tail_probability,previous=None):
 if set(strata)!=set(weights) or any(not rows for rows in strata.values()) or not math.isclose(math.fsum(weights.values()),1,abs_tol=1e-12):raise ValueError('every positive stratum and normalized fixed weights required')
 if not 0<tail_probability<1:raise ValueError('preallocated confidence tail required')
 variance_factor=math.fsum(weights[k]**2/len(rows) for k,rows in strata.items());scale=math.sqrt(math.log(1/tail_probability)*variance_factor/2);profile_mean=0.;lower_mean=0.;upper_mean=0.;unique={};counts={}
 for key,rows in strata.items():
  w=weights[key];counts[key]=len(rows);profile_mean+=w*math.fsum(r['profile_hero_ev_bb'] for r in rows)/len(rows);lower_mean+=w*math.fsum(r['game_value_lower_bb'] for r in rows)/len(rows);upper_mean+=w*math.fsum(r['game_value_upper_bb'] for r in rows)/len(rows)
  for r in rows:
   board=tuple(r['flop'])
   if board in unique and unique[board]!=r:raise ValueError('same board must use same fixed deterministic evaluator')
   unique[board]=r
 mass=math.fsum(r['board_probability'] for r in unique.values())
 if not 0<=mass<=1+1e-12:raise ValueError('invalid physical probability coverage')
 mass=min(1.,mass);missing=1-mass;known_lo=math.fsum(r['board_probability']*r['game_value_lower_bb'] for r in unique.values());known_hi=math.fsum(r['board_probability']*r['game_value_upper_bb'] for r in unique.values());known_profile=math.fsum(r['board_probability']*r['profile_hero_ev_bb'] for r in unique.values());deterministic=[known_lo-missing*pot/2,known_hi+missing*pot/2];profile_det=[known_profile-missing*50,known_profile+missing*50];stat=[lower_mean-pot*scale-1e-7,upper_mean+pot*scale+1e-7];profile_stat=[profile_mean-100*scale-1e-7,profile_mean+100*scale+1e-7];game_bound=[max(-pot/2,deterministic[0],stat[0]),min(pot/2,deterministic[1],stat[1])];profile_bound=[max(-50.,profile_det[0],profile_stat[0]),min(50.,profile_det[1],profile_stat[1])]
 if previous:
  game_bound=[max(game_bound[0],previous['restricted_game_value_interval_bb'][0]),min(game_bound[1],previous['restricted_game_value_interval_bb'][1])];profile_bound=[max(profile_bound[0],previous['uniform512_profile_ev_interval_bb'][0]),min(profile_bound[1],previous['uniform512_profile_ev_interval_bb'][1])]
 empty=game_bound[0]>game_bound[1] or profile_bound[0]>profile_bound[1]
 return {'draw_count':sum(counts.values()),'draws_by_stratum':counts,'unique_physical_boards':len(unique),'evaluated_board_probability':mass,'unevaluated_board_probability':missing,'profile_ev_estimate_bb':profile_mean,'sampled_game_lower_estimate_bb':lower_mean,'sampled_game_upper_estimate_bb':upper_mean,'sampled_mean_local_br_width_bb':upper_mean-lower_mean,'weighted_hoeffding_variance_factor':variance_factor,'game_value_sampling_radius_bb':pot*scale,'profile_sampling_radius_bb':100*scale,'restricted_game_value_interval_bb':game_bound,'uniform512_profile_ev_interval_bb':profile_bound,'deterministic_restricted_game_value_interval_bb':deterministic,'uncomputed_game_value_contribution_bounds_bb':[-missing*pot/2,missing*pot/2],'uncomputed_profile_ev_contribution_bounds_bb':[-missing*50,missing*50],'statistical_game_value_interval_bb':stat,'statistical_profile_interval_bb':profile_stat,'empty_intersection_failure':empty,'exact_ev_integration_complete':mass>=1-1e-12,'statistical_target':'all22100physicalboards under frozen history, restrictedgame value and fixed uniform512profile;NOTrealNLHE','model_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED'}
