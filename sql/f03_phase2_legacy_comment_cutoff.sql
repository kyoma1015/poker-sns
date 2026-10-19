-- F03 phase two: preserve legacy comment notifications without guessing IDs.
-- Applied to Supabase poker-id on 2026-10-19.
-- Pre-existing comments are not eligible for new RPC notification replay.
-- No existing notification rows are modified.
-- Direct INSERT remains available for legacy production clients; F03 is NOT fully resolved.
-- Migration boundary (UTC): 2026-10-19 12:20:19.274508+00
-- This is an auditable record of the applied function definition.
CREATE OR REPLACE FUNCTION public.create_verified_notification(p_event_type text, p_event_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  v_actor uuid := auth.uid();
  v_recipient uuid;
  v_post_id uuid;
  v_event_key text;
  v_comment_created_at timestamptz;
BEGIN
  IF v_actor IS NULL THEN
    RAISE EXCEPTION 'Authentication required' USING ERRCODE = '42501';
  END IF;
  IF p_event_type = 'like' THEN
    SELECT p.user_id, p.id INTO v_recipient, v_post_id
    FROM public.post_likes l JOIN public.posts p ON p.id = l.post_id
    WHERE l.post_id = p_event_id AND l.user_id = v_actor LIMIT 1;
    v_event_key := 'like:' || v_actor::text || ':' || p_event_id::text;
  ELSIF p_event_type = 'comment' THEN
    SELECT p.user_id, p.id, c.created_at INTO v_recipient, v_post_id, v_comment_created_at
    FROM public.post_comments c JOIN public.posts p ON p.id = c.post_id
    WHERE c.id = p_event_id AND c.user_id = v_actor LIMIT 1;
    v_event_key := 'comment:' || p_event_id::text;
  ELSIF p_event_type = 'follow' THEN
    SELECT f.following_id INTO v_recipient
    FROM public.follows f
    WHERE f.follower_id = v_actor AND f.following_id = p_event_id LIMIT 1;
    v_event_key := 'follow:' || v_actor::text || ':' || p_event_id::text;
  ELSE
    RAISE EXCEPTION 'Unsupported notification type' USING ERRCODE = '22023';
  END IF;
  IF v_recipient IS NULL OR v_recipient = v_actor THEN
    RAISE EXCEPTION 'Notification event not found' USING ERRCODE = '22023';
  END IF;
  IF p_event_type = 'comment'
     AND v_comment_created_at < '2026-10-19 12:20:19.274508+00'::timestamptz THEN
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.user_blocks b
    WHERE (b.blocker_id = v_actor AND b.blocked_id = v_recipient)
       OR (b.blocker_id = v_recipient AND b.blocked_id = v_actor)
  ) THEN RETURN; END IF;
  IF p_event_type IN ('like', 'follow') AND EXISTS (
    SELECT 1 FROM public.notifications n
    WHERE n.actor_id = v_actor AND n.user_id = v_recipient
      AND n.type = p_event_type
      AND n.post_id IS NOT DISTINCT FROM v_post_id
  ) THEN RETURN; END IF;
  INSERT INTO public.notifications(user_id, actor_id, type, post_id, event_key)
  VALUES (v_recipient, v_actor, p_event_type, v_post_id, v_event_key)
  ON CONFLICT DO NOTHING;
END;
$$;
REVOKE ALL ON FUNCTION public.create_verified_notification(text,uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.create_verified_notification(text,uuid) TO authenticated;
