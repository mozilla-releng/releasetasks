import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE


class TestPartnerRepacks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    tasks = None
    partner_tasks = None
    eme_free_tasks = None
    sha1_tasks = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'source_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'partner_repacks_platforms': ['win32', 'linux'],
            'release_channels': ['foo', 'bar'],
            'en_US_config': {
                "platforms": {
                    "linux": {"task_id": "xyz"},
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
        })
        self.graph = make_task_graph(**test_kwargs)
        self.partner_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_partner_repacks".format(platform))
            for platform in ["win32", "linux"]
        ]
        self.eme_free_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_eme_free_repacks".format(platform))
            for platform in ["win32", "linux"]
        ]
        self.sha1_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_sha1_repacks".format(platform))
            for platform in ["win32", "linux"]
        ]
        self.tasks = self.partner_tasks + self.eme_free_tasks + self.sha1_tasks

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

    def test_partner_manifests(self):
        for t in self.partner_tasks:
            self.assertEqual(t["task"]["payload"]["properties"]["repack_manifests_url"],
                             "git@github.com:mozilla-partners/repack-manifests.git")

    def test_eme_free_manifests(self):
        for t in self.eme_free_tasks:
            self.assertEqual(t["task"]["payload"]["properties"]["repack_manifests_url"],
                             "https://github.com/mozilla-partners/mozilla-EME-free-manifest")

    def test_sha1_free_manifests(self):
        for t in self.sha1_tasks:
            self.assertEqual(t["task"]["payload"]["properties"]["repack_manifests_url"],
                             "https://github.com/mozilla-partners/mozilla-sha1-manifest")

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

    def test_eme_free_requires(self):
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
                "release-foo-firefox-{}_eme_free_repacks".format(platform))

            requires = [
                get_task_by_name(self.graph, t)["taskId"]
                for t in upstream
            ]
            self.assertEqual(sorted(partner_repacks["requires"]), sorted(requires))

    def test_sha1_requires(self):
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
                "release-foo-firefox-{}_sha1_repacks".format(platform))

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
            eme_free = get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_eme_free_repacks".format(platform))
            sha1 = get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_sha1_repacks".format(platform))
            self.assertNotIn(eme_free["taskId"], push_to_mirrors["requires"])
            self.assertNotIn(sha1["taskId"], push_to_mirrors["requires"])

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
        ] + [
            get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_eme_free_repacks".format(platform))["taskId"]
            for platform in ["win32", "linux"]
        ] + [
            get_task_by_name(
                self.graph,
                "release-foo-firefox-{}_sha1_repacks".format(platform))["taskId"]
            for platform in ["win32", "linux"]
        ]

        self.assertEqual(
            sorted(partner_push_to_mirrors["requires"]),
            sorted(repacks_task_ids + [push_to_mirrors["taskId"]]))
