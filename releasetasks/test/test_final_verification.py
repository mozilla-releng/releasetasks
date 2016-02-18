import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


class TestFinalVerification(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
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
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            postrelease_version_bump_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["foo"],
            balrog_api_root="http://balrog/api",
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task_def = get_task_by_name(self.graph, "foo_final_verify")
        self.task = self.task_def["task"]
        self.payload = self.task["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        self.assertEqual(self.task["workerType"], "b2gtest")

    def test_no_scopes_in_task(self):
        self.assertFalse("scopes" in self.task)

    def test_image(self):
        # XXX: Change the image name once it's in-tree.
        self.assertTrue(
            self.payload["image"].startswith("rail/python-test-runner"))

    def test_no_cache(self):
        self.assertFalse("cache" in self.payload)

    def test_no_artifacts(self):
        self.assertFalse("artifacts" in self.payload)

    def test_no_env(self):
        self.assertTrue("env" in self.payload)

    def test_command_present(self):
        self.assertTrue("command" in self.payload)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))


class TestFinalVerificationMultiChannel(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            postrelease_version_bump_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta", "release"],
            balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_multichannel(self):
        for chan in ["beta", "release"]:
            task_def = get_task_by_name(
                self.graph, "{chan}_final_verify".format(chan=chan))
            task = task_def["task"]
            payload = task["payload"]
            self.assertEqual(task["provisionerId"], "aws-provisioner-v1")
            self.assertEqual(task["workerType"], "b2gtest")
            self.assertFalse("scopes" in task)
            # XXX: Change the image name once it's in-tree.
            self.assertTrue(payload["image"].startswith("rail/python-test-runner"))
            self.assertFalse("cache" in payload)
            self.assertFalse("artifacts" in payload)
            self.assertTrue("env" in payload)
            self.assertTrue("command" in payload)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))
