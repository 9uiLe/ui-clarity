"""Repository policy: direct master pushes run read-only, pinned CI."""

from pathlib import Path
import re
import shlex
import unittest

import yaml


class WorkflowPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / '.github/workflows/ci.yml'
        # BaseLoader preserves the Actions key `on` rather than YAML 1.1's boolean.
        cls.workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)

    def test_only_master_push_and_manual_events(self):
        events = self.workflow['on']
        self.assertIn('push', events)
        self.assertEqual(events['push']['branches'], ['master'])
        self.assertLessEqual(set(events), {'push', 'workflow_dispatch'})

    def test_tokens_are_read_only_and_not_persisted(self):
        self.assertEqual(self.workflow['permissions'], {'contents': 'read'})
        for job in self.workflow['jobs'].values():
            self.assertNotIn('permissions', job)
            for step in job['steps']:
                if step.get('uses', '').startswith('actions/checkout@'):
                    self.assertEqual(step['with']['persist-credentials'], 'false')

    def test_actions_are_pinned_and_jobs_are_bounded(self):
        for job in self.workflow['jobs'].values():
            self.assertEqual(job['runs-on'], 'ubuntu-24.04')
            self.assertLessEqual(int(job['timeout-minutes']), 10)
            for step in job['steps']:
                if 'uses' in step:
                    self.assertRegex(step['uses'], re.compile(r'^[\w.-]+/[\w.-]+@[0-9a-f]{40}$'))

    def test_repository_validation_and_tests_are_required(self):
        job = self.workflow['jobs']['repository']
        self.assertNotIn('if', job)
        self.assertNotIn('continue-on-error', job)
        commands = {step.get('run'): step for step in job['steps'] if 'run' in step}
        for command in (
            "python -m unittest discover -s tests -p 'test_*.py' -v",
            'python tests/check_repository.py',
        ):
            self.assertIn(command, commands)
            self.assertNotIn('if', commands[command])
            self.assertNotIn('continue-on-error', commands[command])

    def test_secret_scan_covers_history_and_fails_on_detection(self):
        job = self.workflow['jobs']['secrets']
        self.assertNotIn('if', job)
        self.assertNotIn('continue-on-error', job)
        checkouts = [s for s in job['steps'] if s.get('uses', '').startswith('actions/checkout@')]
        self.assertTrue(any(s['with'].get('fetch-depth') == '0' for s in checkouts))
        scans = []
        for step in job['steps']:
            args = shlex.split(step.get('run', ''))
            if len(args) > 1 and args[0].endswith('/gitleaks') and args[1] == 'git':
                scans.append(step)
                self.assertIn('--redact', args)
                self.assertIn('--log-opts=--all', args)
                self.assertFalse(any(arg.startswith('--exit-code') for arg in args))
                self.assertNotIn('if', step)
                self.assertNotIn('continue-on-error', step)
        self.assertTrue(scans, 'Git history must be scanned for secrets')


if __name__ == '__main__':
    unittest.main()
