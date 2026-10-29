// This journal is a stop/recovery hint, NEVER authorization to upload/finalize.
// Only this live module can recognize a confirmed reservation and upload ACK.
const prefix = 'poker-id-video-transfer-v1:'
export const VIDEO_TRANSFER_RECOVERY_MESSAGE = '前回の動画送信結果を確認できません。重複を防ぐため動画の再送信を停止しています。保存先・ファイル・予約・検証状態をサーバーで照合できるまで、自動再開はできません。'
export class VideoTransferRecoveryRequiredError extends Error {
  constructor() { super(VIDEO_TRANSFER_RECOVERY_MESSAGE) }
}
export type VideoTransferRecord = {
  owner: string; path: string; sha256: string; size: number; type: string
  startedAt: number; phase: 'reserving' | 'reserved' | 'uploading' | 'acknowledged'
}
const live = new Map<string, VideoTransferRecord>()
const key = (owner: string) => prefix + owner

function write(record: VideoTransferRecord) {
  try { sessionStorage.setItem(key(record.owner), JSON.stringify(record)) }
  catch { throw new VideoTransferRecoveryRequiredError() }
}

export function hasVideoTransferJournal(owner: string): boolean {
  try { return sessionStorage.getItem(key(owner)) !== null }
  catch { return true }
}

export function isVideoTransferBlocked(owner: string): boolean {
  try {
    const raw = sessionStorage.getItem(key(owner))
    if (raw === null) return false
    const current = live.get(owner)
    // Malformed, edited, stale or reloaded state only ever stops operations.
    return !current || raw !== JSON.stringify(current)
  } catch { return true }
}

export function beginVideoTransfer(record: VideoTransferRecord) {
  if (isVideoTransferBlocked(record.owner) || live.has(record.owner)) throw new VideoTransferRecoveryRequiredError()
  write(record) // Must succeed BEFORE any reservation request.
}

export function confirmVideoReservation(record: VideoTransferRecord) {
  record.phase = 'reserved'
  write(record)
  live.set(record.owner, record)
}

export function setVideoTransferPhase(record: VideoTransferRecord, phase: VideoTransferRecord['phase']) {
  if (isVideoTransferBlocked(record.owner) || live.get(record.owner) !== record) throw new VideoTransferRecoveryRequiredError()
  record.phase = phase
  write(record) // Must succeed BEFORE sending bytes / handing off to finalize.
}

/** Call only after persisting the existing immutable pending-finalize draft. */
export function handOffVideoTransfer(owner: string, path: string) {
  try {
    const raw = sessionStorage.getItem(key(owner))
    if (raw === null) return // Legacy acknowledged-upload recovery.
    const record = live.get(owner)
    if (!record || raw !== JSON.stringify(record) || record.path !== path || record.phase !== 'acknowledged') {
      throw new VideoTransferRecoveryRequiredError()
    }
    sessionStorage.removeItem(key(owner))
    live.delete(owner)
  } catch { throw new VideoTransferRecoveryRequiredError() }
}

/** Untrusted locator only. Server-owned manifest and bytes decide eligibility. */
export function readVideoTransferHint(owner:string) {
  const raw=sessionStorage.getItem(key(owner))
  if(raw===null||raw.length>4096) throw new VideoTransferRecoveryRequiredError()
  const hint=JSON.parse(raw)
  if(!hint||hint.owner!==owner||typeof hint.path!=='string'||
    !new RegExp('^'+owner+'/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\\.(mp4|webm|mov)$').test(hint.path)||
    typeof hint.sha256!=='string'||!/^[0-9a-f]{64}$/.test(hint.sha256)||
    !Number.isSafeInteger(hint.size)||hint.size<1||hint.size>20971520) throw new VideoTransferRecoveryRequiredError()
  return {path:hint.path as string,sha256:hint.sha256 as string,size:hint.size as number,raw}
}

/** Only after the server's recovered-publication response. Cannot authorize IO. */
export function finishRecoveredVideoTransfer(owner:string,path:string,expectedRaw?:string) {
  const raw=sessionStorage.getItem(key(owner))
  if(raw!==null) {
    if(raw!==expectedRaw||JSON.parse(raw).path!==path) throw new VideoTransferRecoveryRequiredError()
    sessionStorage.removeItem(key(owner))
  }
  live.delete(owner)
}

/** Explicit user action only, after a fresh authenticated server proof.
 * Never clears an in-flight transfer or a changed journal. */
export function discardProvenExpiredVideoTransfer(owner:string,path:string,expectedRaw:string): void {
  if (!isVideoTransferBlocked(owner)) throw new VideoTransferRecoveryRequiredError()
  try {
    const raw=sessionStorage.getItem(key(owner))
    if (raw===null || raw!==expectedRaw || JSON.parse(raw).path!==path) throw new VideoTransferRecoveryRequiredError()
    sessionStorage.removeItem(key(owner))
    live.delete(owner)
  } catch { throw new VideoTransferRecoveryRequiredError() }
}
