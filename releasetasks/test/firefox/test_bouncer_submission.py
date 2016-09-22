import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE


class TestBouncerSubmission(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'bouncer_enabled': True,
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
        self.task = get_task_by_name(self.graph,
                                     "release-foo_firefox_bncr_sub")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task)

    def test_partials(self):
        self.assertEqual(self.payload["properties"]["partial_versions"],
                         "37.0build2, 38.0build1")

    def test_build_number(self):
        self.assertEqual(self.payload["properties"]["build_number"], 3)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_repo_path(self):
        self.assertEqual(self.payload["properties"]["repo_path"],
                         "releases/foo")

    def test_script_repo_revision(self):
        self.assertEqual(self.payload["properties"]["script_repo_revision"],
                         "abcd")
