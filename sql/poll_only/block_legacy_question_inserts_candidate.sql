-- Poll-only emergency compatibility guard. Non-destructive: retains all historical rows.
-- Install on production only after independent isolated DB QA and approval.
begin;
create or replace function public.reject_new_question_interactive()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $guard$
begin
  if new.kind is distinct from 'poll' then
    raise exception 'Only polls are supported' using errcode = '22023';
  end if;
  return new;
end
$guard$;
revoke all on function public.reject_new_question_interactive() from public, anon, authenticated;
drop trigger if exists reject_new_question_interactive on public.post_interactive;
create trigger reject_new_question_interactive
before insert or update of kind on public.post_interactive
for each row execute function public.reject_new_question_interactive();
commit;
