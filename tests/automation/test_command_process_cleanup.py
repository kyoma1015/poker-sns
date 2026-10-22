"""Actual subprocess command timeout; fixture descendants only, no external CLI."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from code_worker import command
from test_worker_recovery_lifecycle import wait_dead


class CommandProcessCleanup(unittest.TestCase):
    def test_timed_out_command_does_not_leave_its_child_executing(self):
        with tempfile.TemporaryDirectory(prefix='owned-command-qa-') as directory:
            ids_file = Path(directory) / 'owned-pids.json'
            code = '''
import subprocess,sys,os,json,time
from pathlib import Path
child=subprocess.Popen([sys.executable,'-c',"import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('READY',flush=True);time.sleep(30)"],stdout=subprocess.PIPE,text=True)
assert child.stdout.readline().strip()=='READY'
Path('owned-pids.json').write_text(json.dumps({'leader':os.getpid(),'child':child.pid}))
while True:time.sleep(.1)
'''
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    command([sys.executable,'-B','-c',code],directory,timeout=.5)
                ids = json.loads(ids_file.read_text())
                self.assertTrue(wait_dead(ids['leader']))
                self.assertTrue(wait_dead(ids['child']), 'command timeout left its descendant running')
            finally:
                if ids_file.exists():
                    ids = json.loads(ids_file.read_text())
                    try:
                        os.kill(ids['child'],signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == '__main__':
    unittest.main()
