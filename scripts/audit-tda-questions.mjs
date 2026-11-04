#!/usr/bin/env node
// Offline JSON export audit. Never accesses a DB or publishes questions.
import { runQuizAuditCli } from './tda-audit-cli.mjs'
process.exitCode = runQuizAuditCli(process.argv.slice(2))
