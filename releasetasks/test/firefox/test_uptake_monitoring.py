import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestUptakeMonitoring(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
            l10n_config={},
            repo_path="releases/foo",
            build_tools_repo_path='build/tools',
            product="firefox",
            revision="fedcba654321",
            mozharness_changeset="abcd",
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
            bouncer_enabled=False,
            checksums_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            push_to_releases_automatic=False,
            postrelease_version_bump_enabled=False,
            signing_class="release-signing",
            release_channels=["foo"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task = get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")
        self.human_task = get_task_by_name(
            self.graph, "release-foo-firefox_uptake_monitoring_human_decision")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_human_provisioner(self):
        self.assertEqual(self.human_task["task"]["provisionerId"], "null-provisioner")

    def test_human_worker_type(self):
        self.assertEqual(self.human_task["task"]["workerType"], "human-decision")

    def test_human_requires(self):
        requires = [get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")["taskId"]]
        self.assertEqual(sorted(self.human_task["requires"]), sorted(requires))

    def test_provisioner_id(self):
        assert self.task['task']["provisionerId"] == "aws-provisioner-v1"

    def test_worker_type(self):
        assert self.task['task']["workerType"] == "opt-linux64"

    def test_image_name(self):
        assert self.payload["image"] == 'ubuntu'

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task['task'])

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring_human_decision")["taskId"]]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))

    def test_sleep_in_command(self):
        command = self.task['task']['payload']['command']
        self.assertTrue(
            "for i in {1..10}; do echo wait...sleep...good dog && sleep 1m; done" in "".join(command)
        )
