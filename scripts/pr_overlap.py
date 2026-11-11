"""Verify exact inherited-source certificates; never ignore a PR by number.

The trusted host reviews purpose/baseline and pins fresh provider observations.
This verifier proves bytes/history/patch inclusion, not semantic correctness.
"""
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile

from code_worker import child_env, command, path_ok

_SHA = re.compile(r'[0-9a-f]{40}')
_MAX_SOURCE = 2 * 1024 * 1024


def _sha(value):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise ValueError('overlap_pin_required')
    return value


def _blob(repository, commit, path):
    listing = command(['git', 'ls-tree', '-z', commit, '--', path], repository)
    if not listing or listing.split(' ', 1)[0] not in ('100644', '100755'):
        raise ValueError('overlap_regular_source_required')
    sha = command(['git', 'rev-parse', commit + ':' + path], repository)
    _sha(sha)
    size = int(command(['git', 'cat-file', '-s', sha], repository))
    if size > _MAX_SOURCE:
        raise ValueError('overlap_source_size_limit')
    return sha


def _patch(repository, base, head, path):
    proc = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
        'diff', '--full-index', '--no-ext-diff', '--no-textconv', '--no-renames', '--binary',
        '--src-prefix=a/', '--dst-prefix=b/', base, head, '--', path], cwd=repository,
        env=child_env(), capture_output=True, timeout=10)
    if proc.returncode or not proc.stdout or len(proc.stdout) > 2 * _MAX_SOURCE:
        raise ValueError('overlap_nonempty_bounded_patch_required')
    return proc.stdout


def verify_overlap_review(candidate, pr, repository):
    """Return True only when all shared paths have exact, fresh source proofs.

    equivalent_blob: complete current source is identical across histories.
    ancestor_blob: complete PR source equals a verified historical ancestor blob
      of candidate input (later corrections may supersede that old source).
    included_patch: the exact pinned per-file PR diff reverse-checks against a
      private index containing candidate input. The real index/tree are untouched.
    """
    try:
        task = candidate['task']
        target = _sha(task['base_sha'])
        head = _sha(pr['head_sha'])
        base = _sha(pr['base_sha'])
        review = candidate.get('overlap_reviews', {}).get(str(pr['number']))
        if (not isinstance(review, dict) or review.get('reviewed') is not True
                or not isinstance(review.get('reason'), str) or not 1 <= len(review['reason']) <= 1500
                or review.get('candidate_base_sha') != target or review.get('head_sha') != head
                or review.get('pr_base_sha') != base):
            raise ValueError('reviewed_overlap_pins_required')
        shared = set(pr['changed_paths']) & set(task['allowed_paths'])
        files = review.get('files')
        if not shared or not isinstance(files, dict) or set(files) != shared:
            raise ValueError('exact_overlap_path_coverage_required')
        repository = Path(repository)
        for path in sorted(shared):
            if not path_ok(path) or any(c in path for c in '*?[]\x00\n\r'):
                raise ValueError('overlap_exact_safe_path_required')
            proof = files[path]
            if not isinstance(proof, dict):
                raise ValueError('overlap_proof_required')
            target_blob = _blob(repository, target, path)
            head_blob = _blob(repository, head, path)
            if proof.get('candidate_blob') != target_blob or proof.get('head_blob') != head_blob:
                raise ValueError('overlap_source_blob_mismatch')
            mode = proof.get('mode')
            if mode == 'equivalent_blob':
                if target_blob != head_blob:
                    raise ValueError('overlap_source_not_equivalent')
            elif mode == 'ancestor_blob':
                witness = _sha(proof.get('witness_commit'))
                command(['git', 'merge-base', '--is-ancestor', witness, target], repository)
                if _blob(repository, witness, path) != head_blob:
                    raise ValueError('overlap_ancestor_blob_mismatch')
            elif mode == 'included_patch':
                patch = _patch(repository, base, head, path)
                if proof.get('patch_sha256') != hashlib.sha256(patch).hexdigest():
                    raise ValueError('overlap_patch_digest_mismatch')
                # Use a private index AND object directory. Only existing immutable
                # objects are read from the original repository through alternates.
                objects = Path(command(['git', 'rev-parse', '--git-path', 'objects'], repository))
                if not objects.is_absolute():
                    objects = repository / objects
                with tempfile.TemporaryDirectory(prefix='pokerid-pr-proof-') as directory:
                    temp = Path(directory)
                    (temp / 'objects').mkdir()
                    env = child_env()
                    env.update(GIT_INDEX_FILE=str(temp / 'index'),
                               GIT_OBJECT_DIRECTORY=str(temp / 'objects'),
                               GIT_ALTERNATE_OBJECT_DIRECTORIES=str(objects.resolve()))
                    command(['git', 'read-tree', target], repository, env=env)
                    proc = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                        '-c', 'core.fsmonitor=false', 'apply', '--cached', '--reverse', '--check',
                        '--whitespace=nowarn'], cwd=repository, env=env, input=patch,
                        capture_output=True, timeout=10)
                    if proc.returncode:
                        raise ValueError('overlap_patch_not_included')
            else:
                raise ValueError('unsupported_overlap_proof')
        return True
    except (KeyError, TypeError, OSError, RuntimeError, subprocess.SubprocessError):
        # No candidate prose, source content or raw tool/auth error enters logs.
        raise ValueError('overlap_proof_unavailable') from None
