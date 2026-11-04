// Strict offline snapshot decoding. JSON.parse validates syntax; the second
// pass rejects ambiguity that JSON.parse silently normalizes. No raw text or
// member names are included in errors consumed by the public CLI boundary.
export function parseUnambiguousJSON(bytes) {
  const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes)
  const parsed=JSON.parse(text)
  let position=0
  const whitespace=()=>{while(/[ \t\r\n]/.test(text[position]??'!'))position++}
  const string=()=>{
    const start=position++
    while(position<text.length){
      if(text[position]==='\\'){position+=2;continue}
      if(text[position++]==='"')return JSON.parse(text.slice(start,position))
    }
    throw new Error('INVALID_JSON_STRING')
  }
  const value=depth=>{
    if(depth>128)throw new Error('JSON_DEPTH_LIMIT')
    whitespace()
    if(text[position]==='"'){string();return}
    if(text[position]==='{'){
      position++;whitespace();const keys=new Set()
      if(text[position]==='}'){position++;return}
      while(position<text.length){
        whitespace();const key=string()
        if(keys.has(key))throw new Error('AMBIGUOUS_JSON_OBJECT')
        keys.add(key);whitespace();position++;value(depth+1);whitespace()
        if(text[position++]==='}')return
      }
    }else if(text[position]==='['){
      position++;whitespace()
      if(text[position]===']'){position++;return}
      while(position<text.length){
        value(depth+1);whitespace();if(text[position++]===']')return
      }
    }else{
      const start=position
      while(position<text.length&&!/[\s,}\]]/.test(text[position]))position++
      const literal=text.slice(start,position)
      if(!['null','true','false'].includes(literal)&&!Number.isFinite(Number(literal)))throw new Error('NONFINITE_JSON_NUMBER')
    }
  }
  value(0)
  return parsed
}
