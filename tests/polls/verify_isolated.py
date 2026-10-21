"""Real PostgREST + official Supabase Postgres QA; local fixture JWTs only."""
import base64, concurrent.futures, hashlib, hmac, json, os, subprocess, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'http://127.0.0.1:55431'
OWNER = '10000000-0000-0000-0000-000000000001'
VOTER = '10000000-0000-0000-0000-000000000002'
OBSERVER = '10000000-0000-0000-0000-000000000003'
HISTORICAL = '20000000-0000-0000-0000-000000000001'
SECRET = b'poll-fixture-only-jwt-signing-key-at-least-32-bytes'
OUT = ROOT / 'docs/qa/issue22-polls-20261020'
RESULTS = []

def sql(query, fail_ok=False):
    command = ['docker', '--host=unix:///var/run/docker.sock', 'exec', '-i', 'pokerid-poll-qa-db', 'psql', '-U', 'postgres', '-d', 'postgres', '-At', '-v', 'ON_ERROR_STOP=1']
    result = subprocess.run(command, input=query, text=True, capture_output=True, timeout=20)
    if result.returncode and not fail_ok: raise AssertionError(result.stderr)
    return result if fail_ok else result.stdout.strip()

def jwt(user):
    def enc(value): return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).decode().rstrip('=')
    claims = {'role': 'authenticated' if user else 'anon', 'exp': int(time.time()) + 3600}
    if user: claims['sub'] = user
    message = enc({'alg': 'HS256', 'typ': 'JWT'}) + '.' + enc(claims)
    return message + '.' + base64.urlsafe_b64encode(hmac.new(SECRET, message.encode(), hashlib.sha256).digest()).decode().rstrip('=')

