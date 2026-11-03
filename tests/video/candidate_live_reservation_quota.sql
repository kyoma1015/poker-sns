-- CANDIDATE ONLY: review and run against isolated test database after validation.
-- Preserve immutable expired reservations, Storage objects and published posts.
-- Quota counts only live reservations; expired keys remain permanently non-reusable.
CREATE OR REPLACE FUNCTION public.video_cloud_reserve(p_path text, p_sha256 text, p_size bigint, p_mime text, p_content text)
 RETURNS timestamp with time zone
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare r video_cloud.reservations%rowtype;
begin
 if not public.video_cloud_allowed() or auth.uid() is null then raise exception 'test user denied'; end if;
 if p_path is null or split_part(p_path,'/',1)<>auth.uid()::text then raise exception 'owner denied'; end if;
 -- Serialize same-owner reservations and quota decisions across tabs.
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,0));
 select * into r from video_cloud.reservations where path=p_path for update;
 if found then
  if r.owner_id<>auth.uid() or r.sha256 is distinct from p_sha256 or r.size is distinct from p_size
   or r.mime is distinct from p_mime or r.content is distinct from p_content
   or r.expires_at<=clock_timestamp() then raise exception 'reservation conflict'; end if;
  return r.expires_at;
 end if;
 if (select count(*) from video_cloud.reservations where owner_id=auth.uid() and expires_at>clock_timestamp())>=10 then
  raise exception 'test quota exceeded'; end if;
 insert into video_cloud.reservations(path,owner_id,sha256,size,mime,content)
 values(p_path,auth.uid(),p_sha256,p_size,p_mime,p_content) returning * into r;
 return r.expires_at;
end $function$
;
