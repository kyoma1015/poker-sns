import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { randomBytes, randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { createClient } from '@supabase/supabase-js'
import { videoBudgetCredential } from '../../server/video-budget.mjs'

const env = Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV, 'utf8').split('\n')
  .filter(line => line.includes('=')).map(line => {
    const index = line.indexOf('=')
    return [line.slice(0, index), line.slice(index + 1).replace(/^["']|["']$/g, '')]
  }))
const url = env.API_URL
const db = new URL(env.DB_URL)
assert.equal(url, 'http://127.0.0.1:56321')
assert.equal(db.hostname, '127.0.0.1')
assert.equal(db.port, '56322')
const sql = (command, ...args) => execFileSync('psql', [env.DB_URL, '-X', '-v', 'ON_ERROR_STOP=1',
  ...args, command], { stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8' }).trim()
const anon = env.ANON_KEY || env.PUBLISHABLE_KEY
const password = randomBytes(24).toString('hex')
async function account() {
  const client = createClient(url, anon, { auth: { persistSession: false, autoRefreshToken: false } })
  const email = randomUUID() + '@example.invalid'
  const { data, error } = await client.auth.signUp({ email, password })
  assert.ifError(error)
  assert.ok(data.session)
  return { client, email, id: data.user.id, token: data.session.access_token }
}
const [owner, other, reader] = await Promise.all([account(), account(), account()])
const key = randomBytes(32).toString('hex')
sql(`create table if not exists video_private.general_public_rollout (
  singleton boolean primary key, enabled boolean not null);
insert into video_private.general_public_rollout values(true, false) on conflict do nothing;
create or replace function public.video_rollout_member() returns boolean language sql stable as 'select auth.uid() is not null';
create or replace function public.video_rollout_allowed() returns boolean language sql stable as 'select auth.uid() is not null';
create or replace function public.video_rollout_visible(text) returns boolean language sql stable as 'select true';
drop policy if exists video_rollout_storage_read on storage.objects;
create policy video_rollout_storage_read on storage.objects as restrictive for select to authenticated using(true);`, '-c')
sql('sql/video_initial_usage_budget_review_only.sql', '-f')
sql(`update video_private.usage_budget set enabled=true, reads_enabled=true,
 reader_id='${reader.id}', meter_key_sha256=sha256(convert_to('${key}','UTF8')),
 shared_total=100000, monthly_operations=2;`, '-c')
sql("update public.video_reserved_object_keys set created_at=now()-interval '2 days'; notify pgrst, 'reload schema';", '-c')
const reservations = await Promise.all([owner, other].flatMap(account =>
  Array.from({ length: 4 }, async () => {
    const path = account.id + '/' + randomUUID() + '.webm'
    const response = await account.client.rpc('video_reserve_object_key', { p_owner: account.id, p_path: path })
    return { account, path, response }
  })))
const allowed = reservations.filter(record => !record.response.error)
assert.equal(allowed.length, 5, 'parallel accounts share exactly five reservations')
for (const account of [owner, other]) assert.ok(allowed.filter(record => record.account === account).length <= 3)
const { account: uploader, path } = allowed[0]
const bytes = Buffer.from('isolated budget Storage fixture')
const bucket = uploader.client.storage.from('post-videos')
assert.ifError((await bucket.upload(path, bytes, { contentType: 'video/webm', upsert: false })).error)
assert.ok((await bucket.download(path)).error)
assert.ok((await bucket.createSignedUrl(path, 60)).error)
assert.ok((await other.client.storage.from('post-videos').download(path)).error)
assert.ok((await reader.client.rpc('video_reserve_object_key', {
  p_owner: reader.id, p_path: reader.id + '/' + randomUUID() + '.webm',
})).error)
const missingKey = await uploader.client.rpc('video_meter_operation', { p_operation: 'media', p_key: '0'.repeat(64) })
assert.ifError(missingKey.error)
assert.equal(missingKey.data, false)
Object.assign(process.env, { VIDEO_USAGE_BUDGET_ENABLED: 'true', VIDEO_USAGE_METER_KEY: key,
  VIDEO_STORAGE_READER_EMAIL: reader.email, VIDEO_STORAGE_READER_PASSWORD: password })
const attempts = await Promise.allSettled(Array.from({ length: 5 }, () =>
  videoBudgetCredential(uploader.client, url, anon, 'Bearer ' + uploader.token, 'media')))
const accepted = attempts.filter(result => result.status === 'fulfilled')
assert.equal(accepted.length, 2)
const response = await fetch(url + '/storage/v1/object/authenticated/post-videos/' + path, {
  headers: { apikey: anon, Authorization: accepted[0].value, Range: 'bytes=0-2' },
})
assert.ok(response.ok)
assert.ok((await response.arrayBuffer()).byteLength > 0)
sql("update video_private.usage_budget set reads_enabled=false", '-c')
assert.ok((await reader.client.storage.from('post-videos').download(path)).error)
const admin = createClient(url, env.SERVICE_ROLE_KEY, { auth: { persistSession: false, autoRefreshToken: false } })
assert.ifError((await admin.storage.createBucket('budget-qa-images', { public: true })).error)
assert.ifError((await admin.storage.from('budget-qa-images').upload('fixture.png', bytes,
  { contentType: 'image/png', upsert: false })).error)
const image = await fetch(url + '/storage/v1/object/public/budget-qa-images/fixture.png')
assert.equal(image.status, 200)
assert.deepEqual(Buffer.from(await image.arrayBuffer()), bytes)
const post = await uploader.client.from('posts').insert({
  user_id: uploader.id, content: 'ordinary SNS post with video stopped',
}).select('id').single()
assert.ifError(post.error)
assert.ok(post.data.id)
assert.equal(sql('select operations||\':\'||read_bytes||\':\'||delivery_bytes from video_private.usage_budget_month', '-Atc'), '2:41943040:41943040')
console.log('PASS: concurrent reservation and transfer limits, scoped Storage reader, signer denial and emergency stop')
