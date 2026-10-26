// In-memory test transport only, external requests aborted by the browser harness.
const qa = {
 userId:'me' as string|null, authError:false, holdProfile:false, holdRead:false, failRead:false, failMark:false, zeroMark:false,
 pendingProfiles:[] as Array<(x:any)=>void>, pendingReads:[] as Array<(x:any)=>void>, updates:[] as any[], reads:0,
 listeners:new Set<any>(), channels:[] as any[], insideAuth:false, reentrant:0, outsider:false, actor:'PRIVATE_ACTOR_A',
 emit(id:string|null) { this.userId=id;this.insideAuth=true;try{this.listeners.forEach(fn=>fn(id?'SIGNED_IN':'SIGNED_OUT',id?{user:{id}}:null))}finally{this.insideAuth=false} },
 realtime(){this.channels.filter(c=>c.active).forEach(c=>c.handler({new:{}}))},
 rows(id=this.userId){return [{id:'n-'+id,user_id:id,actor_id:'actor',type:'like',post_id:'post',read_at:null,created_at:'2026-10-26T00:00:00Z'},...(this.outsider?[{id:'outsider',user_id:'stranger',actor_id:'outsider',type:'comment',post_id:'foreign',read_at:null,created_at:'2026-10-26T00:00:00Z'}]:[])]},
 releaseProfile(){this.holdProfile=false;this.pendingProfiles.splice(0).forEach(done=>done({data:[{id:'actor',display_name:'LATE_OLD_ACTOR',poker_id:'synthetic'}],error:null}))},
 releaseRead(){this.holdRead=false;this.pendingReads.splice(0).forEach(done=>done({data:this.rows('me'),error:null}))},
}
;(window as any).notificationQA=qa
function query(table:string){let writing=false;let ids:string[]=[];const filters:any={};const c:any={
 select(){return c},eq(k:string,v:string){filters[k]=v;return c},is(k:string,v:any){filters[k]=v;return c},or(){return c},in(k:string,v:string[]){if(k==='id')ids=v;return c},
 update(value:any){writing=true;qa.updates.push({value,filters,ids:()=>ids});return c},
 order(){qa.reads++;if(qa.failRead){qa.failRead=false;return Promise.reject(new Error('SYNTHETIC_PRIVATE_DB'))}if(qa.holdRead)return new Promise(done=>qa.pendingReads.push(done));return Promise.resolve({data:qa.rows(),error:null})},
 then(resolve:any,reject:any){let r:any;if(writing)r=Promise.resolve({data:qa.zeroMark?[]:ids.map(id=>({id,read_at:'synthetic-read-time'})),error:qa.failMark?{message:'SYNTHETIC_PRIVATE_UPDATE'}:null});else if(table==='profiles')r=qa.holdProfile?new Promise(done=>qa.pendingProfiles.push(done)):Promise.resolve({data:[{id:'actor',display_name:qa.userId==='newme'?'PRIVATE_ACTOR_B':qa.actor,poker_id:'synthetic'},{id:'outsider',display_name:'OUTSIDER_PRIVATE',poker_id:'foreign'}],error:null});else r=Promise.resolve({data:[],error:null});return r.then(resolve,reject)},
};return c}
export const supabase={auth:{async getUser(){if(qa.insideAuth)qa.reentrant++;return {data:{user:qa.userId?{id:qa.userId}:null},error:qa.authError?{message:'SYNTHETIC_PRIVATE_AUTH'}:null}},onAuthStateChange(fn:any){qa.listeners.add(fn);queueMicrotask(()=>{if(qa.listeners.has(fn))fn('INITIAL_SESSION',qa.userId?{user:{id:qa.userId}}:null)});return {data:{subscription:{unsubscribe(){qa.listeners.delete(fn)}}}}}},from:query,
 channel(){const c:any={active:true,handler:()=>{},on(_a:any,filter:any,handler:any){c.filter=filter;c.handler=handler;return c},subscribe(){qa.channels.push(c);return c}};return c},removeChannel(c:any){c.active=false}}
