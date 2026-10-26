-- Disposable PostgreSQL only: real attested RPC execution and rejection cases.
-- Independent deterministic Node.js binary-HMAC vector (also checked by Node in CI).
-- Fixture-only key 0x41 * 32, expiration deliberately in the future for vector stability.
do $vector$
declare
 o uuid:='10000000-0000-0000-0000-000000000001';
 p text:='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000009.mp4';
 g uuid:='d71e6f03-8ac2-4a55-91bf-fc3296e7184d';
 payload bytea;actual text;
begin
 payload:=decode('01','hex')||decode(replace(o::text,'-',''),'hex')||
  set_byte(decode('00','hex'),0,octet_length(convert_to(p,'UTF8')))||convert_to(p,'UTF8')||
  decode(replace(g::text,'-',''),'hex')||decode(repeat('a',64),'hex')||
  pg_catalog.int4send(2000)||extensions.digest(convert_to('test','UTF8'),'sha256')||
  pg_catalog.int8send(1893456000::bigint)||decode(repeat('b',32),'hex');
 actual:=encode(extensions.hmac(payload,decode(repeat('41',32),'hex'),'sha256'),'hex');
 if actual<>'d50ae4bb28c6c60b60f7e39b9acec328d537e188b78567ff4ddeab0de0a34779'
 then raise exception 'Node/Postgres HMAC vector mismatch'; end if;
end $vector$;

insert into video_private.attestation_keys(key_id,secret,active)
values(1,decode(repeat('41',32),'hex'),true);
insert into public.video_reserved_object_keys(bucket_id,object_path,owner_id)
values('post-videos','10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000009.mp4',
'10000000-0000-0000-0000-000000000001');
insert into storage.objects(id,bucket_id,name,owner_id) values
('d71e6f03-8ac2-4a55-91bf-fc3296e7184d','post-videos',
'10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000009.mp4',
'10000000-0000-0000-0000-000000000001');
grant execute on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;
-- Ensure the authenticated role can only access the RPC, not the secret or nonce ledger.
do $check$
begin
 if has_table_privilege('authenticated','video_private.attestation_keys','SELECT')
 or has_table_privilege('authenticated','video_private.consumed_nonces','INSERT')
 then raise exception 'secret or nonce ledger exposed'; end if;
end $check$;
-- The following in-process fixture runs as DBA with an emulated JWT claim;
-- real authenticated PostgREST role coverage remains a separate release blocker.
select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000001',false);
do $test$
declare
 o uuid:='10000000-0000-0000-0000-000000000001';
 p text:='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000009.mp4';
 g uuid:='d71e6f03-8ac2-4a55-91bf-fc3296e7184d';
 h text:=repeat('a',64); n text:=repeat('b',32); content text:='test';
 expires bigint:=extract(epoch from clock_timestamp())::bigint+120;
 payload bytea;signature text;result uuid;
