-- SYNTHETIC CONTRACT ONLY. Not a dump, migration, Supabase Auth or production schema.
CREATE ROLE model_authenticated NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE model_anon NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE SCHEMA dm_model;
GRANT USAGE ON SCHEMA dm_model TO model_authenticated, model_anon;
CREATE FUNCTION dm_model.uid() RETURNS uuid LANGUAGE sql STABLE SECURITY INVOKER
SET search_path = pg_catalog AS $$ SELECT nullif(current_setting('model.subject',true),'')::uuid $$;
CREATE TABLE dm_model.messages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), sender_id uuid NOT NULL,
 receiver_id uuid NOT NULL, content text NOT NULL CHECK(length(btrim(content))>0),
 read_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(sender_id<>receiver_id)
);
CREATE TABLE dm_model.blocks (blocker_id uuid NOT NULL, blocked_id uuid NOT NULL, PRIMARY KEY(blocker_id,blocked_id));
INSERT INTO dm_model.messages(id,sender_id,receiver_id,content) VALUES
 ('00000000-0000-0000-0000-000000000001','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','committed AB'),
 ('00000000-0000-0000-0000-000000000002','cccccccc-cccc-cccc-cccc-cccccccccccc','dddddddd-dddd-dddd-dddd-dddddddddddd','private CD'),
 ('00000000-0000-0000-0000-000000000003','cccccccc-cccc-cccc-cccc-cccccccccccc','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','rollback CB');
INSERT INTO dm_model.blocks VALUES('dddddddd-dddd-dddd-dddd-dddddddddddd','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa');
ALTER TABLE dm_model.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE dm_model.blocks ENABLE ROW LEVEL SECURITY;
CREATE POLICY block_read ON dm_model.blocks FOR SELECT TO model_authenticated
 USING(dm_model.uid() IN(blocker_id,blocked_id));
GRANT SELECT ON dm_model.blocks TO model_authenticated;
-- Deliberately weak comparison fixture: recipient RLS alone does not protect columns.
GRANT SELECT,INSERT,UPDATE,DELETE ON dm_model.messages TO model_authenticated;
CREATE POLICY participant_read ON dm_model.messages FOR SELECT TO model_authenticated
 USING(dm_model.uid() IN(sender_id,receiver_id));
CREATE POLICY sender_insert ON dm_model.messages FOR INSERT TO model_authenticated
 WITH CHECK(sender_id=dm_model.uid());
CREATE POLICY recipient_ack ON dm_model.messages FOR UPDATE TO model_authenticated
 USING(receiver_id=dm_model.uid()) WITH CHECK(receiver_id=dm_model.uid());
CREATE FUNCTION dm_model.ok(label text, condition boolean) RETURNS text
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN IF condition IS DISTINCT FROM true THEN RAISE EXCEPTION 'FAIL:%',label; END IF;
RETURN 'PASS:'||label; END $$;
CREATE FUNCTION dm_model.denied(statement text) RETURNS boolean
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN EXECUTE statement; RETURN false;
EXCEPTION WHEN insufficient_privilege OR check_violation THEN RETURN true; END $$;
CREATE FUNCTION dm_model.affected(statement text) RETURNS integer LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE n integer; BEGIN EXECUTE statement; GET DIAGNOSTICS n=ROW_COUNT; RETURN n; END $$;
