import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema
from voluptuous.humanize import validate_with_humanized_errors


class TestVersionBump(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'buildbot-bridge',
            'workerType': 'buildbot-bridge',
            'payload': {
                'properties': {
                    'next_version': '42.0b3',
                    'repo_path': 'releases/foo',
                    'script_repo_revision': 'abcd',
                }
            }
        }
    }, extra=True, required=True)

    HUMAN_TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'null-provisioner',
            'workerType': 'human-decision',
        }
    }, extra=True, required=True)

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'bouncer_enabled': True,
            'postrelease_version_bump_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(
            self.graph, "release-foo-firefox_version_bump")
        self.human_task = get_task_by_name(
            self.graph, "publish_release_human_decision")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_version_bump_task(self):
        assert validate_with_humanized_errors(self.task, TestVersionBump.TASK_SCHEMA)

    def test_version_bump_human_task(self):
        assert validate_with_humanized_errors(self.human_task, TestVersionBump.HUMAN_TASK_SCHEMA)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_requires(self):
        self.assertIn(self.human_task["taskId"], self.task["requires"])
