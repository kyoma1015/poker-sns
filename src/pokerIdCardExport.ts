import { qrcode } from './qrGenerator'
import { pokerExperience, MAIN_PLAY_LABELS, POKER_FREQUENCIES } from './PokerProfileExtras'

export type CardProfile = {
  poker_id: string; display_name: string; avatar_url?: string | null
  poker_started_year?: number | null; poker_started_month?: number | null; poker_years?: number | null
  main_game?: string | null; main_play?: string | null; poker_frequency?: string | null
  hobbies?: string[] | null; poker_meaning?: string | null; poker_meaning_detail?: string | null; my_hand_cards?: string[] | null; my_hand_reason?: string | null
  activity_areas?: string[] | null
}
export type CardAnimal = { result_type_key: string; animal_name_ja: string; catchphrase: string }
export type CardDiagnosis = { description: string; behavior_text: string; strength_text: string; weakness_text: string; perceived_text: string; best_situation_text: string }
export type CardAchievement = { id: string; source: string; title: string; rank: number | null; year: string }
export type CardTheme = { bg: string; panel: string; line: string; accent: string }

export function profileCardUrl(userId: string) {
  return new URL('/player/' + encodeURIComponent(userId), window.location.origin).toString()
}
export function createQrSvgData(url: string): { size: number; dark: { x: number; y: number }[] } {
  const qr = qrcode(0, 'M')
  qr.addData(url)
  qr.make()
  const dark: { x: number; y: number }[] = []
  for (let y = 0; y < qr.getModuleCount(); y++) for (let x = 0; x < qr.getModuleCount(); x++)
    if (qr.isDark(y,x)) dark.push({x,y})
  return { size: qr.getModuleCount(), dark }
}
function roundedRect(ctx: CanvasRenderingContext2D, x:number,y:number,w:number,h:number,r:number,fill:string,stroke?:string) {
  ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fillStyle=fill;ctx.fill()
  if(stroke){ctx.lineWidth=2;ctx.strokeStyle=stroke;ctx.stroke()}
}
function txt(ctx: CanvasRenderingContext2D,text:string,x:number,y:number,size:number,color:string,bold=false,maxWidth?:number) {
  ctx.fillStyle=color;ctx.font=`${bold?'700':'400'} ${size}px system-ui, sans-serif`;ctx.textAlign='left'
  if(maxWidth)ctx.fillText(text,x,y,maxWidth);else ctx.fillText(text,x,y)
}
function wrap(ctx: CanvasRenderingContext2D,value:string,x:number,y:number,width:number,size:number,color:string,maxLines=2,lineHeight=size*1.35) {
  ctx.font=`700 ${size}px system-ui,sans-serif`
  const chars=Array.from(value), lines:string[]=[]
  let line=''
  for(const c of chars){if(ctx.measureText(line+c).width>width&&line){lines.push(line);line=c}else line+=c}
  if(line)lines.push(line)
  const actual=lines.slice(0,maxLines)
  actual.forEach((v,i)=>txt(ctx,i===maxLines-1&&lines.length>maxLines?v.slice(0,-1)+'…':v,x,y+i*lineHeight,size,color,true,width))
  return actual.length*lineHeight
}
async function drawImageUrl(ctx:CanvasRenderingContext2D,url:string,x:number,y:number,w:number,h:number,mode:'cover'|'contain') {
  const image = new Image()
  image.crossOrigin='anonymous'
  image.src=url
  try { await new Promise<void>((ok,fail)=>{image.onload=()=>ok();image.onerror=()=>fail(new Error('image'))})
    const ratio=mode==='cover'?Math.max(w/image.width,h/image.height):Math.min(w/image.width,h/image.height)
    const nw=image.width*ratio,nh=image.height*ratio
    ctx.drawImage(image,x+(w-nw)/2,y+(h-nh)/2,nw,nh)
  } catch { /* Cross-origin avatars may not allow canvas export. Omit them safely. */ }
}
function rankLabel(rank:number|null) {return rank==null?'順位未登録':rank===1?'優勝':rank+'位'}
function drawQr(ctx:CanvasRenderingContext2D,url:string,x:number,y:number,size:number) {
  const qr=createQrSvgData(url), quiet=4
  roundedRect(ctx,x,y,size,size,9,'#FFFFFF')
  const module=size/(qr.size+quiet*2)
  ctx.fillStyle='#111111'
  for(const m of qr.dark)ctx.fillRect(x+(m.x+quiet)*module,y+(m.y+quiet)*module,Math.ceil(module+.1),Math.ceil(module+.1))
}
export async function renderPokerIdCard(data:{
  profile:CardProfile; animal:CardAnimal|null; diagnosisDetail:CardDiagnosis|null; achievements:CardAchievement[];
  theme:CardTheme; userId:string
}):Promise<Blob>{
  const {profile:p,animal,diagnosisDetail,achievements:a,theme:t,userId}=data
  const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1350
  const ctx=canvas.getContext('2d')
  if(!ctx)throw new Error('このブラウザでは画像を作成できません')
  ctx.fillStyle=t.bg;ctx.fillRect(0,0,1080,1350)
  ctx.strokeStyle=t.line;ctx.lineWidth=3;ctx.strokeRect(35,35,1010,1280)
  txt(ctx,'♠ POKER ID',76,111,44,'#26303B',true)
  txt(ctx,'PLAYER PROFILE',769,107,22,t.accent,true)
  ctx.fillStyle=t.line;ctx.fillRect(76,132,928,2)
  if(p.avatar_url)await drawImageUrl(ctx,p.avatar_url,80,158,120,120,'cover')
  else {roundedRect(ctx,80,158,120,120,60,t.line);txt(ctx,'♠',117,236,72,'#26303B')}
  txt(ctx,p.display_name||'PLAYER',225,207,50,'#26303B',true,760)
  txt(ctx,'@'+p.poker_id,226,247,25,t.accent,false,710)
  txt(ctx,pokerExperience(p)+'  ·  '+(MAIN_PLAY_LABELS[p.main_play||'']||'—'),226,284,22,'#45505E',false,700)
  let y=309
  if(p.poker_meaning?.trim()){
    const h=p.poker_meaning_detail?.trim()?149:103
    roundedRect(ctx,75,y,930,h,18,t.panel)
    txt(ctx,'WHAT IS POKER TO YOU?',98,y+29,17,t.accent,true)
    wrap(ctx,'「'+p.poker_meaning+'」',98,y+68,870,27,'#26303B',1)
    if(p.poker_meaning_detail?.trim()){
      ctx.fillStyle=t.line;ctx.fillRect(100,y+83,880,1)
      wrap(ctx,p.poker_meaning_detail,101,y+107,868,18,'#596370',2,22)
    }
    y+=h+15
  }
  if(animal || p.my_hand_cards?.length===2) {
    const h=353
    if(animal){
      roundedRect(ctx,75,y,691,h,16,t.panel)
      txt(ctx,'PLAYER TYPE',95,y+28,18,t.accent,true)
      await drawImageUrl(ctx,'/animals/'+animal.result_type_key+'.png',97,y+41,95,85,'contain')
      txt(ctx,animal.animal_name_ja,200,y+80,28,'#26303B',true,530)
      wrap(ctx,animal.catchphrase,200,y+109,535,17,'#596370',1)
      const entries:[string,string][] = diagnosisDetail ? [
        ['全体像',diagnosisDetail.description],['行動傾向',diagnosisDetail.behavior_text],
        ['強み',diagnosisDetail.strength_text],['弱み・注意点',diagnosisDetail.weakness_text],
        ['周囲からの印象',diagnosisDetail.perceived_text],['得意な状況',diagnosisDetail.best_situation_text],
      ] : []
      for(let i=0;i<entries.length;i++){
        const col=i%2,row=Math.floor(i/2),x=96+col*337,top=y+139+row*69
        ctx.fillStyle=t.line;ctx.fillRect(x,top-10,313,1)
        txt(ctx,entries[i][0],x,top+10,16,t.accent,true)
        wrap(ctx,entries[i][1],x,top+33,311,15,'#35404D',2,19)
      }
    }
    if(p.my_hand_cards?.length===2){
      roundedRect(ctx,778,y,227,h,16,t.panel)
      txt(ctx,'MY HAND',791,y+28,18,t.accent,true)
      p.my_hand_cards.forEach((card,i)=>{
        const suit=card.slice(-1),rank=card.slice(0,-1)
        const color=({'♠':'#222936','♥':'#dc354c','♦':'#2675d9','♣':'#15955c'} as Record<string,string>)[suit]||'#222936'
        const x=790+i*102,top=y+42
        roundedRect(ctx,x,top,92,120,12,'#FFFFFF','#D8DCE4')
        txt(ctx,rank,x+10,top+36,35,color,true)
        txt(ctx,suit,x+18,top+97,55,color,true)
      })
      if(p.my_hand_reason?.trim()){
        ctx.fillStyle=t.line;ctx.fillRect(795,y+181,195,1)
        wrap(ctx,p.my_hand_reason,796,y+208,189,17,'#45505E',7,19)
      }
    }
    y+=h+17
  }
  if(a.length){
    const rows=Math.min(3,a.length-1),h=104+rows*39
    roundedRect(ctx,75,y,930,h,17,t.panel,t.line)
    txt(ctx,'★ MAIN ACHIEVEMENT',98,y+29,19,'#96723F',true)
    wrap(ctx,a[0].title,98,y+69,745,26,'#26303B',1)
    txt(ctx,rankLabel(a[0].rank),853,y+69,29,'#96723F',true,135)
    a.slice(1,4).forEach((item,i)=>{
      const ry=y+110+i*39;ctx.fillStyle=t.line;ctx.fillRect(100,ry-19,880,1)
      txt(ctx,item.title,105,ry+7,20,'#35404D',false,690)
      txt(ctx,rankLabel(item.rank),859,ry+7,20,'#96723F',true,120)
    })
    y+=h+19
  }
  const stats:[string,string|undefined|null][]=[
    ['MAIN GAME',p.main_game],['FREQUENCY',POKER_FREQUENCIES[p.poker_frequency||'']],
    ['AREA',p.activity_areas?.join('・')],['HOBBIES',p.hobbies?.join('・')]
  ]
  const present=stats.filter((x):x is [string,string]=>!!x[1])
  const rowHeight=45
  for(let i=0;i<present.length;i++){
    const col=i%2,row=Math.floor(i/2),x=86+col*472,top=y+row*rowHeight
    txt(ctx,present[i][0],x,top+13,14,t.accent,true)
    txt(ctx,present[i][1],x,top+36,19,'#26303B',true,425)
  }
  const footerTop=Math.max(y+Math.ceil(present.length/2)*rowHeight+15,1080)
  if(footerTop>1175)throw new Error('カードの情報量が多く、1枚に収まりません。実績名などを短くして再試行してください。')
  ctx.save();ctx.globalAlpha=0.07;txt(ctx,'♠',470,1085,260,t.accent,true);ctx.restore()
  ctx.fillStyle=t.line;ctx.fillRect(80,1170,920,2)
  txt(ctx,'♠ POKER ID',85,1247,44,t.accent,true)
  txt(ctx,'CREATE YOUR OWN POKER ID',87,1281,18,t.accent)
  drawQr(ctx,profileCardUrl(userId),853,1185,120)
  return await new Promise<Blob>((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('PNGを生成できませんでした')),'image/png'))
}
export function savePokerIdImage(blob:Blob, name:string) {
  const url=URL.createObjectURL(blob),link=document.createElement('a')
  link.href=url;link.download=`PokerID_${name.replace(/[^a-zA-Z0-9_-]/g,'_')}.png`
  document.body.appendChild(link);link.click();link.remove()
  window.setTimeout(()=>URL.revokeObjectURL(url),30000)
}
