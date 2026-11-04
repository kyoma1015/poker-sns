-- Atomic, fail-closed preparation for the disposable model only.
BEGIN;
DO $guard$
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles r WHERE r.rolname IN('model_authenticated','model_anon')
  AND (r.rolsuper OR r.rolbypassrls OR pg_has_role(r.oid,(SELECT relowner FROM pg_class WHERE oid='dm_model.messages'::regclass),'USAGE')))
 THEN RAISE EXCEPTION 'DM_UNSAFE_ACTOR_ROLE'; END IF;
 IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid='dm_model.messages'::regclass)
 THEN RAISE EXCEPTION 'DM_RLS_DISABLED'; END IF;
 IF EXISTS(SELECT 1 FROM pg_policy WHERE polrelid='dm_model.messages'::regclass
  AND polname NOT IN('participant_read','sender_insert','recipient_ack'))
 THEN RAISE EXCEPTION 'DM_UNREVIEWED_POLICY'; END IF;
END $guard$;
-- REVIEW PROPOSAL / disposable dm_model ONLY. NEVER apply as a production migration.
-- Actual schema, role inheritance, all permissive policies, column ACLs, helpers and
-- RPC/view paths must be inventoried before adapting this proposal.
REVOKE ALL ON dm_model.messages FROM PUBLIC,model_anon,model_authenticated;
REVOKE ALL(id,sender_id,receiver_id,content,read_at,created_at)
 ON dm_model.messages FROM PUBLIC,model_anon,model_authenticated;
GRANT SELECT ON dm_model.messages TO model_authenticated;
GRANT INSERT(sender_id,receiver_id,content) ON dm_model.messages TO model_authenticated;
GRANT UPDATE(read_at) ON dm_model.messages TO model_authenticated;
DROP POLICY sender_insert ON dm_model.messages;
CREATE POLICY sender_insert ON dm_model.messages FOR INSERT TO model_authenticated
 WITH CHECK(dm_model.uid() IS NOT NULL AND sender_id=dm_model.uid()
 AND sender_id<>receiver_id AND NOT EXISTS(
 SELECT 1 FROM dm_model.blocks b
 WHERE (b.blocker_id=sender_id AND b.blocked_id=receiver_id)
 OR (b.blocker_id=receiver_id AND b.blocked_id=sender_id)));
-- Keep receiver USING+WITH CHECK; SELECT visibility alone never authorizes writes.
-- No DELETE, sender/content/recipient reassignment or client-set INSERT read_at.
-- Read visibility of historical blocked conversations and acknowledgement semantics
-- require approved product contracts; do not infer them from this model.

-- Replace only these reviewed model policy definitions; unknown policies are not removed.
DROP POLICY participant_read ON dm_model.messages;
CREATE POLICY participant_read ON dm_model.messages FOR SELECT TO model_authenticated
 USING(dm_model.uid() IN(sender_id,receiver_id));
DROP POLICY recipient_ack ON dm_model.messages;
CREATE POLICY recipient_ack ON dm_model.messages FOR UPDATE TO model_authenticated
 USING(receiver_id=dm_model.uid()) WITH CHECK(receiver_id=dm_model.uid());
DO $guard$
BEGIN
 -- Effective privileges include inherited roles and PUBLIC; direct REVOKE is insufficient.
 IF has_table_privilege('model_authenticated','dm_model.messages','DELETE')
 OR EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid='dm_model.messages'::regclass
  AND attnum>0 AND NOT attisdropped AND attname<>'read_at'
  AND has_column_privilege('model_authenticated','dm_model.messages',attname,'UPDATE'))
 OR EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid='dm_model.messages'::regclass
  AND attnum>0 AND NOT attisdropped AND attname NOT IN('sender_id','receiver_id','content')
  AND has_column_privilege('model_authenticated','dm_model.messages',attname,'INSERT'))
 OR has_any_column_privilege('model_anon','dm_model.messages','SELECT')
 OR has_any_column_privilege('model_anon','dm_model.messages','INSERT')
 OR has_any_column_privilege('model_anon','dm_model.messages','UPDATE')
 OR has_table_privilege('model_anon','dm_model.messages','DELETE')
 THEN RAISE EXCEPTION 'DM_UNEXPECTED_EFFECTIVE_PRIVILEGES'; END IF;
END $guard$;
COMMIT;
