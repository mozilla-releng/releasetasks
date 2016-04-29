import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestUptakeMonitoring(unittest.TestCase):
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
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
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
            updates_enabled=False,
            bouncer_enabled=False,
            checksums_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            push_to_releases_automatic=False,
            uptake_monitoring_enabled=True,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            tuxedo_server_url="https://bouncer.real.allizom.org/api",
            signing_class="release-signing",
            release_channels=["foo"],
            final_verify_channels=["foo"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task = get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"],
                         "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_scopes_present(self):
        self.assertTrue("scopes" in self.task['task'])

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")["taskId"]]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))

    def test_product(self):
        self.assertEqual(self.payload["properties"]["product"],
                         "firefox")

    def test_version(self):
        self.assertEqual(self.payload["properties"]["version"],
                         "42.0b2")

    def test_build_number(self):
        self.assertEqual(self.payload["properties"]["build_number"], 3)

    def test_repo_path(self):
        self.assertEqual(self.payload["properties"]["repo_path"],
                         "releases/foo")

    def test_script_repo_revision(self):
        self.assertEqual(self.payload["properties"]["script_repo_revision"],
                         "abcd")

    def test_revision(self):
        self.assertEqual(self.payload["properties"]["revision"],
                         "fedcba654321")

    def test_tuxedo_server_url(self):
        self.assertEqual(self.payload["properties"]["tuxedo_server_url"],
                         "https://bouncer.real.allizom.org/api")
