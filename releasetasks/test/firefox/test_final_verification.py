import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestFinalVerification(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        test_args = create_test_args({
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'final_verify_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'enUS_platforms': ["linux", "linux64", "win64", "win32", "macosx64"],
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
        self.graph = make_task_graph(**test_args)
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

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")["taskId"]]
        self.assertEqual(sorted(self.task_def["requires"]), sorted(requires))


class TestFinalVerificationMultiChannel(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_kwargs = create_test_args({
            'push_to_releases_enabled': True,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'final_verify_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
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


class TestFinalVerifyNoMirrors(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'repo_path': 'releases/mozilla-beta',
            'branch': 'mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'enUS_platforms': ["win32", "macosx64"],
            'final_verify_platforms': ["macosx64", "win32"],
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "macosx64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },

                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "zh-TW": "default",
                },
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task_def = get_task_by_name(self.graph, "beta_final_verify")
        self.task = self.task_def["task"]
        self.payload = self.task["payload"]

    def test_requires(self):
        en_US_tmpl = "release-mozilla-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-mozilla-beta_firefox_{}_partial_en-US_{}build{}_beetmover_candidates"
        l10n_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_partial_{}build{}_beetmover_candidates_1"
        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                get_task_by_name(self.graph, completes.format(p))["taskId"]
                for p in ("macosx64", "win32")
            ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl):
            requires.extend([
                get_task_by_name(self.graph, partials.format(platform, p_version, p_build_num))["taskId"]
                for platform in ("macosx64", "win32")
                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
            ])
        self.assertEqual(sorted(self.task_def["requires"]), sorted(requires))
