"""Host coordinator bridge. Does not impersonate or spawn a collaboration agent.

Prepare -> formal host collaboration dispatch -> finish with coordinator receipt.
The host's tools/permissions remain the authority; this command adds no capability.
"""
import argparse
import json
from pathlib import Path
from code_worker import prepare_host_session, finish_host_session, validate_spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'finish'))
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--repository', type=Path)
    parser.add_argument('--work-root', type=Path)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True, help='coordinator-owned lease receipt, outside agent worktree')
    parser.add_argument('--receipt', type=Path, help='trusted coordinator records the actual formal collaboration agent')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.phase == 'prepare':
        if not args.manifest or not args.repository or not args.work_root:
            parser.error('prepare requires manifest, repository and work-root')
        spec = validate_spec(json.loads(args.manifest.read_text()))
        tasks = [task for task in spec['tasks'] if task['id'] == args.task_id]
        if len(tasks) != 1:
            parser.error('reviewed task ID missing')
        args.work_root.mkdir(parents=True, exist_ok=True)
        result = prepare_host_session(args.repository.resolve(), args.work_root.resolve(), args.state.resolve(), tasks[0])
        if result['status'] == 'prepared':
            # Never commit or give this coordinator-only lease token to the model.
            args.prepared.write_text(json.dumps(result, indent=2))
            args.prepared.chmod(0o600)
        public = {key: value for key, value in result.items() if key != 'lease_token'}
    else:
        if args.receipt is None:
            parser.error('finish requires coordinator receipt')
        prepared = json.loads(args.prepared.read_text())
        if prepared['id'] != args.task_id:
            parser.error('prepared task mismatch')
        public = finish_host_session(args.state.resolve(), args.task_id, prepared['lease_token'], json.loads(args.receipt.read_text()))
    args.output.write_text(json.dumps(public, indent=2))
    print(json.dumps(public, indent=2))
    return 0 if public['status'] in ('prepared', 'implemented_local') else 2


if __name__ == '__main__':
    raise SystemExit(main())
