import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


class TestVersionBump(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            l10n_config={},
            repo_path="releases/foo",
            product="firefox",
            revision="fedcba654321",
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=True,
            push_to_candidates_enabled=False,
            postrelease_version_bump_enabled=True,
            signing_class="release-signing",
            release_channels=["foo"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task = get_task_by_name(
            self.graph, "release-foo-firefox_version_bump")
        self.human_task = get_task_by_name(
            self.graph, "release-foo-firefox_version_bump_human_decision")
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
                         "fedcba654321")
