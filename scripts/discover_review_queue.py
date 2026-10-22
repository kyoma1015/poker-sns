"""Offline suggestion preview only; never a state or execution authority."""
import json
import os
from pathlib import Path
import stat
import sys

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from continuation_recovery import digest, extract_candidates

MAX_BYTES = 1024 * 1024


def preview(sources):
    """Return deterministic non-executable review metadata without opening state."""
    if type(sources) is not list or len(sources) > 100:
        raise ValueError('invalid review sources')
    for source in sources:
        if (type(source) is not dict or type(source.get('lane')) is not str
                or source['lane'] not in ('A', 'B', 'C', 'D')
                or type(source.get('reference')) is not str
                or type(source.get('text')) is not str):
            raise ValueError('invalid review source')
    items = {}
    for suggestion in extract_candidates(sources):
        metadata = {key: suggestion[key] for key in ('lane', 'reference', 'title')}
        ident = digest(metadata)
        items[ident] = {'id': ident, **metadata, 'status': 'review_required', 'owner': None}
    return {'version': 1, 'executable': False, 'count': len(items),
            'items': [items[ident] for ident in sorted(items)]}


def read_sources(path):
    """Read a bounded regular file using the opened descriptor, not a path check."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_BYTES:
            raise ValueError('invalid review source file')
        raw = bytearray()
        while len(raw) <= MAX_BYTES:
            chunk = os.read(descriptor, min(65536, MAX_BYTES + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) > MAX_BYTES:
            raise ValueError('review source file exceeds limit')
        return json.loads(raw.decode('utf-8'))
    finally:
        os.close(descriptor)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] != '--sources':
        print('review queue preview input rejected', file=sys.stderr)
        return 2
    try:
        result = preview(read_sources(args[1]))
    except (OSError, ValueError, UnicodeError, RecursionError):
        print('review queue preview input rejected', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
