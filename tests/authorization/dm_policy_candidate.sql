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
