// Initial-release candidate only. This does not enable or deploy the existing application.
export const FIRST_RELEASE_ENABLED = false
export const CORE_ROUTES = [
 ['entry','^/$'],['login','^/login/?$'],['signup','^/signup/?$'],
 ['timeline','^/(?:home|timeline)/?$'],['post','^/post/[^/]+/?$'],
 ['dm','^/dm/?$'],['conversation','^/dm/[^/]+/?$'],
 ['notifications','^/notifications/?$'],['profile','^/profile/?$'],
 ['profileEdit','^/profile/edit/?$'],['search','^/search/?$'],
 ['player','^/player/[^/]+/?$'],['following','^/player/[^/]+/following/?$'],
 ['followers','^/player/[^/]+/followers/?$'],['settings','^/settings/?$'],
] as const
export function firstReleaseRoute(input: unknown): string | null {
 if (typeof input !== 'string' || !input.startsWith('/') || input.startsWith('//')) return null
 let path: string
 try { path = decodeURIComponent(input.split(/[?#]/)[0]) } catch { return null }
 if (path.includes('\\') || [...path].some(c=>c.charCodeAt(0)<32 || c.charCodeAt(0)===127) || path.includes('//') || path.split('/').some(s=>s==='.' || s==='..')) return null
 return CORE_ROUTES.find(([,pattern])=>new RegExp(pattern).test(path))?.[0] ?? null
}
export const REQUIRED_RELEASE_GATES = ['scope','legacy_ledger_preserved','deferred_ui','regression_build',
 'auth_sessions','owner_rls','storage','account_isolation','nested_and_api_deferral',
 'privacy','mobile_e2e','recovery_release_review'] as const
export function firstReleaseVerdict(doc: unknown) {
 if (!doc || typeof doc !== 'object') return {ready:false,blocked:[...REQUIRED_RELEASE_GATES]}
 const gates = (doc as {gates?:unknown}).gates
 if (!Array.isArray(gates)) return {ready:false,blocked:[...REQUIRED_RELEASE_GATES]}
 const valid = gates.length === REQUIRED_RELEASE_GATES.length &&
  gates.every(g=>g && typeof g==='object' && REQUIRED_RELEASE_GATES.includes(g.id) &&
   ['PASS','BLOCKED','UNKNOWN'].includes(g.status)) &&
  new Set(gates.map(g=>g.id)).size===gates.length
 const blocked = valid ? REQUIRED_RELEASE_GATES.filter(id=>{
  const gate=gates.find(g=>g.id===id)
  return gate.status!=='PASS' || !Array.isArray(gate.evidence) || gate.evidence.length===0 ||
   !gate.evidence.every((e:unknown)=>typeof e==='string' && e.trim().length>0)
 }) : [...REQUIRED_RELEASE_GATES]
 return {ready:valid && blocked.length===0,blocked}
}
