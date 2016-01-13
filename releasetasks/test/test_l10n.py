import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    get_task_by_name, \
    do_common_assertions


class TestL10NSingleChunk(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None
    properties = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            enUS_platforms=["win32"],
            en_US_config={"platforms": {
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
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
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.payload = self.task["task"]["payload"]
        self.properties = self.payload["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task_present(self):
        self.assertIsNotNone(self.task)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_buildername(self):
        self.assertEqual(self.payload["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")

    def test_locales(self):
        self.assertEqual(self.properties["locales"], "de:default en-GB:default zh-TW:default")

    def test_en_us_binary_url(self):
        self.assertEqual(self.properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")

    def test_only_one_chunk_1(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_0"))

    def test_only_one_chunk_2(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2"))

    def test_artifacts_task_present(self):
        self.assertIsNotNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))

    def test_artifacts_task_only_one_chunk_1(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_0"))

    def test_artifacts_task_only_one_chunk_2(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))

    def test_artifacts_task_provisioner(self):
        art_task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.assertEqual(art_task["task"]["provisionerId"], "null-provisioner")

    def test_artifacts_task_worker_type(self):
        art_task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.assertEqual(art_task["task"]["workerType"], "buildbot")


class TestL10NMultipleChunks(unittest.TestCase):
    maxDiff = 30000

    def test_l10n_multiple_chunks(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            enUS_platforms=["win32"],
            en_US_config={"platforms": {
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 2,
                    },
                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "ru": "default",
                    "uk": "default",
                    "zh-TW": "default",
                },
            },
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            signing_class="release-signing",
            balrog_api_root="https://fake.balrog/api",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )

        do_common_assertions(graph)

        chunk1 = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        chunk2 = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")

        chunk1_properties = chunk1["task"]["payload"]["properties"]
        chunk2_properties = chunk2["task"]["payload"]["properties"]

        self.assertEqual(chunk1["task"]["payload"]["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")
        self.assertEqual(chunk1_properties["locales"], "de:default en-GB:default ru:default")
        self.assertEqual(chunk1_properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")
        self.assertEqual(chunk2["task"]["payload"]["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")
        self.assertEqual(chunk2_properties["locales"], "uk:default zh-TW:default")
        self.assertEqual(chunk2_properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")

        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_3"))

        # make sure artifacts tasks are present
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_3"))
        # partials
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_1_37.0_update_generator"))
