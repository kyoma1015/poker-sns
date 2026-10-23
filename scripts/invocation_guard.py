"""Opt-in invocation exclusion and cooperative limits, not a worker or daemon."""
from pathlib import Path
import re
import sys
import time

from code_worker import WorkerLivenessUnknown, finite_lease_number, setup_lock


class InvocationGuard:
    def __init__(self, controller, run_id, owner, enabled=False, max_seconds=1800):
        if enabled is not True:
            raise ValueError('invocation guard requires explicit enablement')
        if (not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', run_id)
                or not isinstance(owner, str) or not re.fullmatch(r'[A-Za-z0-9_./@-]{1,100}', owner)):
            raise ValueError('invalid invocation identity')
        max_seconds = finite_lease_number(max_seconds, 'invocation duration')
        if not 0 < max_seconds <= 1800:
            raise ValueError('invocation duration must be within 1800 seconds')
        self.controller = controller
        self.run_id = run_id
        self.owner = owner
        self.max_seconds = max_seconds
        self._path = Path(controller.path)
        self._stop = self._path.with_suffix('.stop')
        self._lock = None
        self._active = False
        self._deadline = None

    def _check_stop(self):
        if self._stop.exists() or self._stop.is_symlink():
            raise RuntimeError('invocation stop requested')

    def __enter__(self):
        if self._active:
            raise ValueError('invocation guard already active')
        lock = setup_lock(self._path.with_suffix('.invocation.lock'), seconds=0)
        try:
            lock.__enter__()
        except RuntimeError:
            raise TimeoutError('invocation lock unavailable') from None
        try:
            self._check_stop()
            if self.controller.db.execute(
                    "SELECT 1 FROM development_jobs WHERE status='running' LIMIT 1").fetchone():
                raise ValueError('running job requires review; no automatic takeover')
            start = finite_lease_number(time.monotonic(), 'invocation clock')
            self._deadline = finite_lease_number(start + self.max_seconds, 'invocation deadline')
            if not self.controller.reserve_run(self.run_id):
                raise ValueError('invocation already reserved or finite limit reached')
            self._lock = lock
            self._active = True
            self.check()
            return self
        except BaseException:
            self._active = False
            self._lock = None
            lock.__exit__(*sys.exc_info())
            raise

    def check(self):
        if not self._active:
            raise ValueError('invocation guard is inactive')
        self._check_stop()
        if finite_lease_number(time.monotonic(), 'invocation clock') >= self._deadline:
            raise TimeoutError('invocation deadline reached')

    def call_host(self, dispatch, *, observe, preserve):
        """Opt-in trusted synchronous boundary; never starts an agent or scheduler.

        observe must positively attest this invocation's agent is stopped, before
        and after dispatch. preserve must durably retain private local results and
        partial work before this method can return or propagate a stop/deadline.
        Callbacks are trusted host functions, not task-descriptor instructions.
        They remain responsible for deadlines, identity, atomic persistence and
        actual agent cancellation. This method cannot interrupt a blocked callback.
        Existing prepare/finish, receipt and source/test checks remain mandatory.
        """
        if not all(callable(callback) for callback in (dispatch, observe, preserve)):
            raise ValueError('trusted host callbacks required')
        self.check()

        def stopped():
            try:
                return observe() == 'stopped'
            except BaseException:
                return False

        if not stopped():
            raise WorkerLivenessUnknown('Host liveness unconfirmed; dispatch forbidden')
        self.check()
        result = None
        error = None
        try:
            result = dispatch()
        except BaseException as caught:
            error = caught
        confirmed = stopped()
        status = {'outcome': 'raised' if error is not None else 'returned',
                  'liveness': 'stopped' if confirmed else 'unknown'}
        try:
            preserve(result, status)
        except BaseException:
            raise WorkerLivenessUnknown('Host preservation unconfirmed; continuation forbidden') from None
        if not confirmed:
            raise WorkerLivenessUnknown('Host liveness unconfirmed; continuation forbidden') from None
        self.check()
        if error is not None:
            raise error
        return result

    def __exit__(self, exc_type, exc, traceback):
        lock = self._lock
        self._lock = None
        self._active = False
        if lock is not None:
            return lock.__exit__(exc_type, exc, traceback)
        return False
