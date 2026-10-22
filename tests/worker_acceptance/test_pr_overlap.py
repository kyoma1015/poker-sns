"""Fixed overlap certificates; owned repositories, never model-execution proof."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from pr_overlap import verify_overlap_review


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'user.name=Overlap fixture', '-c', 'user.email=fixture@users.noreply.github.com', *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()


class OverlapProof(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, 'init', '-b', 'main')
        (self.repo/'src').mkdir()
        self.path = 'src/value.py'
        self.original = ''.join(f'# line {n}\n' for n in range(1,21))
        (self.repo/self.path).write_text(self.original)
        git(self.repo,'add','.'); git(self.repo,'commit','-m','base')
        self.base = git(self.repo,'rev-parse','HEAD')
        git(self.repo,'checkout','-b','pr')
        self.prtext = self.original.replace('# line 2\n','# changed two\n')
        (self.repo/self.path).write_text(self.prtext)
        git(self.repo,'add','.');git(self.repo,'commit','-m','PR change')
        self.head = git(self.repo,'rev-parse','HEAD')
        git(self.repo,'checkout','-b','candidate',self.base)
        (self.repo/self.path).write_text(self.prtext)
        (self.repo/'marker').write_text('candidate is separate history')
        git(self.repo,'add','.');git(self.repo,'commit','-m','independent inherited source')
        self.target = git(self.repo,'rev-parse','HEAD')
        self.pr = {'number':77,'head':'codex/legacy','head_sha':self.head,'base_sha':self.base,'changed_paths':[self.path]}
        self.candidate = {'task':{'base_sha':self.target,'allowed_paths':[self.path]},'overlap_reviews':{}}

    def tearDown(self): self.tmp.cleanup()

    def certificate(self, mode='equivalent_blob'):
        patch=subprocess.check_output(['git','diff','--full-index','--no-ext-diff','--no-textconv','--no-renames','--binary','--src-prefix=a/','--dst-prefix=b/',self.base,self.head,'--',self.path],cwd=self.repo)
        self.candidate['overlap_reviews']['77']={'reviewed':True,'reason':'Exact prior change is already in the pinned input; distinct acceptance fails.',
          'candidate_base_sha':self.target,'pr_base_sha':self.base,'head_sha':self.head,
          'files':{self.path:{'mode':mode,'candidate_blob':git(self.repo,'rev-parse',self.target+':'+self.path),
                           'head_blob':git(self.repo,'rev-parse',self.head+':'+self.path),
                           'patch_sha256':hashlib.sha256(patch).hexdigest()}}}
        return self.candidate['overlap_reviews']['77']

    def test_independent_history_identical_source_is_proved(self):
        self.assertNotEqual(self.target,self.head)
        self.certificate()
        self.assertTrue(verify_overlap_review(self.candidate,self.pr,self.repo))

    def test_exact_patch_already_included_with_unrelated_newer_changes(self):
        (self.repo/self.path).write_text(self.prtext.replace('# line 19\n','# unrelated nineteen\n'))
        git(self.repo,'add','.');git(self.repo,'commit','-m','unrelated new source')
        self.target=git(self.repo,'rev-parse','HEAD');self.candidate['task']['base_sha']=self.target
        self.certificate('included_patch')
        self.assertTrue(verify_overlap_review(self.candidate,self.pr,self.repo))

    def test_exact_prior_source_blob_in_verified_ancestor(self):
        witness=self.target
        (self.repo/self.path).write_text(self.prtext.replace('# line 19\n','# later correction\n'))
        git(self.repo,'add','.');git(self.repo,'commit','-m','later corrected source')
        self.target=git(self.repo,'rev-parse','HEAD');self.candidate['task']['base_sha']=self.target
        review=self.certificate('ancestor_blob');review['files'][self.path]['witness_commit']=witness
        self.assertTrue(verify_overlap_review(self.candidate,self.pr,self.repo))
        review['files'][self.path]['witness_commit']=self.head
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_ancestor_with_different_blob_is_not_a_witness(self):
        review=self.certificate('ancestor_blob');review['files'][self.path]['witness_commit']=self.base
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_pending_change_not_in_candidate_is_not_exempted(self):
        self.target=self.base;self.candidate['task']['base_sha']=self.base
        self.certificate('included_patch')
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_changed_head_base_or_candidate_pins_are_rejected(self):
        for field in ('head_sha','base_sha'):
            with self.subTest(field=field):
                self.certificate();p=dict(self.pr);p[field]='0'*40
                with self.assertRaises(ValueError):verify_overlap_review(self.candidate,p,self.repo)
        self.certificate();self.candidate['overlap_reviews']['77']['candidate_base_sha']='0'*40
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_wrong_blob_patch_digest_and_review_flag_rejected(self):
        for key,value in [('candidate_blob','0'*40),('head_blob','0'*40),('patch_sha256','0'*64)]:
            with self.subTest(key=key):
                review=self.certificate('included_patch');review['files'][self.path][key]=value
                with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)
        self.certificate()['reviewed']=False
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_noop_patch_not_accepted_as_coverage(self):
        self.head=self.base;self.pr['head_sha']=self.base
        self.certificate('included_patch')
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_missing_extra_path_and_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)
        self.certificate()['files']['src/other.py']={}
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)
        self.certificate('ignore')
        with self.assertRaises(ValueError):verify_overlap_review(self.candidate,self.pr,self.repo)

    def test_proof_does_not_modify_repository_index_or_working_tree(self):
        self.certificate('included_patch')
        before=(git(self.repo,'status','--porcelain'),git(self.repo,'write-tree'))
        verify_overlap_review(self.candidate,self.pr,self.repo)
        self.assertEqual(before,(git(self.repo,'status','--porcelain'),git(self.repo,'write-tree')))


class PlannerIntegration(unittest.TestCase):
    def test_planner_accepts_verified_equivalence_but_still_requires_failed_baseline(self):
        from test_continuation_recovery import RecoveryAcceptance
        import continuation_recovery as recovery
        h=RecoveryAcceptance();h.setUp()
        try:
            base=h.sha
            git(h.repo,'checkout','-b','legacy')
            (h.repo/'src/value.py').write_text('VALUE=1\n# prior feature\n')
            git(h.repo,'add','.');git(h.repo,'commit','-m','legacy feature')
            head=git(h.repo,'rev-parse','HEAD')
            git(h.repo,'checkout','-b','candidate',base)
            (h.repo/'src/value.py').write_text('VALUE=1\n# prior feature\n')
            (h.repo/'marker').write_text('separate history')
            git(h.repo,'add','.');git(h.repo,'commit','-m','candidate inherited feature')
            h.sha=git(h.repo,'rev-parse','HEAD')
            c=h.candidate()
            c['overlap_reviews']={'77':{'reviewed':True,'reason':'Whole file inherited identically; VALUE2 acceptance still fails.',
                'candidate_base_sha':h.sha,'pr_base_sha':base,'head_sha':head,'files':{'src/value.py':{
                'mode':'equivalent_blob','candidate_blob':git(h.repo,'rev-parse',h.sha+':src/value.py'),
                'head_blob':git(h.repo,'rev-parse',head+':src/value.py')}}}}
            obs=h.observe([{'number':77,'head':'codex/legacy','head_sha':head,'base_sha':base,'changed_paths':['src/value.py']}])
            plan=h.store.plan([c],obs,h.repo,now=100)
            self.assertEqual(len(plan['manifest']['tasks']),1)
            bad=h.candidate('bad');bad['baseline']['failed']=False;bad['overlap_reviews']=c['overlap_reviews']
            self.assertEqual(h.store.plan([bad],obs,h.repo,now=100)['manifest']['tasks'],[])
        finally:h.tearDown()


if __name__=='__main__':unittest.main()
