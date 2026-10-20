-- Required grants for interactive feed queries; writes remain RPC-only.
revoke all on table public.post_interactive, public.post_interactive_responses from anon, authenticated;
grant select on table public.post_interactive, public.post_interactive_responses to authenticated;
