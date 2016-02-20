import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


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
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            l10n_config={},
            repo_path="releases/mozilla-beta",
            revision="fedcba654321",
            branch="beta",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            checksums_enabled=False,
            postrelease_version_bump_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta"],
            build_tools_repo_path='build/tools',
            balrog_api_root="http://balrog/api",
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.task = get_task_by_name(self.graph, "release-beta_win32_update_verify_beta_3")
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

    def test_all_builders_exist(self):
        for p in ['win32', 'win64', 'macosx64']:
            for i in range(1, 7):  # test full chunk size
                self.assertIsNotNone(
                    get_task_by_name(
                        self.graph,
                        "release-beta_%s_update_verify_beta_%s" % (p, i)
                    )
                )
