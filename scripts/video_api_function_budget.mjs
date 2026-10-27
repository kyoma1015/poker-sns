import {readdirSync} from 'node:fs'
import {join,relative} from 'node:path'

// Conservative inventory of runtime sources in Vercel's auto-discovered api
// tree. Declaration files and Node24 QA aliases are not deployed functions.
const runtime=/\.(?:[cm]?[jt]s|[jt]sx|py|go|rb)$/i
export function listApiFunctionSources(root) {
 const result=[]
 function visit(directory) {
  for(const entry of readdirSync(directory,{withFileTypes:true})) {
   const path=join(directory,entry.name)
   if(entry.isSymbolicLink())continue
   if(entry.isDirectory())visit(path)
   else if(runtime.test(entry.name)&&!entry.name.endsWith('.d.ts')&&!entry.name.endsWith('.d.mts')&&!entry.name.endsWith('.d.cts'))result.push(relative(root,path))
  }
 }
 visit(root)
 return result.sort()
}
export function assertApiFunctionBudget(root,limit=12) {
 const entries=listApiFunctionSources(root)
 if(entries.length>limit)throw Error(`Hobby supports at most ${limit} API functions, found ${entries.length}`)
 return entries
}
