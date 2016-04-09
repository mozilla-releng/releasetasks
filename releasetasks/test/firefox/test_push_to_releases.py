import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE

EN_US_CONFIG = {
    "platforms": {
        "macosx64": {"task_id": "xyz"},
        "win32": {"task_id": "xyy"}
    }
}


L10N_CONFIG = {
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
}


AUTO_INIT_ITEMS = dict(
    version="42.0b2",
    next_version="42.0b3",
    appVersion="42.0",
    buildNumber=3,
    source_enabled=False,
    checksums_enabled=True,
    updates_enabled=True,
    bouncer_enabled=False,
    push_to_candidates_enabled=True,
    push_to_releases_enabled=True,
    beetmover_candidates_bucket='fake_bucket',
    postrelease_version_bump_enabled=False,
    postrelease_bouncer_aliases_enabled=False,
    en_US_config=EN_US_CONFIG,
    l10n_config=L10N_CONFIG,
    partial_updates={
        "38.0": {
            "buildNumber": 1,
            "locales": ["de", "en-GB", "zh-TW"],
        },
        "37.0": {
            "buildNumber": 2,
            "locales": ["de", "en-GB", "zh-TW"],
        },
    },
    branch="mozilla-beta",
    repo_path="releases/mozilla-beta",
    product="firefox",
    revision="abcdef123456",
    mozharness_changeset="abcd",
    balrog_api_root="https://balrog.real/api",
    funsize_balrog_api_root="http://balrog/api",
    signing_class="release-signing",
    verifyConfigs={},
    signing_pvt_key=PVT_KEY_FILE,
    release_channels=["beta", "release"],
    final_verify_channels=["beta", "release"],
    build_tools_repo_path='build/tools',
)
HUMAN_INIT_ITEMS = AUTO_INIT_ITEMS.copy()
HUMAN_INIT_ITEMS["push_to_releases_automatic"] = False
AUTO_INIT_ITEMS["push_to_releases_automatic"] = True


class TestPushToMirrorsHuman(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    human_task_name = "release-{}_{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "firefox")

    def setUp(self):
        self.graph = make_task_graph(**HUMAN_INIT_ITEMS)
        self.task = get_task_by_name(
            self.graph, "release-{}_{}_push_to_releases".format("mozilla-beta", "firefox")
        )
        self.human_task = get_task_by_name(self.graph, self.human_task_name)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "opt-linux64")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task["task"])

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64"
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_version_in_command(self):
        command = self.task['task']['payload']['command']
        self.assertTrue("--version 42.0b2" in "".join(command))

    def test_build_num_in_command(self):
        command = self.task['task']['payload']['command']
        self.assertTrue("--build-number 3" in "".join(command))

    def test_requires(self):
        requires = [get_task_by_name(self.graph, self.human_task_name)["taskId"]]
        self.assertEqual(self.task["requires"], requires)

    def test_human_provisioner(self):
        self.assertEqual(self.human_task["task"]["provisionerId"], "null-provisioner")

    def test_human_worker_type(self):
        self.assertEqual(self.human_task["task"]["workerType"], "human-decision")

    def test_human_requires(self):
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
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-firefox_chcksms")["taskId"])
        self.assertEqual(sorted(self.human_task["requires"]), sorted(requires))


class TestPushToMirrorsAutomatic(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    human_task_name = "release-{}_{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "firefox")

    def setUp(self):
        self.graph = make_task_graph(**AUTO_INIT_ITEMS)
        self.task = get_task_by_name(
            self.graph, "release-{}_{}_push_to_releases".format("mozilla-beta", "firefox")
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "opt-linux64")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task["task"])

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64"
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_version_in_command(self):
        command = self.task['task']['payload']['command']
        self.assertTrue("--version 42.0b2" in "".join(command))

    def test_build_num_in_command(self):
        command = self.task['task']['payload']['command']
        self.assertTrue("--build-number 3" in "".join(command))

    def test_human_decision_is_none(self):
        self.assertIsNone(get_task_by_name(self.graph, self.human_task_name))

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
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-firefox_chcksms")["taskId"])
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))
