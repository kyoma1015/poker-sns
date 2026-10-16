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
export type CardAchievement = { id: string; source: string; title: string; rank: number | null; entryCount: number | null; year: string; venue: string | null; prizeAmount: number | null; prizeDescription: string | null }
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
  txt(ctx,p.display_name||'PLAYER',225,207,50,'#26303B',true,535)
  txt(ctx,'@'+p.poker_id,226,247,25,t.accent,false,535)
  txt(ctx,pokerExperience(p)+'  ·  '+(MAIN_PLAY_LABELS[p.main_play||'']||'—'),226,284,22,'#45505E',false,535)
  const meta:[string,string|undefined|null][]=[
    ['MAIN GAME',p.main_game],
    ['AREA',p.activity_areas?.join('・')],
    ['FREQUENCY',POKER_FREQUENCIES[p.poker_frequency||'']]
  ]
  meta.filter((item):item is [string,string]=>Boolean(item[1])).forEach(([label,value],i)=>{
    const yy=168+i*44
    txt(ctx,label,772,yy,15,t.accent,true)
    txt(ctx,value,772,yy+23,19,'#26303B',true,225)
  })
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
    const h=354
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
        const col=i%2,row=Math.floor(i/2),x=96+col*337,top=y+136+row*68
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
    // 4:5 card: the largest achievement section is 285px, ending above the fixed 1170px footer.
    const rows=Math.min(3,a.length-1)
    const h=120+rows*55
    if(y+h+12>1155)throw new Error('大会実績がカードのフッターに重なるため画像を生成できません')
    roundedRect(ctx,75,y,930,h,18,t.panel,t.line)

    const gold='#A37A39'
    const muted='#647080'
    const main=a[0]
    const prize=(item:CardAchievement)=>item.prizeAmount!=null&&item.prizeAmount>0
      ? '¥'+item.prizeAmount.toLocaleString('ja-JP')
      : (item.prizeDescription?.trim()||'')
    const detail=(item:CardAchievement)=>[item.year?item.year+'年':null,item.venue].filter(Boolean).join(' · ')
    const placement=(item:CardAchievement)=>item.entryCount!=null&&item.entryCount>0
      ? item.entryCount+'エントリー中'
      : ''

    // Featured result: distinct hierarchy (competition / placing / prize).
    txt(ctx,'✦ FEATURED ACHIEVEMENT',98,y+26,18,gold,true)
    txt(ctx,main.title,100,y+63,30,'#26303B',true,650)
    const mainDetail=[detail(main),placement(main)].filter(Boolean).join(' · ')
    if(mainDetail)txt(ctx,mainDetail,101,y+87,17,muted,false,645)
    ctx.textAlign='right'
    ctx.fillStyle=gold
    ctx.font=(main.rank===1?'700 39px':'700 32px')+' system-ui, sans-serif'
    ctx.fillText(rankLabel(main.rank),976,y+63,205)
    ctx.textAlign='left'
    const featuredPrize=prize(main)
    if(featuredPrize){
      txt(ctx,main.prizeAmount!=null&&main.prizeAmount>0?'プライズ相当額':'獲得内容',101,y+108,15,gold,true)
      txt(ctx,featuredPrize,261,y+109,21,gold,true,700)
    }

    a.slice(1,4).forEach((item,i)=>{
      const top=y+120+i*55
      ctx.fillStyle=t.line;ctx.fillRect(97,top,884,1)
      // Rank badge emphasizes tournament placing without competing with the featured result.
      roundedRect(ctx,100,top+8,70,40,9,'#EFE7D9')
      const rank=rankLabel(item.rank)
      ctx.textAlign='center'
      ctx.font='700 19px system-ui, sans-serif'
      ctx.fillStyle=gold
      ctx.fillText(rank,135,top+34,62)
      ctx.textAlign='left'
      txt(ctx,item.title,184,top+24,20,'#26303B',true,505)
      const notes=[detail(item),placement(item)].filter(Boolean).join(' · ')
      if(notes)txt(ctx,notes,184,top+44,15,muted,false,510)
      const value=prize(item)
      if(value){
        ctx.textAlign='right'
        ctx.fillStyle='#8B6B3D'
        ctx.font='700 19px system-ui, sans-serif'
        ctx.fillText(value,981,top+30,260)
        ctx.textAlign='left'
      }
    })
    y+=h+12
  }
  if(y>1155)throw new Error('大会実績の情報量がカードに収まりません')
  ctx.save();ctx.globalAlpha=0.065;ctx.textAlign='center';ctx.font='700 240px Georgia, serif';ctx.fillStyle=t.accent;ctx.fillText('♠',540,1020);ctx.restore()
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
