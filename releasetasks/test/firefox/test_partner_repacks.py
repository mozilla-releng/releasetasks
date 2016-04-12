import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph
from releasetasks.test import PVT_KEY_FILE


class TestPartnerRepacks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    tasks = None

    def setUp(self):
        self.graph = make_task_graph(
            product="firefox",
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=True,
            checksums_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux": {
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
            repo_path="releases/foo",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            push_to_releases_automatic=True,
            release_channels=["foo", "bar"],
            balrog_api_root="https://balrog.real/api",
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            partner_repacks_platforms=["win32", "linux"],
        )
        self.tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_partner_repacks".format(platform))
            for platform in ["win32", "linux"]]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        for t in self.tasks:
            self.assertEqual(t["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        for t in self.tasks:
            self.assertEqual(t["task"]["workerType"], "buildbot-bridge")

    def test_version(self):
        for t in self.tasks:
            self.assertEqual(t["task"]["payload"]["properties"]["version"], "42.0b2")

    def test_build_number(self):
        for t in self.tasks:
            self.assertEqual(t["task"]["payload"]["properties"]["build_number"], 3)

    def test_requires(self):
        upstream = [
            "release-foo_firefox_{}_complete_en-US_beetmover_candidates".format(platform)
            for platform in ["win32", "linux"]
        ] + [
            "release-foo_firefox_{}_l10n_repack_beetmover_candidates_1".format(platform)
            for platform in ["win32", "linux"]
        ]

        for platform in ["win32", "linux"]:
            partner_repacks = get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_partner_repacks".format(platform))

            requires = [
                get_task_by_name(self.graph, t)["taskId"]
                for t in upstream
            ]
            self.assertEqual(sorted(partner_repacks["requires"]), sorted(requires))

    def test_not_required_by_push_to_mirrors(self):
        push_to_mirrors = get_task_by_name(
            self.graph, "release-foo_firefox_push_to_releases")
        for platform in ["win32", "linux"]:
            partner_repacks = get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_partner_repacks".format(platform))
            self.assertNotIn(partner_repacks["taskId"],
                             push_to_mirrors["requires"])

    def test_partner_push_to_releases_requires(self):
        partner_push_to_mirrors = get_task_by_name(
            self.graph, "release-foo-firefox_partner_repacks_copy_to_releases")
        push_to_mirrors = get_task_by_name(
            self.graph, "release-foo_firefox_push_to_releases")
        repacks_task_ids = [
            get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_partner_repacks".format(platform))["taskId"]
            for platform in ["win32", "linux"]
        ]

        self.assertEqual(
            sorted(partner_push_to_mirrors["requires"]),
            sorted(repacks_task_ids + [push_to_mirrors["taskId"]]))
