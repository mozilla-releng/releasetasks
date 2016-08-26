import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestChecksums(unittest.TestCase):
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
                    "win64": {"task_id": "jgh"},
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
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            branch="foo",
            updates_enabled=True,
            bouncer_enabled=False,
            checksums_enabled=True,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            signing_class="release-signing",
            release_channels=["foo"],
            final_verify_channels=["foo"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
            publish_to_balrog_channels=None,
        )
        self.task = get_task_by_name(self.graph, "release-foo-firefox_chcksms")
        self.payload = self.task["task"]["payload"]

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

    def test_version(self):
        self.assertEqual(self.payload["properties"]["version"], "42.0b2")

    def test_build_number(self):
        self.assertEqual(self.payload["properties"]["build_number"], "3")

    def test_requires(self):
        tmpl = "release-foo_firefox_{p}_complete_en-US_beetmover_candidates"
        tmpl_partials = "release-foo_firefox_{p}_partial_en-US_{v}build{b}_beetmover_candidates"
        requires = [
            get_task_by_name(self.graph, tmpl.format(p=p))["taskId"]
            for p in ("linux64", "macosx64", "win64")
        ] + [
            get_task_by_name(self.graph, tmpl_partials.format(p=p, v=v, b=b))["taskId"]
            for p in ("linux64", "macosx64", "win64")
            for v, b in [("37.0", 2), ("38.0", 1)]
        ]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))
