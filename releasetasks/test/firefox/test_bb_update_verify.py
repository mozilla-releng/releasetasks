import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestBB_UpdateVerify(unittest.TestCase):
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
                    "macosx64": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"},
                    "win64": {"task_id": "xyw"}
                }
            },
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
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "win64": {
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
            repo_path="releases/mozilla-beta",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            branch="beta",
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            beetmover_candidates_bucket='fake_bucket',
            checksums_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            update_verify_enabled=True,
            updates_builder_enabled=True,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            build_tools_repo_path='build/tools',
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
            publish_to_balrog_channels=None,
        )
        self.task = get_task_by_name(self.graph, "release-beta_firefox_win32_update_verify_beta_3")
        self.payload = self.task["task"]["payload"]
        self.properties = self.payload["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_required_property(self):
        self.assertEqual(self.payload['properties']['NO_BBCONFIG'], "1")
        self.assertEqual(self.payload['properties']['VERIFY_CONFIG'],
                         "beta-firefox-win32.cfg")

    def test_chunking_info(self):
        self.assertEqual(self.payload['properties']['TOTAL_CHUNKS'], "12")
        self.assertEqual(self.payload['properties']['THIS_CHUNK'], "3")

    def test_all_builders_exist(self):
        for p in ['win32', 'win64', 'macosx64']:
            for i in range(1, 7):  # test full chunk size
                self.assertIsNotNone(
                    get_task_by_name(
                        self.graph,
                        "release-beta_firefox_%s_update_verify_beta_%s" % (p, i)
                    )
                )

    def test_requires(self):
        en_US_tmpl = "release-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-beta_firefox_{}_partial_en-US_{}build{}_beetmover_candidates"
        l10n_tmpl = "release-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-beta_firefox_{}_l10n_repack_partial_{}build{}_beetmover_candidates_1"
        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                get_task_by_name(self.graph, completes.format(p))["taskId"]
                for p in ("macosx64", "win32", "win64")
            ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl):
            requires.extend([
                get_task_by_name(self.graph, partials.format(platform, p_version, p_build_num))["taskId"]
                for platform in ("macosx64", "win32", "win64")
                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
            ])
        requires.append(get_task_by_name(self.graph, "release-beta-firefox_updates")["taskId"])
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))


class TestBB_UpdateVerifyMultiChannel(unittest.TestCase):
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
                    "macosx64": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"},
                    "win64": {"task_id": "xyw"}
                }
            },
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
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "win64": {
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
            repo_path="releases/mozilla-beta",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            branch="beta",
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            beetmover_candidates_bucket='fake_bucket',
            checksums_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            update_verify_enabled=True,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta", "release"],
            build_tools_repo_path='build/tools',
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
            publish_to_balrog_channels=None,
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_multichannel(self):
        for chan in ["beta", "release"]:
            task = get_task_by_name(
                self.graph, "release-beta_firefox_win32_update_verify_{chan}_3".format(chan=chan)
            )
            self.assertEqual(task["task"]["provisionerId"], "buildbot-bridge")
            self.assertEqual(task["task"]["workerType"], "buildbot-bridge")
            self.assertFalse("scopes" in task)
            self.assertEqual(task["task"]["payload"]['properties']['VERIFY_CONFIG'],
                             "{chan}-firefox-win32.cfg".format(chan=chan))
