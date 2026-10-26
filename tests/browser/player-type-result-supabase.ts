import fixture from '../fixtures/player-type-v2.json'
// Synthetic transport only; no production SDK, accounts, keys or calls.
const mode=new URLSearchParams(window.location.search).get('mode')
const calls: {name:string,args:unknown}[]=[]
const pending: Record<string,(value:unknown)=>void>={}
let failures=0
Object.assign(window,{qaResultCalls:calls,qaResolve:(name:string,value:unknown)=>pending[name]?.(value)})
const wait=(name:string)=>new Promise(resolve=>{pending[name]=resolve})
const row=(id:string)=>({result_id:id,result_type_key:'lion',animal_name_ja:id==='qa-next'?'QA次ライオン':'QA元ライオン',catchphrase:'合成の表示確認',core_answer_count:50,description:'QA description',trait_scores:mode==='presentation-invalid'?{initiative:'99',confidence:true,attack_momentum:[99]}:mode==='presentation-negative'?{initiative:-1,confidence:0,attack_momentum:-3}:mode==='presentation-normalized'?{exploit:24,risk_tolerance:3,patience:23}:{},discriminator_scores:{},behavior_text:'QA',strength_text:'QA',weakness_text:'QA',perceived_text:'QA',best_situation_text:'QA'})
export const supabase={
 auth:{getUser:async()=>{calls.push({name:'getUser',args:null});if(mode==='auth-race'||mode==='unmount-auth')return await wait('auth');return {data:{user:{id:'qa-owner'}},error:null}}},
 rpc:async(name:string,args?:{p_result_id?:string,p_option_ids?:string[]})=>{
  calls.push({name,args})
  if(name==='get_player_type_v2_questions'){
   if(mode==='questions-error' && failures++===0)throw Error('qa-private-question-transport')
   return {data:fixture.rows,error:null}
  }
  if(name==='get_player_type_v2_result_detail'){
   if(mode==='result-race' && args?.p_result_id==='qa-result')return await wait('detail')
   if(mode==='detail-error' && failures++===0)throw Error('qa-private-result-transport')
   if(mode==='wrong-result')return {data:[row('qa-unrequested')],error:null}
   return {data:[row(args?.p_result_id || 'qa-result')],error:null}
  }
  if(name==='is_my_player_type_v2_result'){
   if(mode==='owner-race' && args?.p_result_id==='qa-result')return await wait('owner')
   return {data:!(mode==='owner-race' && args?.p_result_id==='qa-next'),error:null}
  }
  if(name==='complete_player_type_v2_diagnosis'){
   if(mode==='questions-save-error' && failures++===0)throw Error('qa-private-save-transport')
   return {data:[row('qa-saved')],error:null}
  }
  return {data:[],error:null}
 },
 from:(name:string)=>({insert:async(args:unknown)=>{
  calls.push({name:'insert:'+name,args})
  if(mode==='share-error' && failures++===0)return {error:{message:'qa-private-post-key'}}
  if(mode==='share-race'||mode==='double-share')return await wait('post')
  return {error:null}
 }}),
}
