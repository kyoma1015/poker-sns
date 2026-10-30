import test from 'node:test'
import assert from 'node:assert/strict'
import { assertProductionVideoPublisher, assertProductionVideoMember } from '../../server/video-production-rollout.mjs'
const owner = '11111111-1111-4111-8111-111111111111'
const keys = ['VIDEO_PRODUCTION_LIMITED_ROLLOUT','VITE_SUPABASE_URL','VIDEO_SERVER_ENABLED','VIDEO_ALLOWED_USER_IDS','VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED','VIDEO_PUBLIC_ROLLOUT_ENABLED']
test('production gate requires pinned target, explicit flags, server allowlist and DB authorization', async () => {
  const saved = keys.map(key=>process.env[key])
  try {
    const reset = () => Object.assign(process.env, {VIDEO_PRODUCTION_LIMITED_ROLLOUT:'true',VITE_SUPABASE_URL:'https://ephptepeuespnxtzdqby.supabase.co',VIDEO_SERVER_ENABLED:'true',VIDEO_ALLOWED_USER_IDS:owner})
    let calls=0
    const viewer={rpc:async name=>{calls++;assert.equal(name,'video_rollout_allowed');return {data:true,error:null}}}
    reset(); await assertProductionVideoPublisher(viewer,owner); assert.equal(calls,1)
    for (const [key,value] of [['VITE_SUPABASE_URL','https://hbhyuotzginwysrineyo.supabase.co'],['VIDEO_SERVER_ENABLED','false'],['VIDEO_PRODUCTION_LIMITED_ROLLOUT','false'],['VIDEO_ALLOWED_USER_IDS','']]) {
      reset(); process.env[key]=value; const before=calls
      await assert.rejects(assertProductionVideoPublisher(viewer,owner)); assert.equal(calls,before)
    }
    reset(); await assert.rejects(assertProductionVideoPublisher(viewer,'33333333-3333-4333-8333-333333333333'))
    reset(); await assert.rejects(assertProductionVideoPublisher({rpc:async()=>({data:false,error:null})},owner))
    reset(); await assert.rejects(assertProductionVideoPublisher({rpc:async()=>({data:true,error:{}})},owner))
    reset(); process.env.VIDEO_SERVER_ENABLED='false'
    await assertProductionVideoMember({rpc:async name=>{assert.equal(name,'video_rollout_member');return {data:true,error:null}}},owner)
    await assert.rejects(assertProductionVideoMember({rpc:async()=>({data:false,error:null})},owner))
  } finally {keys.forEach((key,i)=>saved[i]===undefined?delete process.env[key]:process.env[key]=saved[i])}
})

test('public release requires both independent flags AND a positive database JWT decision', async () => {
  const saved = keys.map(key=>process.env[key])
  const other = '33333333-3333-4333-8333-333333333333'
  let calls = 0
  const viewer = {rpc:async rpc=>{calls++;assert.equal(rpc,'video_rollout_allowed');return {data:true,error:null}}}
  try {
    Object.assign(process.env,{
      VIDEO_PRODUCTION_LIMITED_ROLLOUT:'true',
      VITE_SUPABASE_URL:'https://ephptepeuespnxtzdqby.supabase.co',
      VIDEO_SERVER_ENABLED:'true',
      VIDEO_ALLOWED_USER_IDS:owner,
      VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED:'false',
      VIDEO_PUBLIC_ROLLOUT_ENABLED:'false',
    })
    await assert.rejects(assertProductionVideoPublisher(viewer,other))
    assert.equal(calls,0)
    process.env.VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED='true'
    await assert.rejects(assertProductionVideoPublisher(viewer,other))
    assert.equal(calls,0)
    process.env.VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED='false'
    process.env.VIDEO_PUBLIC_ROLLOUT_ENABLED='true'
    await assert.rejects(assertProductionVideoPublisher(viewer,other))
    assert.equal(calls,0)
    process.env.VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED='true'
    await assertProductionVideoPublisher(viewer,other)
    assert.equal(calls,1)
    await assert.rejects(assertProductionVideoPublisher({rpc:async()=>({data:false,error:null})},other))
    await assert.rejects(assertProductionVideoPublisher({rpc:async()=>({data:null,error:{}})},other))
    process.env.VIDEO_SERVER_ENABLED='false'
    await assert.rejects(assertProductionVideoPublisher(viewer,other))
    process.env.VIDEO_SERVER_ENABLED='true'
    process.env.VITE_SUPABASE_URL='https://untrusted.supabase.co'
    await assert.rejects(assertProductionVideoPublisher(viewer,other))
    process.env.VITE_SUPABASE_URL='https://ephptepeuespnxtzdqby.supabase.co'
    await assert.rejects(assertProductionVideoPublisher(viewer,'invalid-user'))
  } finally {keys.forEach((key,i)=>saved[i]===undefined?delete process.env[key]:process.env[key]=saved[i])}
})
