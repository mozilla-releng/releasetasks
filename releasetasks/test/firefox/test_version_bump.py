import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestVersionBump(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    def setUp(self):
        test_kwargs = create_test_args({
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

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"],
                         "buildbot-bridge")

    def test_human_provisioner(self):
        self.assertEqual(self.human_task["task"]["provisionerId"],
                         "null-provisioner")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_human_worker_type(self):
        self.assertEqual(self.human_task["task"]["workerType"],
                         "human-decision")

    def test_next_version(self):
        self.assertEqual(self.payload["properties"]["next_version"], "42.0b3")

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_requires(self):
        self.assertIn(self.human_task["taskId"], self.task["requires"])

    def test_repo_path(self):
        self.assertEqual(self.payload["properties"]["repo_path"],
                         "releases/foo")

    def test_script_repo_revision(self):
        self.assertEqual(self.payload["properties"]["script_repo_revision"],
                         "abcd")
