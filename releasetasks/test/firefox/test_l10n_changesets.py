import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph
from releasetasks.test import PVT_KEY_FILE


class TestL10NChangesets(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    task_beet = None

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
            l10n_changesets={"ab": "cd", "ef": "gh", "ij": "kl"},
        )
        self.task = get_task_by_name(self.graph, "foo_l10n_changeset")
        self.task_beet = get_task_by_name(self.graph, "foo_l10n_changeset_beet")

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "opt-linux64")

    def test_l10n_changesets_text(self):
        self.assertEqual(self.task["task"]["extra"]["l10n_changesets"],
                         "ab cd\nef gh\nij kl\n")
