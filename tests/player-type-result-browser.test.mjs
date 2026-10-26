import test,{before,after} from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {createServer} from 'vite'
import {chromium} from 'playwright-core'
const root=fileURLToPath(new URL('../',import.meta.url));let server,browser,base
before(async()=>{
 server=await createServer({root,configFile:false,server:{host:'127.0.0.1',port:0},plugins:[{name:'d-result-transport',enforce:'pre',resolveId(source,importer){if(source==='./supabase'&&importer?.includes('/src/'))return path.join(root,'tests/browser/player-type-result-supabase.ts')},configureServer(s){s.middlewares.use('/__qa-d-result',(req,res)=>{res.setHeader('Content-Type','text/html');res.end('<div id="root"></div><script type="module" src="/tests/browser/player-type-result-entry.tsx"></script>')})}}],esbuild:{jsx:'automatic'}})
 await server.listen();base=`http://127.0.0.1:${server.httpServer.address().port}`
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']})
})
after(async()=>{await browser?.close();await server?.close()})
async function page(mode='normal',ready=true){const p=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});p.setDefaultTimeout(2000);await p.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());await p.goto(base+'/__qa-d-result?mode='+mode);if(ready)await p.getByRole('heading',{name:'QA元ライオン',exact:true}).waitFor();return p}
const routeIs=(p,expected)=>p.waitForFunction(expected=>document.querySelector('[data-testid=qa-route]')?.textContent===expected,expected,{timeout:2000})
const heading=p=>p.getByRole('heading',{name:'QA次ライオン',exact:true})
const next=p=>p.getByRole('button',{name:'QA次結果',exact:true}).click()
const calls=(p,name)=>p.evaluate(name=>window.qaResultCalls.filter(c=>c.name===name),name)
const resolve=(p,name,value)=>p.evaluate(({name,value})=>window.qaResolve(name,value),{name,value})
const mockRow=id=>({result_id:id,result_type_key:'lion',animal_name_ja:'QA元ライオン',catchphrase:'QA',core_answer_count:50,trait_scores:{},discriminator_scores:{}})
async function editor(p,text='保存前の文章'){await p.getByRole('button',{name:'Poker IDのタイムラインに投稿',exact:false}).click();await p.getByRole('textbox',{name:'診断結果の投稿文'}).fill(text)}
const submit=p=>p.getByRole('button',{name:'この内容で投稿する',exact:true})
test('late old result cannot replace the newer requested result',async()=>{const p=await page('result-race',false);try{await p.waitForFunction(()=>window.qaResultCalls.some(c=>c.name==='get_player_type_v2_result_detail'));await next(p);await heading(p).waitFor();await resolve(p,'detail',{data:[mockRow('qa-result')],error:null});await p.waitForTimeout(100);assert.equal(await heading(p).count(),1)}finally{await p.close()}})
test('late ownership cannot expose old result or owner actions on the newer nonowned result',async()=>{const p=await page('owner-race',false);try{await p.waitForFunction(()=>window.qaResultCalls.some(c=>c.name==='is_my_player_type_v2_result'));await next(p);await heading(p).waitFor();await resolve(p,'owner',{data:true,error:null});await p.waitForTimeout(100);assert.equal(await heading(p).count(),1);assert.equal(await p.getByRole('button',{name:'Poker IDのタイムラインに投稿',exact:false}).count(),0)}finally{await p.close()}})
test('failed result read is redacted and retry recovers the requested result',async()=>{const p=await page('detail-error',false);try{await p.getByRole('button',{name:'結果を再読み込み',exact:true}).waitFor();assert.doesNotMatch(await p.locator('body').innerText(),/qa-private/);await p.getByRole('button',{name:'結果を再読み込み',exact:true}).click();await p.getByRole('heading',{name:'QA元ライオン',exact:true}).waitFor()}finally{await p.close()}})
test('mismatched result identity is refused without rendering its data',async()=>{const p=await page('wrong-result',false);try{await p.getByRole('button',{name:'結果を再読み込み',exact:true}).waitFor();assert.equal(await p.getByRole('heading',{name:'QA元ライオン',exact:true}).count(),0)}finally{await p.close()}})
test('post error is redacted, keeps the draft and permits retry',async()=>{const p=await page('share-error');try{await editor(p);await submit(p).click();await p.getByText('投稿に失敗しました。通信状況を確認して、もう一度お試しください。',{exact:true}).waitFor();assert.doesNotMatch(await p.locator('body').innerText(),/qa-private/);assert.equal(await p.getByRole('textbox',{name:'診断結果の投稿文'}).inputValue(),'保存前の文章');await submit(p).click();await p.getByText('タイムラインに投稿しました。',{exact:true}).waitFor();assert.equal((await calls(p,'insert:posts')).length,2)}finally{await p.close()}})
test('result navigation before authentication completes refuses the old post write',async()=>{const p=await page('auth-race');try{await editor(p);await submit(p).click();await next(p);await heading(p).waitFor();await resolve(p,'auth',{data:{user:{id:'qa-owner'}},error:null});await p.waitForTimeout(100);assert.deepEqual(await calls(p,'insert:posts'),[])}finally{await p.close()}})
test('unmount before authentication completes refuses the old post write',async()=>{const p=await page('unmount-auth');try{await editor(p);await submit(p).click();await p.getByRole('button',{name:'QAアンマウント',exact:true}).click();await resolve(p,'auth',{data:{user:{id:'qa-owner'}},error:null});await p.waitForTimeout(100);assert.deepEqual(await calls(p,'insert:posts'),[])}finally{await p.close()}})
test('late post completion cannot close the newer result draft',async()=>{const p=await page('share-race');try{await editor(p);await submit(p).click();await next(p);await heading(p).waitFor();await editor(p,'次の結果の文章');await resolve(p,'post',{error:null});await p.waitForTimeout(100);assert.equal(await p.getByRole('textbox',{name:'診断結果の投稿文'}).inputValue(),'次の結果の文章');assert.equal(await p.getByText('タイムラインに投稿しました。',{exact:true}).count(),0)}finally{await p.close()}})
test('same-tick duplicate share activation creates one write',async()=>{const p=await page('double-share');try{await editor(p);await submit(p).evaluate(button=>{button.click();button.click()});await p.waitForFunction(()=>window.qaResultCalls.some(c=>c.name==='insert:posts'));assert.equal((await calls(p,'insert:posts')).length,1)}finally{await p.close()}})
test('restart clears the saved-result URL while opening question one',async()=>{const p=await page();try{await p.getByRole('button',{name:'もう一度診断する',exact:false}).click();await p.getByText('QUESTION 1',{exact:true}).waitFor();await routeIs(p,'/player-type');assert.equal(await p.getByTestId('qa-route').innerText(),'/player-type')}finally{await p.close()}})
test('question transport failure has safe retry and recovers all50 questions',async()=>{const p=await page('questions-error',false);try{await p.getByRole('button',{name:'質問を再読み込み',exact:true}).waitFor();assert.doesNotMatch(await p.locator('body').innerText(),/qa-private/);await p.getByRole('button',{name:'質問を再読み込み',exact:true}).click();await p.getByRole('button',{name:'診断をはじめる',exact:true}).click();await p.getByText('QUESTION 1',{exact:true}).waitFor()}finally{await p.close()}})
test('final answer transport failure retries exactly50 answers and persists the new result URL',async()=>{
 const p=await page('questions-save-error',false);try{
  await p.getByRole('button',{name:'診断をはじめる',exact:true}).click()
  for(let i=1;i<50;i++){await p.getByText('QUESTION '+i,{exact:true}).waitFor();await p.locator('.ptd-option').first().click()}
  await p.getByText('QUESTION 50',{exact:true}).waitFor();await p.locator('.ptd-option').first().click()
  await p.getByText('結果を保存できませんでした。通信状況を確認して、最後の回答をもう一度選んでください。',{exact:true}).waitFor()
  assert.doesNotMatch(await p.locator('body').innerText(),/qa-private/)
  await p.locator('.ptd-option').first().click();await p.getByRole('heading',{name:'QA元ライオン',exact:true}).waitFor()
  const saves=await calls(p,'complete_player_type_v2_diagnosis');assert.equal(saves.length,2);assert.deepEqual(saves[0].args.p_option_ids,saves[1].args.p_option_ids);assert.equal(saves[1].args.p_option_ids.length,50);assert.equal(new Set(saves[1].args.p_option_ids).size,50)
  await routeIs(p,'/player-type?result=qa-saved');assert.equal(await p.getByTestId('qa-route').innerText(),'/player-type?result=qa-saved')
 }finally{await p.close()}
})

