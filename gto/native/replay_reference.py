"""Exact cross-build replay gate for research evidence, never a GTO certificate."""
_FIELDS=('parent_sha256','checkpoint_sha256','additional_iterations','before','progress',
         'infoset_diagnosis','strict_evaluation','full_game_convergence_verified',
         'ordinary_verified_gto_ranges','formal_acceptance_complete')

def projection(report):
    selected={key:report[key] for key in _FIELDS}
    selected['contexts']=[{'stage':c['stage'],'updated_orderings':c['updated_orderings'],
        'complete_frequency_classes':c.get('history_reach',{}).get('complete_frequency_classes',c['complete_frequency_classes'])}
        for c in report['contexts']]
    return selected

def verify(report,reference):
    actual=projection(report)
    if (reference['full_game_convergence_verified'] is not False
            or reference['ordinary_verified_gto_ranges']!=0 or reference['formal_acceptance_complete']!=0):
        raise ValueError('research replay cannot certify GTO or formal acceptance')
    if actual!=reference:
        differing=sorted(k for k in set(actual)|set(reference) if actual.get(k)!=reference.get(k))
        raise ValueError('independent build replay differs: '+','.join(differing))
    return {'independent_build_replay_verified':True,'new_statistical_sample_sets':0,
            'ordinary_gto_certificate':False}
