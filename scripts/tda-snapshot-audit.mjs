#!/usr/bin/env node
// Offline-only: read exact local snapshots, verify a separately supplied ledger,
// then apply existing structural audits. No network, DB or publication path.
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import {pathToFileURL} from 'node:url'
import {auditQuizAnswerKey} from '../src/tdaQuizAnswerAudit.ts'
import {parseUnambiguousJSON} from './strict-json.mjs'

const MAX_INPUT_BYTES = 5 * 1024 * 1024
const defaultIo = {readFile:file=>readFileSync(file),stdout:line=>console.log(line),stderr:line=>console.error(line)}
const hash = bytes=>createHash('sha256').update(bytes).digest('hex')
const plain = value=>typeof value==='object'&&value!==null&&!Array.isArray(value)
const positive = value=>typeof value==='number'&&Number.isSafeInteger(value)&&value>0
const digest = value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value)
const parse = parseUnambiguousJSON
class InputFailure extends Error { constructor(code){super(code);this.code=code} }

export function runQuizSnapshotAudit(args,io=defaultIo) {
  const fail=(reason,code=1)=>{io.stderr(JSON.stringify({verdict:'FAIL',reason,
    official_rule_accuracy:'UNVERIFIED',publication_approved:false}));return code}
  if(!Array.isArray(args)||args.length!==3||args.some(arg=>typeof arg!=='string'||!arg.trim()))return fail('INVALID_ARGUMENTS',2)
  const load=file=>{
    let bytes
    try{bytes=io.readFile(file)}catch{throw new InputFailure('INPUT_READ_FAILED')}
    if(!(bytes instanceof Uint8Array))throw new InputFailure('INPUT_NOT_BYTES')
    // Bounds the accepted buffer. readFile itself is caller/OS-controlled; this
    // is not a claim of a hard filesystem-read timeout or allocation bound.
    if(bytes.byteLength>MAX_INPUT_BYTES)throw new InputFailure('INPUT_TOO_LARGE')
    return Buffer.from(bytes)
  }
  try {
    const manifestBytes=load(args[2])
    let manifest
    try{manifest=parse(manifestBytes)}catch{return fail('INVALID_MANIFEST')}
    if(!plain(manifest)||manifest.version!==1||!digest(manifest.question_sha256)||!digest(manifest.answer_key_sha256)||
      !positive(manifest.expected_question_count)||!positive(manifest.expected_option_count))return fail('INVALID_MANIFEST')
    const questionBytes=load(args[0]),keyBytes=load(args[1])
    const questionHash=hash(questionBytes),keyHash=hash(keyBytes)
    if(questionHash!==manifest.question_sha256)return fail('QUESTION_HASH_MISMATCH')
    if(keyHash!==manifest.answer_key_sha256)return fail('ANSWER_KEY_HASH_MISMATCH')
    let questions,keys
    try{questions=parse(questionBytes);keys=parse(keyBytes)}catch{return fail('INVALID_SOURCE_JSON')}
    let report
    try{report=auditQuizAnswerKey(questions,keys)}catch{return fail('INVALID_QUESTION_DATA')}
    const countMatches={questions:report.question_count===manifest.expected_question_count,
      options:report.option_count===manifest.expected_option_count}
    const passes=report.verdict==='STRUCTURE_PASS'&&countMatches.questions&&countMatches.options
    io.stdout(JSON.stringify({...report,expected_question_count:manifest.expected_question_count,
      expected_option_count:manifest.expected_option_count,count_matches:countMatches,
      question_snapshot_sha256:questionHash,answer_key_snapshot_sha256:keyHash,manifest_sha256:hash(manifestBytes),
      snapshot_integrity:'HASH_MATCH_NOT_PROVENANCE',
      verdict:passes?'STRUCTURE_PASS':'REVIEW_REQUIRED',official_rule_accuracy:'UNVERIFIED',publication_approved:false},null,2))
    return passes?0:1
  }catch(error){return fail(error instanceof InputFailure?error.code:'AUDIT_FAILED')}
}

if(process.argv[1]&&pathToFileURL(process.argv[1]).href===import.meta.url)process.exitCode=runQuizSnapshotAudit(process.argv.slice(2))
