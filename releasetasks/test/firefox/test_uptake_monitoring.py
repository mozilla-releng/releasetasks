import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema
from voluptuous.humanize import validate_with_humanized_errors


class TestUptakeMonitoring(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'buildbot-bridge',
            'workerType': 'buildbot-bridge',
            'payload': {
                'properties': {
                    'product': 'firefox',
                    'version': '42.0b2',
                    'build_number': 3,
                    'repo_path': 'releases/foo',
                    'script_repo_revision': 'abcd',
                    'revision': 'abcdef123456',
                    'tuxedo_server_url': 'https://bouncer.real.allizom.org/api',
                }
            }
        }
    }, extra=True, required=True)

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'uptake_monitoring_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_uptake_monitoring_task(self):
        assert validate_with_humanized_errors(self.task, TestUptakeMonitoring.TASK_SCHEMA)

    def test_scopes_present(self):
        self.assertTrue("scopes" in self.task['task'])

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")["taskId"]]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))
