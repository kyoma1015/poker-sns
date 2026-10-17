-- Do not expose answer timestamps: they can be correlated with user activity.
create or replace function public.get_interactive_results(p_post_ids uuid[])
returns table(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean)
language sql stable security definer set search_path = '' as $$
 select i.post_id,
   (select count(*) from public.post_interactive_responses r where r.post_id=i.post_id),
   (select coalesce(jsonb_object_agg(t.option_index::text,t.cnt),'{}'::jsonb)
      from (select r.option_index,count(*) cnt from public.post_interactive_responses r
            where r.post_id=i.post_id and r.option_index is not null group by r.option_index) t),
   (select coalesce(jsonb_agg(jsonb_build_object('answer',r.answer) order by r.created_at),'[]'::jsonb)
      from public.post_interactive_responses r where r.post_id=i.post_id and r.answer is not null),
   (select r.option_index from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid())),
   exists(select 1 from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid()))
 from public.post_interactive i
 where i.post_id=any(p_post_ids)
   and (select auth.uid()) is not null
   and exists(select 1 from public.posts p where p.id=i.post_id);
$$;
revoke all on function public.get_interactive_results(uuid[]) from public;
grant execute on function public.get_interactive_results(uuid[]) to authenticated;
