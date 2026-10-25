-- Read-only production preflight. This file intentionally fails while the
-- privileged Storage writer cannot be proven immutable and reservation-fenced.
-- Do NOT treat RLS policies as a service_role protection mechanism.
\set ON_ERROR_STOP on
DO $release_gate$
DECLARE bypass boolean;
DECLARE can_insert boolean;
DECLARE can_update boolean;
DECLARE can_delete boolean;
BEGIN
 SELECT rolbypassrls INTO bypass FROM pg_roles WHERE rolname='service_role';
 SELECT has_table_privilege('service_role','storage.objects','INSERT'),
        has_table_privilege('service_role','storage.objects','UPDATE'),
        has_table_privilege('service_role','storage.objects','DELETE')
 INTO can_insert,can_update,can_delete;
 IF coalesce(bypass,false) AND
    (coalesce(can_insert,false) OR coalesce(can_update,false) OR coalesce(can_delete,false)) THEN
   RAISE EXCEPTION 'NO-GO: service_role bypasses RLS and has Storage write privileges; require independently verified writer fencing before video release';
 END IF;
 RAISE NOTICE 'This SQL check alone cannot attest privileged Storage API routes; independent HTTP tests are mandatory';
END $release_gate$;
