"""Opt-in adapter for an already-prepared host task; no agent/scheduler backend.

Callbacks are trusted coordinator functions. This module does not connect to a
formal host, grant authority, acquire jobs, or preempt blocking host callbacks.
"""
import json
from pathlib import Path
import time

import code_worker as worker
from invocation_guard import InvocationGuard


def _prepared(guard, state, task_id, token, now):
    if Path(guard.controller.path).resolve() != Path(state).resolve():
        raise ValueError('guard and prepared task must share the exact state')
    db = guard.controller.db
    row = db.execute("SELECT evidence,spec_hash FROM development_jobs WHERE id=? AND token=? AND status='running' AND expires>?", (task_id, token, now)).fetchone()
    if row is None or worker.bound_evidence_spec(row[0], row[1], task_id) is None:
        raise worker.LeaseActivationRefused('prepared identity, ownership or liveness requires review')
    context = json.loads(row[0])
    if context.get('prepared_for') != 'host_session':
        raise ValueError('existing prepared host context required')
    worktree = Path(context['worktree'])
    if worktree.name != task_id or not worktree.is_dir() or worktree.is_symlink():
        raise ValueError('retained prepared worktree required')
    if worker.command(['git','rev-parse','HEAD'],worktree) != context['base_sha']:
        raise ValueError('prepared base changed; review required')
    if worker.protected_hashes(worktree,context['task']['protected_tests']) != context['before']:
        raise ValueError('prepared acceptance changed; review required')
    return row[0], row[1], context


def _retain_unknown(guard, task_id, token, original, spec, context):
    kept = dict(context)
    kept['worker_liveness_unknown'] = True
    # Conditional evidence update only: never reset expiry/attempts/token or
    # overwrite a changed owner's context. The original worktree is preserved.
    cursor = guard.controller.db.execute("UPDATE development_jobs SET evidence=? WHERE id=? AND token=? AND spec_hash=? AND evidence=? AND status='running'",
        (json.dumps(kept),task_id,token,spec,original))
    if cursor.rowcount != 1:
        raise worker.WorkerLivenessUnknown('unknown context changed; manual reconciliation required')


def complete_prepared(guard, state, task_id, token, *, dispatch, observe, preserve,
                      enabled=False, now=None):
    """Validate retained state, bracket a trusted call and finish only if safe.

    This consumes no new run/task: the caller enters InvocationGuard, prepares a
    reviewed task and supplies identity-scoped liveness/private persistence. It
    still owns actual cancellation, callback time bounds, auth and fresh PR gates.
    A known stopped interruption may use existing defer_host/resume_host after
    positive coordinator confirmation. UNKNOWN is retained for manual review.
    No private token/receipt is logged or returned by this adapter itself.
    """
    if enabled is not True or not isinstance(guard, InvocationGuard):
        raise ValueError('prepared boundary requires explicit trusted opt-in')
    if not all(callable(x) for x in (dispatch,observe,preserve)):
        raise ValueError('trusted coordinator callbacks required')
    guard.check()
    current = worker.finite_lease_number(time.time() if now is None else now,'prepared clock')
    original, spec, context = _prepared(guard,state,task_id,token,current)
    guard.check()
    def checked_dispatch():
        # observe() may block/change context; never dispatch on its earlier read.
        latest = worker.finite_lease_number(time.time() if now is None else now,'dispatch clock')
        raw, latest_spec, _ = _prepared(guard,state,task_id,token,latest)
        if raw != original or latest_spec != spec:
            raise worker.LeaseActivationRefused('prepared context changed before dispatch')
        guard.check()
        return dispatch()

    def finish_stop_check():
        try:
            guard.check()
        except BaseException as error:
            error.host_boundary_stopped = True
            raise

    try:
        receipt = guard.call_host(checked_dispatch,observe=observe,preserve=preserve)
        guard.check()
        return worker.finish_host_session(state,task_id,token,receipt,now=now,stop_check=finish_stop_check)
    except BaseException as error:
        if getattr(error,'worker_liveness_unknown',False):
            try:
                _retain_unknown(guard,task_id,token,original,spec,context)
            except BaseException:
                error.add_note('Unable to retain UNKNOWN context; no automatic continuation')
        raise
