import unittest

from releasetasks.test.firefox import make_task_graph, get_task_by_name, \
    do_common_assertions
from releasetasks.test import PVT_KEY_FILE


class TestL10NSingleChunk(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None
    properties = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            push_to_releases_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
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
                    "linux64": {
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
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_class="release-signing",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
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

    def test_repo_path(self):
        self.assertEqual(self.payload["properties"]["repo_path"],
                         "releases/mozilla-beta")

    def test_script_repo_revision(self):
        self.assertEqual(self.payload["properties"]["script_repo_revision"],
                         "abcd")

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

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                task_name = "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_update_generator".format(
                    pl=pl, part=part)
                self.assertIsNotNone(get_task_by_name(
                    self.graph, task_name))


class TestL10NMultipleChunks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    chunk1 = None
    chunk2 = None
    chunk1_properties = None
    chunk2_properties = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            push_to_releases_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
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
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
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
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            signing_class="release-signing",
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )
        self.chunk1 = get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.chunk2 = get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")
        self.chunk1_properties = self.chunk1["task"]["payload"]["properties"]
        self.chunk2_properties = self.chunk2["task"]["payload"]["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_chunk1_buildername(self):
        self.assertEqual(
            self.chunk1["task"]["payload"]["buildername"],
            "release-mozilla-beta_firefox_win32_l10n_repack")

    def test_chunk1_locales(self):
        self.assertEqual(self.chunk1_properties["locales"],
                         "de:default en-GB:default ru:default")

    def test_chunk1_en_us_binary_url(self):
        self.assertEqual(
            self.chunk1_properties["en_us_binary_url"],
            "https://queue.taskcluster.net/something/firefox.exe")

    def test_chunk2_buildername(self):
        self.assertEqual(
            self.chunk2["task"]["payload"]["buildername"],
            "release-mozilla-beta_firefox_win32_l10n_repack")

    def test_chunk2_locales(self):
        self.assertEqual(self.chunk2_properties["locales"],
                         "uk:default zh-TW:default")

    def test_chunk2_en_us_binary_url(self):
        self.assertEqual(
            self.chunk2_properties["en_us_binary_url"],
            "https://queue.taskcluster.net/something/firefox.exe")

    def test_chunk1_repo_path(self):
        self.assertEqual(self.chunk1_properties["repo_path"],
                         "releases/mozilla-beta")

    def test_chunk1_script_repo_revision(self):
        self.assertEqual(self.chunk1_properties["script_repo_revision"],
                         "abcd")

    def test_chunk2_repo_path(self):
        self.assertEqual(self.chunk2_properties["repo_path"],
                         "releases/mozilla-beta")

    def test_chunk2_script_repo_revision(self):
        self.assertEqual(self.chunk2_properties["script_repo_revision"],
                         "abcd")

    def test_no_chunk3(self):
        self.assertIsNone(get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_3"))

    def test_chunk1_artifacts_task_present(self):
        # make sure artifacts tasks are present
        self.assertIsNotNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))

    def test_chunk2_artifacts_task_present(self):
        self.assertIsNotNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))

    def test_no_chunk3_artifacts(self):
        self.assertIsNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_3"))

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                for chunk in [1, 2]:
                    task_name1 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_update_generator".format(
                        pl=pl, part=part, chunk=chunk)
                    task_name2 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_signing_task".format(
                        pl=pl, part=part, chunk=chunk)
                    self.assertIsNotNone(get_task_by_name(
                        self.graph, task_name1))
                    self.assertIsNotNone(get_task_by_name(
                        self.graph, task_name2))


class TestL10NNewLocales(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            push_to_releases_enabled=False,
            beetmover_candidates_bucket="bucket",
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            enUS_platforms=["win32"],
            en_US_config={"platforms": {
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
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
                    "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "ru", "uk"],
                },
            },
            signing_class="release-signing",
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_new_locale_not_in_update_generator(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_1_37.0_update_generator")
        self.assertEqual(
            sorted(["de", "en-GB", "ru", "uk"]),
            sorted([p["locale"] for p in t["task"]["extra"]["funsize"]["partials"]]))

    def test_new_locale_in_update_generator(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_1_38.0_update_generator")
        self.assertEqual(sorted(["de", "en-GB", "ru", "uk", "zh-TW"]),
                         sorted([p["locale"] for p in t["task"]["extra"]["funsize"]["partials"]]))

    def test_new_locale_not_in_beetmover(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_partial_37.0build2_beetmover_candidates_1")
        self.assertNotIn("--locale zh-TW",  " ".join(t["task"]["payload"]["command"]))
        self.assertIn("--locale en-GB", " ".join(t["task"]["payload"]["command"]))

    def test_new_locale_in_beetmover(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_partial_38.0build1_beetmover_candidates_1")
        self.assertIn("--locale zh-TW", " ".join(t["task"]["payload"]["command"]))
        self.assertIn("--locale en-GB", " ".join(t["task"]["payload"]["command"]))