def api(path, data=None, user=OWNER, method=None):
    payload = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(BASE + path, data=payload, method=method or ('POST' if payload is not None else 'GET'), headers={'Authorization': 'Bearer ' + jwt(user), 'Content-Type': 'application/json', 'Prefer': 'return=representation'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response: status, raw = response.status, response.read()
    except urllib.error.HTTPError as error: status, raw = error.code, error.read()
    return status, json.loads(raw) if raw else None

def rpc(name, data, user=OWNER): return api('/rpc/' + name, data, user)
def require_ok(result):
    status, value = result
    assert status in (200, 201, 204), (status, value)
    return value

def reject(result, allowed=(400, 401, 403, 409)):
    status, value = result
    assert status in allowed, (status, value)
    return {'status': status, 'code': value.get('code') if isinstance(value, dict) else None}

def record(name, expected, function):
    try:
        actual = function()
        RESULTS.append({'name': name, 'expected': expected, 'actual': actual, 'status': 'PASS'})
        print('PASS', name, json.dumps(actual, ensure_ascii=False), flush=True)
    except Exception as error:
        RESULTS.append({'name': name, 'expected': expected, 'actual': str(error), 'status': 'FAIL'})
        print('FAIL', name, repr(error), flush=True)

def create(anonymous, count=2, name='fixture poll', user=OWNER, function='create_interactive_post_v4'):
    arguments = {'p_content': name, 'p_kind': 'poll', 'p_options': [str(i) for i in range(count)], 'p_hours': 1}
    if function != 'create_interactive_post': arguments['p_is_anonymous'] = anonymous
    return require_ok(rpc(function, arguments, user))

def vote(post, user, anonymous, option=0):
    return rpc('submit_interactive_response_v2', {'p_post_id': post, 'p_option_index': option, 'p_answer': None, 'p_is_anonymous': anonymous}, user)

def result(post, user): return require_ok(rpc('get_interactive_results_v4', {'p_post_ids': [post]}, user))[0]
def expire(post): sql("update public.post_interactive set closes_at=clock_timestamp()-interval '1 second' where post_id='%s';" % post)
def count_notices(post): return int(sql("select count(*) from public.notifications where type='poll_closed' and post_id='%s';" % post))

def main():
    image = subprocess.check_output(['docker', '--host=unix:///var/run/docker.sock', 'inspect', '--format', '{{.Config.Image}}', 'pokerid-poll-qa-db'], text=True).strip()
    assert image == 'supabase/postgres:17.6.1.136', image
    sql("select cron.alter_job(jobid,active:=false) from cron.job where jobname='pokerid-poll-close-v1';")
    for _ in range(20):
        status, _data = api('/post_interactive?select=post_id&limit=1')
        if status == 200: break
        time.sleep(.5)
    assert status == 200, 'PostgREST schema cache not ready'
    record('official_supabase_auth_uid', 'Real Supabase auth.uid and pg_cron exist', lambda: {'postgres': sql('select version();'), 'auth_uid': sql("select to_regprocedure('auth.uid()')::text;"), 'cron': sql("select extversion from pg_extension where extname='pg_cron';"), 'image': image, 'GoTrue': 'not started; signed local JWT fixtures'})
    def privilege_boundaries():
        value=sql("select bool_and(not p.prosecdef) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('create_interactive_post','create_interactive_post_v2','create_interactive_post_v3','create_interactive_post_v4','submit_interactive_response','submit_interactive_response_v2','get_interactive_results','get_interactive_results_v4');")
        assert value=='t',value
        hidden=api('/rpc/create_poll',{'p_content':'hidden','p_kind':'poll','p_options':['A','B']},OWNER)
        assert hidden[0]==404,hidden
        assert sql("select has_function_privilege('authenticated','poll_private.close_due_polls()','execute');")=='f'
        return {'public_rpcs_security_invoker':True,'private_helper_rest_status':hidden[0],'authenticated_close_execute':False}
    record('privileged_schema_boundary','Privileged implementations are private; system close not executable',privilege_boundaries)
    for n in (2, 3, 4):
        record('create_%d_choices' % n, '2–4 choices accepted', lambda n=n: {'post_id': create(False, n)})
    for options in (['one'], ['0','1','2','3','4'], ['A',' a '], ['', 'B'], ['x'*81,'B'], [None,'B']):
        record('reject_options_' + str(options)[:45], 'Invalid content rejected by direct RPC', lambda options=options: reject(rpc('create_interactive_post_v4', {'p_content': 'fixture', 'p_kind': 'poll', 'p_options': options, 'p_hours': 1, 'p_is_anonymous': False})))
    for name in ('create_interactive_post', 'create_interactive_post_v2', 'create_interactive_post_v3', 'create_interactive_post_v4'):
        record('legacy_question_rejected_' + name, 'Question mode rejected at every legacy RPC', lambda name=name: reject(rpc(name, {'p_content': 'not published', 'p_kind': 'question', 'p_options': None})))
    record('anonymous_user_create_denied', 'anon cannot create', lambda: reject(rpc('create_interactive_post_v4', {'p_content':'guest','p_kind':'poll','p_options':['A','B']}, None), (401,403)))
    named = create(False, name='named fixture')
    anonymous = create(True, name='anonymous fixture')
    record('named_vote', 'Owner may vote on named poll', lambda: {'response':require_ok(vote(named,OWNER,False))})
    # Above owner vote and below voter vote are distinct; owner voting is allowed.
    record('anonymous_vote', 'Anonymous vote accepted', lambda: {'response': require_ok(vote(anonymous, VOTER, True))})
    record('named_voter_response', 'Named voter accepted', lambda: {'response': require_ok(vote(named, VOTER, False))})
    record('one_vote_only', 'Duplicate rejected with unique violation', lambda: reject(vote(anonymous, VOTER, True), (409,)))
    record('privacy_mode_tamper', 'Cannot change poll privacy at submission', lambda: reject(vote(anonymous, OBSERVER, False), (400,)))
    record('invalid_choice_rpc', 'Out of range option rejected', lambda: reject(vote(anonymous, OBSERVER, True, 99), (400,)))
    for user, label in ((OWNER,'owner'), (VOTER,'voter'), (OBSERVER,'observer')):
        def anonymous_read(user=user):
            value = result(anonymous,user)
            encoded = json.dumps(value)
            assert value['voters']==[] and value['answers']==[] and value['total_votes']==1, value
            assert VOTER not in encoded and 'fixture_voter' not in encoded and 'created_at' not in encoded and 'user_id' not in encoded, value
            assert value['my_option_index'] == (0 if user==VOTER else None)
            raw = require_ok(api('/post_interactive_responses?post_id=eq.'+anonymous, user=user))
            assert raw == [], raw
            return {'aggregate':value,'direct_rows':raw}
        record('anonymous_privacy_'+label, 'No voter ID, profile or timestamp from RPC/direct REST', anonymous_read)
        def named_read(user=user):
            value = result(named,user)
            assert any(v.get('poker_id')=='fixture_voter' for v in value['voters']), value
            return {'named_voters_visible':True,'total_votes':value['total_votes']}
        record('named_display_'+label, 'Named voters visible as disclosed', named_read)
    def legacy_results():
        value=require_ok(rpc('get_interactive_results',{'p_post_ids':[anonymous]},OBSERVER))
        encoded=json.dumps(value)
        assert VOTER not in encoded and 'fixture_voter' not in encoded and 'created_at' not in encoded
        return {'response':value}
    record('legacy_results_safe','Old results RPC does not expose identifiers',legacy_results)
    legacy = create(True, function='create_interactive_post')
    def legacy_privacy():
        value=require_ok(api('/post_interactive?post_id=eq.'+legacy+'&select=is_anonymous'))[0]['is_anonymous']
        assert value is True and result(legacy,OWNER)['voters']==[]
        return {'is_anonymous':value}
    record('legacy_create_conservative_privacy', 'Old no-mode caller defaults to anonymous',legacy_privacy)
    record('legacy_vote_compatible', 'Old vote client uses stored poll mode', lambda: {'response':require_ok(rpc('submit_interactive_response', {'p_post_id':legacy,'p_option_index':1,'p_answer':None}, VOTER))})
    record('direct_vote_insert_denied', 'Raw INSERT never a voting API', lambda: reject(api('/post_interactive_responses', {'post_id':anonymous,'user_id':OBSERVER,'option_index':0}, OBSERVER), (401,403)))
    record('direct_question_table_insert_denied', 'Cannot bypass RPC to make question metadata', lambda: reject(api('/post_interactive', {'post_id':named,'kind':'question','options':[]}, OWNER), (401,403)))
    for user,label in ((OWNER,'owner'), (VOTER,'voter'), (OBSERVER,'observer'), (None,'anon')):
        record('close_rpc_denied_'+label, 'Clients cannot execute system close', lambda user=user: reject(rpc('finish_due_polls_v1', {}, user), (401,403)))
    record('legacy_notification_insert_grant_preserved', 'INSERT grant stays intact', lambda: {'has_insert':sql("select has_table_privilege('authenticated','public.notifications','INSERT');")} if sql("select has_table_privilege('authenticated','public.notifications','INSERT');")=='t' else (_ for _ in ()).throw(AssertionError('grant revoked')))
    record('legacy_nonpoll_notification_still_works', 'Existing INSERT behavior retained', lambda: {'response':require_ok(api('/notifications', {'user_id':OWNER,'actor_id':VOTER,'type':'like','post_id':named}, VOTER))})
    record('forged_close_direct_denied', 'Restrictive RLS defeats permissive legacy INSERT policy', lambda: reject(api('/notifications', {'user_id':OWNER,'actor_id':VOTER,'type':'poll_closed','post_id':anonymous}, VOTER), (401,403)))
    record('forged_close_definer_denied', 'Trigger also blocks legacy SECURITY DEFINER bypass', lambda: reject(rpc('legacy_notification_insert_fixture', {'p_user_id':OWNER,'p_actor_id':VOTER,'p_type':'poll_closed','p_post_id':anonymous}, VOTER), (401,403)))
    expire(anonymous)
    record('deadline_vote_rejected', 'No votes after deadline', lambda: reject(vote(anonymous, OBSERVER, True), (400,)))
    def concurrent_close():
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            values=list(pool.map(lambda _:sql('select poll_private.close_due_polls();'),range(2)))
        assert count_notices(anonymous)==1, values
        assert sql('select poll_private.close_due_polls();')=='0'
        return {'two_worker_counts':values,'notifications':count_notices(anonymous),'retry_notifications':count_notices(anonymous)}
    record('close_concurrency_and_retry', 'Exactly one close despite simultaneous workers/retry', concurrent_close)
    for user,label in ((OWNER,'owner'),(VOTER,'voter'),(OBSERVER,'observer')):
        def history(user=user):
            rows = require_ok(api('/notifications?post_id=eq.'+anonymous+'&type=eq.poll_closed', user=user))
            encoded=json.dumps(rows)
            assert VOTER not in encoded and 'fixture_voter' not in encoded, rows
            assert len(rows)==(1 if user==OWNER else 0), rows
            return {'rows':len(rows),'anonymous_voter_identity_absent':True}
        record('close_history_privacy_'+label, 'Owner-only notification, no anonymous voter ID',history)
    def mark_read():
        rows=require_ok(api('/notifications?post_id=eq.'+anonymous+'&type=eq.poll_closed', {'read_at':'2026-10-20T00:00:00Z'}, OWNER, 'PATCH'))
        assert len(rows)==1 and rows[0]['read_at'], rows
        return {'marked_read':True}
    record('owner_can_mark_close_read', 'System notification immutability still allows read_at',mark_read)
    record('close_notification_rewrite_denied','Cannot rewrite a close notification identity',lambda:reject(api('/notifications?post_id=eq.'+anonymous+'&type=eq.poll_closed',{'actor_id':VOTER},OWNER,'PATCH'),(401,403)))
    atomic=create(True,name='atomic close fixture');expire(atomic)
    def atomicity():
        sql("create function public.fail_close_fixture() returns trigger language plpgsql as $$begin if new.post_id='%s' then raise exception 'injected isolated notification failure'; end if;return new;end$$; create trigger fail_close_fixture before insert on public.notifications for each row execute function public.fail_close_fixture();"%atomic)
        failed=sql('select poll_private.close_due_polls();',True)
        assert failed.returncode!=0
        assert count_notices(atomic)==0
        assert sql("select count(*) from poll_private.close_receipts where post_id='%s';"%atomic)=='0'
        sql('drop trigger fail_close_fixture on public.notifications;drop function public.fail_close_fixture();')
        sql('select poll_private.close_due_polls();')
        assert count_notices(atomic)==1
        return {'failure_raised':True,'failed_receipt_rows':0,'after_retry_notifications':1}
    record('close_atomic_failure_and_retry','Failed transaction retains no receipt/partial notification; retry succeeds',atomicity)
    blocked=create(True,name='blocked fixture')
    sql("insert into public.user_blocks values('%s','%s');"%(OWNER,OBSERVER))
    record('blocked_actor_vote_denied','Explicit block respected by definer RPC',lambda:reject(vote(blocked,OBSERVER,True),(401,403)))
    record('blocked_actor_results_denied','Blocked viewer cannot bypass UI via results RPC',lambda:reject(rpc('get_interactive_results_v4',{'p_post_ids':[blocked]},OBSERVER),(401,403)))
    sql('delete from public.user_blocks;')
    cron=create(True,name='actual cron fixture');expire(cron)
    def actual_cron():
        sql("select cron.alter_job(jobid,active:=true) from cron.job where jobname='pokerid-poll-close-v1';")
        start=time.monotonic()
        while time.monotonic()-start<75:
            if count_notices(cron)==1: break
            time.sleep(1)
        elapsed=round(time.monotonic()-start,2)
        assert count_notices(cron)==1,'No actual cron close within 75 seconds'
        succeeded=sql("select count(*) from cron.job_run_details d join cron.job j on j.jobid=d.jobid where j.jobname='pokerid-poll-close-v1' and d.status='succeeded';")
        assert int(succeeded)>=1
        sql('select poll_private.close_due_polls();')
        assert count_notices(cron)==1
        return {'elapsed_seconds':elapsed,'cron_succeeded_runs':int(succeeded),'notifications_after_retry':1}
    record('actual_pg_cron_close','Real scheduler executes and duplicate retry stays one',actual_cron)
    before=sql('select count(*) from public.posts;')
    with (ROOT/'sql/poll_only/disable_candidate.sql').open() as stream: sql(stream.read())
    record('disable_retains_all_posts','Feature-disable never deletes user data',lambda:{'before':before,'after':sql('select count(*) from public.posts;')} if sql('select count(*) from public.posts;')==before else (_ for _ in ()).throw(AssertionError('data lost')))
    record('historical_question_retained','Original question and answer still present internally',lambda:{'question_rows':sql("select count(*) from public.post_interactive where post_id='%s' and kind='question';"%HISTORICAL),'answer_rows':sql("select count(*) from public.post_interactive_responses where post_id='%s';"%HISTORICAL)} if sql("select count(*) from public.post_interactive_responses where post_id='%s';"%HISTORICAL)=='1' else (_ for _ in ()).throw(AssertionError('history lost')))
    record('disable_blocks_writes','Rollback disables feature APIs without resurrecting question boxes',lambda:reject(rpc('create_interactive_post_v4',{'p_content':'disabled','p_kind':'poll','p_options':['A','B']},OWNER),(401,403)))

try:
    main()
except Exception as error:
    RESULTS.append({'name':'harness_setup_or_dependency','status':'FAIL','actual':repr(error)})
    print('FAIL harness',repr(error),flush=True)
summary={status:sum(row['status']==status for row in RESULTS) for status in ('PASS','FAIL','BLOCKED')}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'database-results.json').write_text(json.dumps({'configuration':'official Supabase Postgres 17.6.1.136 + PostgREST 14.18; GoTrue absent; locally signed JWTs; seeded synthetic app schema; NOT production parity','summary':summary,'tests':RESULTS},ensure_ascii=False,indent=2)+'\n')
print('SUMMARY',summary,flush=True)
raise SystemExit(1 if summary['FAIL'] else 0)
