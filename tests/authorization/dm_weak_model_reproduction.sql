-- Fixed unsafe comparison only, rolled back; not an observed production exploit.
BEGIN;
SET LOCAL ROLE model_authenticated;
SELECT set_config('model.subject','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',true);
UPDATE dm_model.messages SET content='recipient rewrote sender content'
 WHERE id='00000000-0000-0000-0000-000000000001';
SELECT dm_model.ok('WEAK_MODEL_CONTENT_REWRITE_OBSERVED',
 (SELECT content='recipient rewrote sender content' FROM dm_model.messages WHERE id='00000000-0000-0000-0000-000000000001'));
ROLLBACK;
