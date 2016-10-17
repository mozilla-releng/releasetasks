import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema


class TestMarkAsShipped(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    HUMAN_TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'null-provisioner',
            'workerType': 'human-decision',
        }
    })

    TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'buildbot-bridge',
            'workerType': 'buildbot-bridge',
            'payload': {
                'next_version': '42.0b3',
                'properties': {
                    'repo_path': 'releases/foo',
                    'script_repo_revision': 'abcd',
                }
            }
        }
    })

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'bouncer_enabled': True,
            'postrelease_mark_as_shipped_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'final_verify_channels': ['foo'],
            'release_channels': ['foo'],
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
            self.graph, "release-foo-firefox_mark_as_shipped")
        self.human_task = get_task_by_name(
            self.graph, "publish_release_human_decision")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_requires(self):
        self.assertIn(self.human_task["taskId"], self.task["requires"])
