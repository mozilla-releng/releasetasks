import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestUpdates(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    props = None

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            en_US_config={
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
            l10n_config={},
            repo_path="releases/foo",
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
            bouncer_enabled=True,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            postrelease_version_bump_enabled=True,
            postrelease_bouncer_aliases_enabled=False,
            signing_class="release-signing",
            release_channels=["foo", "bar"],
            final_verify_channels=["foo", "beta"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )
        self.task = get_task_by_name(
            self.graph, "release-foo-firefox_updates")
        self.props = self.task["task"]["payload"]["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"],
                         "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_requires(self):
        tmpl = "release-foo_firefox_{}_complete_en-US_beetmover_candidates"
        requires = [
            get_task_by_name(self.graph, tmpl.format(p))["taskId"]
            for p in ("linux", "linux64", "macosx64", "win32", "win64")
        ]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))

    def test_repo_path(self):
        self.assertEqual(self.props["repo_path"], "releases/foo")

    def test_script_repo_revision(self):
        self.assertEqual(self.props["script_repo_revision"], "abcd")

    def test_partials(self):
        self.assertEqual(self.props["partial_versions"],
                         "37.0build2, 38.0build1")

    def test_balrog(self):
        self.assertEqual(self.props["balrog_api_root"], "https://balrog.real/api")

    def test_platforms(self):
        self.assertEqual(self.props["platforms"],
                         "linux, linux64, macosx64, win32, win64")

    def test_channels(self):
        self.assertEqual(self.props["channels"], "bar, foo")
