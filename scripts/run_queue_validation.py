"""Run at most four allowlisted queue validations; never generate code or deploy."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from development_queue import LANES, Queue

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lane', choices=LANES)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / '.github/queues/development.json').read_text())
    queue = Queue(args.state, manifest)
    results = []
    try:
        lanes = (args.lane,) if args.lane else LANES
        for lane in lanes[:manifest['max_tasks_per_run']]:
            lease = queue.claim(lane)
            if lease is None:
                continue
            # A fixed trusted test command; manifest text is never executed.
            try:
                completed = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/automation/test_development_queue.py')],
                    cwd=ROOT, timeout=60, capture_output=True, text=True, check=False)
                log = completed.stdout + completed.stderr
                success = completed.returncode == 0
            except subprocess.TimeoutExpired:
                log, success = 'TIMEOUT: validation exceeded 60 seconds', False
            evidence = args.output / (lane + '-validation.log')
            evidence.write_text(log)
            status = queue.finish(lease['id'], lease['token'], success, str(evidence))
            results.append({'lane': lane, 'task': lease['id'], 'status': status})
        report = queue.report()
        report['this_run'] = results
        report['recurring_scheduler_verified'] = False
        (args.output / 'queue-report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 1 if any(row['status'] != 'succeeded' for row in results) else 0
    finally:
        queue.close()


if __name__ == '__main__':
    sys.exit(main())
