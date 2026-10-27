export const RECOVERY_REQUEST_TIMEOUT_MS=30000

/** Auth initialization can hang too. Bound the WHOLE request and release UI
 * locks on abort even if an SDK session Promise cannot itself be cancelled. */
export async function withVideoRecoveryDeadline<T>(external:AbortSignal|undefined,work:(signal:AbortSignal)=>Promise<T>):Promise<T> {
  const deadline=new AbortController()
  const signal=external?AbortSignal.any([external,deadline.signal]):deadline.signal
  const timer=setTimeout(()=>deadline.abort(),RECOVERY_REQUEST_TIMEOUT_MS)
  let onAbort:()=>void=()=>{}
  try {
    signal.throwIfAborted()
    const cancelled=new Promise<never>((_resolve,reject)=>{
      onAbort=()=>reject(new Error('動画の復旧通信を中断しました。安全のため停止しています。'))
      signal.addEventListener('abort',onAbort,{once:true})
    })
    return await Promise.race([work(signal),cancelled])
  } finally {
    clearTimeout(timer)
    signal.removeEventListener('abort',onAbort)
  }
}
