"""Offline structural review of an explicitly supplied catalog export.

No database client, SQL execution or production approval is provided here.
Catalog policy/ACL/function bodies, historical privacy and Auth require review.
"""
import argparse
import json
from pathlib import Path
import re


REQUIRED = {
    'posts': {'id':'uuid','user_id':'uuid','content':'text','post_type':'text','result_type':'text','result_id':'uuid'},
    'profiles': {'id':'uuid','display_name':'text','poker_id':'text','avatar_url':'text'},
    'user_blocks': {'blocker_id':'uuid','blocked_id':'uuid'},
    'notifications': {'id':'uuid','user_id':'uuid','actor_id':'uuid','type':'text','post_id':'uuid','read_at':'timestamp with time zone'},
    'post_interactive': {'post_id':'uuid','kind':'text','options':'jsonb','closes_at':'timestamp with time zone','is_anonymous':'boolean'},
    'post_interactive_responses': {'post_id':'uuid','user_id':'uuid','option_index':'integer','answer':'text'},
}
WRITTEN = {
    'posts': {'user_id','content','post_type','result_type','result_id'},
    'notifications': {'id','user_id','actor_id','type','post_id','event_key'},
    'post_interactive': {'post_id','kind','options','closes_at','is_anonymous'},
    'post_interactive_responses': {'post_id','user_id','option_index','answer'},
}
RPC_SIGNATURES = {
    'create_interactive_post(text,text,text[],integer)',
    'create_interactive_post_v2(text,text,text[],integer,boolean)',
    'create_interactive_post_v3(text,text,text[],integer,boolean,text)',
    'create_interactive_post_v4(text,text,text[],integer,boolean,text)',
    'submit_interactive_response(uuid,integer,text)',
    'submit_interactive_response_v2(uuid,integer,text,boolean)',
    'get_interactive_results(uuid[])',
    'get_interactive_results_v4(uuid[])',
}
SECTIONS = ('columns','functions','policies','grants','cron_jobs')
MANUAL_REVIEW = 'POLICY_GRANT_CRON_REVIEW_REQUIRED'


def _report(issues):
    issues = sorted(set(issues))
    blocked = any(issue != MANUAL_REVIEW for issue in issues)
    return {'status':'BLOCKED' if blocked else 'REVIEW_REQUIRED',
            'structural_checks_passed':not blocked,'production_approved':False,
            'db_connected':False,'issues':issues}


def _text(value):
    return isinstance(value,str) and 0 < len(value) <= 200


def review_catalog(inventory):
    """Inspect metadata only; return reason codes without echoing caller data.

    The input is neither modified nor executed. A compatible synthetic catalog
    is still REVIEW_REQUIRED; structural checks cannot establish deployment or
    security approval and no switch can change production_approved to true.
    """
    if (not isinstance(inventory,dict) or type(inventory.get('version')) is not int
            or inventory['version'] != 1
            or set(inventory) != {'version',*SECTIONS}
            or any(not isinstance(inventory.get(section),list)
                   or len(inventory[section]) > 10000 for section in SECTIONS)):
        return _report(['MALFORMED_INVENTORY'])
    if any(not isinstance(row,dict) for section in SECTIONS for row in inventory[section]):
        return _report(['MALFORMED_INVENTORY'])
    issues = [MANUAL_REVIEW]
    tables = {}
    rls = {}
    for row in inventory['columns']:
        fields = ('relname','relrowsecurity','attname','type','attnotnull','default_expression')
        if (not all(key in row for key in fields)
                or not all(_text(row[key]) for key in ('relname','attname','type'))
                or type(row['relrowsecurity']) is not bool or type(row['attnotnull']) is not bool
                or (row['default_expression'] is not None and not isinstance(row['default_expression'],str))):
            issues.append('MALFORMED_COLUMN'); continue
        table,column = row['relname'],row['attname']
        columns = tables.setdefault(table,{})
        if column in columns:
            issues.append('DUPLICATE_COLUMN'); continue
        if table in rls and rls[table] != row['relrowsecurity']:
            issues.append('MALFORMED_COLUMN')
        rls[table] = row['relrowsecurity']; columns[column] = row
        if (table in WRITTEN and column not in WRITTEN[table]
                and row['attnotnull'] and not row['default_expression']):
            issues.append('UNSUPPORTED_REQUIRED_COLUMN')
    for table,columns in REQUIRED.items():
        if table not in tables:
            issues.append('MISSING_REQUIRED_TABLE'); continue
        for column,kind in columns.items():
            if column not in tables[table]:
                issues.append('PRIVACY_COLUMN_REVIEW_REQUIRED' if (table,column)==('post_interactive','is_anonymous') else 'MISSING_REQUIRED_COLUMN')
            elif tables[table][column]['type'] != kind:
                issues.append('INCOMPATIBLE_COLUMN_TYPE')
    if 'notifications' in rls and not rls['notifications']:
        issues.append('NOTIFICATION_RLS_DISABLED')
    seen = set()
    for row in inventory['functions']:
        if (not all(key in row for key in ('signature','prosecdef','proacl','definition_hash'))
                or not _text(row['signature']) or type(row['prosecdef']) is not bool
                or not isinstance(row['definition_hash'],str)
                or re.fullmatch(r'[0-9a-fA-F]{32}',row['definition_hash']) is None
                or row['proacl'] is not None and not isinstance(row['proacl'],(str,list))):
            issues.append('MALFORMED_FUNCTION'); continue
        signature = row['signature'].replace(' ','')
        if signature.startswith('public.'):
            signature = signature[len('public.'):]
        if re.fullmatch(r'[a-z_][a-z0-9_]*\([a-z0-9_,\[\]]*\)',signature) is None:
            issues.append('MALFORMED_FUNCTION'); continue
        if signature in seen:
            issues.append('DUPLICATE_FUNCTION')
        seen.add(signature)
        if signature.startswith(('create_interactive_post','submit_interactive_response','get_interactive_results')) and signature not in RPC_SIGNATURES:
            issues.append('UNKNOWN_RPC_SIGNATURE')
    return _report(issues)


def _unique_object(pairs):
    value = {}
    for key,item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key')
        value[key] = item
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory',type=Path,help='local metadata-only version1 JSON export')
    args = parser.parse_args()
    try:
        with args.inventory.open('rb') as stream:
            raw = stream.read(4*1024*1024+1)
        if len(raw)>4*1024*1024:
            raise ValueError('bounded input required')
        result = review_catalog(json.loads(raw,object_pairs_hook=_unique_object))
    except (OSError,ValueError,TypeError,RecursionError):
        result = _report(['MALFORMED_INVENTORY'])
    print(json.dumps(result,sort_keys=True))
    # Neither code means production permission: 3 needs manual review, 2 blocked.
    return 2 if result['status']=='BLOCKED' else 3


if __name__=='__main__':
    raise SystemExit(main())
