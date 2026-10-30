import test from 'node:test'
import assert from 'node:assert/strict'
import {assertCloudTestTarget,CLOUD_TEST_URL} from '../server/video-cloud-test-target.mjs'
const valid=()=>({VIDEO_CLOUD_TEST_ENABLED:'true',VERCEL_ENV:'preview',VIDEO_CLOUD_TEST_PROJECT_REF:'hbhyuotzginwysrineyo',VITE_SUPABASE_URL:CLOUD_TEST_URL,SUPABASE_URL:CLOUD_TEST_URL,VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID:'dedicated-test-project',VERCEL_PROJECT_ID:'dedicated-test-project'})
test('accepts only explicit dedicated Preview configuration',()=>{assert.equal(assertCloudTestTarget(valid()).url,CLOUD_TEST_URL)})
test('rejects missing configuration and production endpoint variants',()=>{
 for(const key of Object.keys(valid())){const e=valid();delete e[key];assert.throws(()=>assertCloudTestTarget(e))}
 for(const url of ['https://ephptepeuespnxtzdqby.supabase.co',CLOUD_TEST_URL+'/',CLOUD_TEST_URL+'.evil.invalid','http://127.0.0.1:56321']){
  assert.throws(()=>assertCloudTestTarget({...valid(),VITE_SUPABASE_URL:url}))
  assert.throws(()=>assertCloudTestTarget({...valid(),SUPABASE_URL:url}))
 }
})
test('rejects production deployment, project, release flags and privileged credentials',()=>{
 for(const patch of [{VERCEL_ENV:'production'},{VERCEL_PROJECT_ID:'prj_XfvN7NTO8lo6xXcjHZWGTUIp4VBI',VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID:'prj_XfvN7NTO8lo6xXcjHZWGTUIp4VBI'},{VIDEO_PRODUCTION_FENCED_READY:'true'},{VIDEO_ATTESTED_RPC_RELEASE_APPROVED:'true'},...['SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV'].map(k=>({[k]:'fixture-not-a-secret'}))]){
  assert.throws(()=>assertCloudTestTarget({...valid(),...patch}),/configuration rejected/)
 }
})
