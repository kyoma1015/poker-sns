"""Opt-in invocation exclusion and cooperative limits, not a worker or daemon."""
from pathlib import Path
import re
import sys
import time

from code_worker import finite_lease_number, setup_lock


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

    def __exit__(self, exc_type, exc, traceback):
        lock = self._lock
        self._lock = None
        self._active = False
        if lock is not None:
            return lock.__exit__(exc_type, exc, traceback)
        return False
