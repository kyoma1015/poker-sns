import test from 'node:test'
import assert from 'node:assert/strict'
import { loadShareImage, encodeSharePng } from '../src/playerTypeShareImage.ts'
async function environment(run) {
 const oldWindow=globalThis.window,oldImage=globalThis.Image
 const timers=new Map();let next=0
 const fixture={timers,image:null,mode:'pending'}
 globalThis.window={setTimeout(fn,ms){assert.equal(ms,15000);timers.set(++next,fn);return next},clearTimeout(id){timers.delete(id)}}
 globalThis.Image=class {constructor(){fixture.image=this}set src(value){this.value=value;if(fixture.mode==='sync'){assert.equal(typeof this.onload,'function');this.onload()}if(fixture.mode==='throw')throw Error('private-image-detail')}}
 try {await run(fixture)} finally {if(oldWindow===undefined)delete globalThis.window;else globalThis.window=oldWindow;if(oldImage===undefined)delete globalThis.Image;else globalThis.Image=oldImage}
}
test('image handlers exist before a synchronous load and timers are cleared',()=>environment(async f=>{f.mode='sync';const image=await loadShareImage('/animals/lion.png');assert.equal(image,f.image);assert.equal(f.timers.size,0);assert.equal(image.onload,null);assert.equal(image.onerror,null)}))
test('image errors clean callback references and deadline',()=>environment(async f=>{const pending=loadShareImage('/animals/lion.png');f.image.onerror();await assert.rejects(pending);assert.equal(f.image.onload,null);assert.equal(f.image.onerror,null);assert.equal(f.timers.size,0)}))
test('image timeout settles once and clears callbacks',()=>environment(async f=>{const pending=loadShareImage('/animals/lion.png');const late=f.image.onload;[...f.timers.values()][0]();late();await assert.rejects(pending,/タイムアウト/);assert.equal(f.image.onload,null);assert.equal(f.timers.size,0)}))
test('image src exceptions clean timer without disclosing raw failure',()=>environment(async f=>{f.mode='throw';await assert.rejects(loadShareImage('/animals/lion.png'),error=>!error.message.includes('private'));assert.equal(f.timers.size,0)}))
test('PNG null encoding and thrown encoding both clean deadlines',()=>environment(async f=>{await assert.rejects(encodeSharePng({toBlob:fn=>fn(null)}));await assert.rejects(encodeSharePng({toBlob(){throw Error('private')}}),error=>!error.message.includes('private'));assert.equal(f.timers.size,0)}))
test('PNG callback after deadline cannot turn the failed request into success',()=>environment(async f=>{let callback;const pending=encodeSharePng({toBlob(fn){callback=fn}});[...f.timers.values()][0]();callback(new Blob(['late']));await assert.rejects(pending);assert.equal(f.timers.size,0)}))