begin
 -- SQL fixture derives signature from a disposable key, never from the HTTP client.
 payload:=decode('01','hex')||decode(replace(o::text,'-',''),'hex')||
  set_byte(decode('00','hex'),0,octet_length(convert_to(p,'UTF8')))||convert_to(p,'UTF8')||
  decode(replace(g::text,'-',''),'hex')||decode(h,'hex')||
  pg_catalog.int4send(2000)||extensions.digest(convert_to(content,'UTF8'),'sha256')||
  pg_catalog.int8send(expires)||decode(n,'hex');
 -- In real deployment this signature is created by the finalizer, not DB.
 -- Test-only key is supplied as a literal in the disposable fixture.
 signature:=encode(extensions.hmac(payload,decode(repeat('41',32),'hex'),'sha256'),'hex');
 -- Rotation isolation: inactive key IDs, unknown key IDs, and active keys
 -- with a different secret must never validate an old signature.
 insert into video_private.attestation_keys(key_id,secret,active)
 values(2,decode(repeat('42',32),'hex'),false);
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,2::smallint);
  raise exception 'inactive rotation key accepted';
 exception when raise_exception then
  if SQLERRM='inactive rotation key accepted' then raise; end if;
 end;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,3::smallint);
  raise exception 'unknown rotation key accepted';
 exception when raise_exception then
  if SQLERRM='unknown rotation key accepted' then raise; end if;
 end;
 update video_private.attestation_keys set active=true where key_id=2;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,2::smallint);
  raise exception 'cross-key attestation accepted';
 exception when raise_exception then
  if SQLERRM='cross-key attestation accepted' then raise; end if;
 end;
 update video_private.attestation_keys set active=false where key_id=2;
 -- Retiring the original signing key must revoke otherwise valid old proofs.
 update video_private.attestation_keys set active=false where key_id=1;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,1::smallint);
  raise exception 'retired original key accepted';
 exception when raise_exception then
  if SQLERRM='retired original key accepted' then raise; end if;
 end;
 update video_private.attestation_keys set active=true where key_id=1;
 -- A correctly signed, already-expired proof must fail specifically on
 -- the expiration guard, not incidentally on an HMAC mismatch.
 declare
  expired_at bigint:=extract(epoch from clock_timestamp())::bigint-60;
  expired_payload bytea;
  expired_signature text;
 begin
  expired_payload:=decode('01','hex')||decode(replace(o::text,'-',''),'hex')||
   set_byte(decode('00','hex'),0,octet_length(convert_to(p,'UTF8')))||convert_to(p,'UTF8')||
   decode(replace(g::text,'-',''),'hex')||decode(h,'hex')||
   pg_catalog.int4send(2000)||extensions.digest(convert_to(content,'UTF8'),'sha256')||
   pg_catalog.int8send(expired_at)||decode(n,'hex');
  expired_signature:=encode(extensions.hmac(expired_payload,decode(repeat('41',32),'hex'),'sha256'),'hex');
  begin
   perform public.video_publish_attested_v1(o,p,g,h,2000,content,expired_at,n,expired_signature,1::smallint);
   raise exception 'expired proof accepted';
  exception when raise_exception then
   if SQLERRM<>'invalid attestation claims' then raise; end if;
  end;
 end;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,repeat('0',64),1::smallint);
  raise exception 'forged signature accepted';
 exception when raise_exception then
  if SQLERRM='forged signature accepted' then raise; end if;
 end;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,'tampered',expires,n,signature,1::smallint);
  raise exception 'tampered content accepted';
 exception when raise_exception then
  if SQLERRM='tampered content accepted' then raise; end if;
 end;
 -- A valid signature cannot authorize a different post body or duration.
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2001,content,expires,n,signature,1::smallint);
  raise exception 'altered duration accepted';
 exception when raise_exception then
  if SQLERRM='altered duration accepted' then raise; end if;
 end;
 -- A correctly signed proof must still fail for a different Storage generation.
 begin
  perform public.video_publish_attested_v1(o,p,'f0000000-0000-0000-0000-000000000001'::uuid,h,2000,content,expires,n,signature,1::smallint);
  raise exception 'mismatched generation accepted';
 exception when raise_exception then
  if SQLERRM='mismatched generation accepted' then raise; end if;
 end;
 -- A different caller cannot publish the owner's media, even with a valid signature.
 perform set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000002',true);
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,1::smallint);
  raise exception 'foreign JWT accepted';
 exception when raise_exception then
  if SQLERRM='foreign JWT accepted' then raise; end if;
 end;
 perform set_config('request.jwt.claim.sub',o::text,true);
 result:=public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,1::smallint);
 if result is null then raise exception 'valid attestation rejected'; end if;
 begin
  perform public.video_publish_attested_v1(o,p,g,h,2000,content,expires,n,signature,1::smallint);
  raise exception 'replayed nonce accepted';
 exception when unique_violation then null;
 end;
 if (select count(*) from public.posts where video_path=p)<>1 then
  raise exception 'publish was not exactly once'; end if;
 if (select count(*) from video_private.consumed_nonces where nonce=decode(n,'hex'))<>1 then
  raise exception 'nonce was not consumed exactly once'; end if;
end $test$;
