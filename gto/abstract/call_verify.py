"""Strict EV/provenance reproduction; raw deal-mass roundoff has its own units."""
import copy,math
from gto.abstract.verify_export import compare


def verify(actual,expected):
 actual=copy.deepcopy(actual);expected=copy.deepcopy(expected)
 key='maximum_board_chance_mass_error'
 if key in actual or key in expected:
  if key not in actual or key not in expected:raise ValueError('chance audit missing')
  # This is absolute error on a large unnormalized physical-deal sum, NOT BB.
  # Match the computation's existing pre-fit1e-7 guard, not the EV1e-12 tolerance.
  for obj in (actual,expected):
   value=obj.pop(key)
   if not math.isfinite(value) or not 0<=value<=1e-7:raise ValueError('raw chance mass audit exceeds independent direct-sum guard')
 compare(actual,expected)

if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--actual',type=Path,required=True);p.add_argument('--expected',type=Path,required=True);a=p.parse_args();verify(json.loads(a.actual.read_text()),json.loads(a.expected.read_text()));print('PASS call research EV1e-12 and source/protocol identity; raw chance-mass audit within pre-fit1e-7 guard;NOT external GTO')
