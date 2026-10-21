"""Fixed offline catalog-review acceptance; fixtures are not production parity."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from poll_catalog_review import review_catalog


FIELDS = {
    'posts': {'id':'uuid','user_id':'uuid','content':'text','post_type':'text','result_type':'text','result_id':'uuid'},
    'profiles': {'id':'uuid','display_name':'text','poker_id':'text','avatar_url':'text'},
    'user_blocks': {'blocker_id':'uuid','blocked_id':'uuid'},
    'notifications': {'id':'uuid','user_id':'uuid','actor_id':'uuid','type':'text','post_id':'uuid','read_at':'timestamp with time zone'},
    'post_interactive': {'post_id':'uuid','kind':'text','options':'jsonb','closes_at':'timestamp with time zone','is_anonymous':'boolean'},
    'post_interactive_responses': {'post_id':'uuid','user_id':'uuid','option_index':'integer','answer':'text'},
}


def fixture():
    columns = []
    for table, fields in FIELDS.items():
        for column, kind in fields.items():
            columns.append({'relname':table,'relrowsecurity':True,'attname':column,'type':kind,
                            'attnotnull':column in ('id','post_id','user_id','kind','options'),
                            'default_expression':'gen_random_uuid()' if table=='posts' and column=='id' else None})
    return {'version':1,'columns':columns,'functions':[
        {'signature':'public.create_interactive_post(text,text,text[],integer)','prosecdef':True,'proacl':None,'definition_hash':'0'*32},
        {'signature':'submit_interactive_response(uuid,integer,text)','prosecdef':True,'proacl':None,'definition_hash':'0'*32},
        {'signature':'get_interactive_results(uuid[])','prosecdef':True,'proacl':None,'definition_hash':'0'*32}],
        'policies':[],'grants':[],'cron_jobs':[]}


class CatalogReviewAcceptance(unittest.TestCase):
    def test_complete_synthetic_structure_is_never_production_pass(self):
        report = review_catalog(fixture())
        self.assertEqual(report['status'], 'REVIEW_REQUIRED')
        self.assertTrue(report['structural_checks_passed'])
        self.assertFalse(report['production_approved'])
        self.assertFalse(report['db_connected'])
        self.assertIn('POLICY_GRANT_CRON_REVIEW_REQUIRED', report['issues'])

    def test_missing_table_is_blocked(self):
        value = fixture(); value['columns'] = [r for r in value['columns'] if r['relname']!='notifications']
        report=review_catalog(value)
        self.assertEqual(report['status'],'BLOCKED'); self.assertIn('MISSING_REQUIRED_TABLE',report['issues'])

    def test_missing_or_incompatible_column_is_blocked(self):
        for kind in ('missing','wrong_type'):
            with self.subTest(kind=kind):
                value=fixture()
                if kind=='missing': value['columns']=[r for r in value['columns'] if (r['relname'],r['attname'])!=('posts','content')]
                else: next(r for r in value['columns'] if (r['relname'],r['attname'])==('posts','content'))['type']='bytea'
                report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED')
                self.assertIn('MISSING_REQUIRED_COLUMN' if kind=='missing' else 'INCOMPATIBLE_COLUMN_TYPE',report['issues'])

    def test_disabled_notification_rls_is_blocked(self):
        value=fixture()
        for row in value['columns']:
            if row['relname']=='notifications': row['relrowsecurity']=False
        report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED');self.assertIn('NOTIFICATION_RLS_DISABLED',report['issues'])

    def test_unknown_rpc_signature_is_blocked(self):
        for sig in ('create_interactive_post_v9(uuid)','submit_interactive_response(uuid,text)','get_interactive_results_v2(uuid[])'):
            with self.subTest(sig=sig):
                value=fixture();value['functions'].append({'signature':sig,'prosecdef':True,'proacl':None,'definition_hash':'f'*32})
                report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED');self.assertIn('UNKNOWN_RPC_SIGNATURE',report['issues'])

    def test_unwritten_required_column_without_default_is_blocked(self):
        for table in ('posts','notifications','post_interactive','post_interactive_responses'):
            with self.subTest(table=table):
                value=fixture();value['columns'].append({'relname':table,'relrowsecurity':True,'attname':'owner_review_field','type':'text','attnotnull':True,'default_expression':None})
                report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED');self.assertIn('UNSUPPORTED_REQUIRED_COLUMN',report['issues'])

    def test_optional_or_defaulted_extra_columns_do_not_fake_full_approval(self):
        for nullable,default in ((False,"'synthetic'::text"),(True,None)):
            value=fixture();value['columns'].append({'relname':'posts','relrowsecurity':True,'attname':'future_field','type':'text','attnotnull':not nullable,'default_expression':default})
            report=review_catalog(value);self.assertEqual(report['status'],'REVIEW_REQUIRED');self.assertFalse(report['production_approved'])

    def test_privacy_inventory_missing_is_not_inferred(self):
        value=fixture();value['columns']=[r for r in value['columns'] if r['attname']!='is_anonymous']
        report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED');self.assertIn('PRIVACY_COLUMN_REVIEW_REQUIRED',report['issues'])

    def test_malformed_partial_and_duplicate_inventory_fail_closed_without_echo(self):
        values=[None,[],{}, {'version':1,'columns':[]}, fixture()]
        values[-1]['columns'].append(copy.deepcopy(values[-1]['columns'][0]))
        for value in values:
            with self.subTest(value_type=type(value).__name__):
                report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED');self.assertFalse(report['production_approved'])
        value=fixture();value['functions'].append({'signature':'SENSITIVE_SYNTHETIC_MARKER; DROP TABLE x','prosecdef':True})
        report=review_catalog(value);self.assertEqual(report['status'],'BLOCKED')
        self.assertNotIn('SENSITIVE_SYNTHETIC_MARKER',json.dumps(report))

    def test_input_is_not_mutated_and_richer_security_inventory_still_needs_review(self):
        value=fixture();value['policies']=[{'qual':'SYNTHETIC_PRIVATE_MARKER'}];value['grants']=[{'grantee':'authenticated','privilege_type':'INSERT'}];value['cron_jobs']=[{'command':'SYNTHETIC_PRIVATE_MARKER'}]
        before=copy.deepcopy(value);report=review_catalog(value)
        self.assertEqual(value,before);self.assertEqual(report['status'],'REVIEW_REQUIRED')
        self.assertNotIn('SYNTHETIC_PRIVATE_MARKER',json.dumps(report))


if __name__=='__main__': unittest.main()