for(const mode of ['presentation-invalid','presentation-negative'])test(`${mode} does not invent positive traits from malformed or nonpositive scores`,async()=>{const p=await page(mode);try{assert.equal(await p.getByRole('heading',{name:'特に強く出ている3つの傾向',exact:true}).count(),0);assert.doesNotMatch(await p.locator('.ptd-advice-card').innerText(),/自分から動ける強み|攻めを継続できるのが武器/)}finally{await p.close()}})
test('presentation-normalized ranks actual result traits by the existing per-axis ceilings',async()=>{const p=await page('presentation-normalized');try{assert.deepEqual(await p.locator('.ptd-trait strong').allTextContents(),['待てる','リスクを取れる','弱点を利益に変える'])}finally{await p.close()}})

for(const id of ['qa-other',null])test(`account transition ${id??'signout'} clears the loaded result and draft synchronously`,async()=>{const p=await page();try{await editor(p,'QA元の非公開下書き');await p.evaluate(id=>window.qaAuthChange(id),id);await p.getByRole('button',{name:'診断をはじめる',exact:true}).waitFor();assert.equal(await p.getByRole('heading',{name:'QA元ライオン',exact:true}).count(),0);assert.equal(await p.getByRole('textbox',{name:'診断結果の投稿文'}).count(),0);await routeIs(p,'/player-type');assert.equal(await p.getByTestId('qa-route').innerText(),'/player-type')}finally{await p.close()}})
test('account transition during pending share authentication refuses the old write',async()=>{const p=await page('auth-switch-pending');try{await editor(p);await submit(p).click();await p.evaluate(()=>window.qaAuthChange('qa-other'));await resolve(p,'auth',{data:{user:{id:'qa-other'}},error:null});await p.waitForTimeout(100);assert.deepEqual(await calls(p,'insert:posts'),[]);assert.equal(await p.getByRole('heading',{name:'QA元ライオン',exact:true}).count(),0)}finally{await p.close()}})
test('anonymous public-result viewing remains available without owner actions',async()=>{const p=await page('anonymous');try{assert.equal(await p.getByRole('button',{name:'Poker IDのタイムラインに投稿',exact:false}).count(),0)}finally{await p.close()}})
