import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE


class TestUpdates(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    props = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'bouncer_enabled': True,
            'push_to_candidates_enabled': True,
            'postrelease_version_bump_enabled': True,
            'updates_builder_enabled': True,
            'release_channels': ['foo', 'bar'],
            'final_verify_channels': ['foo', 'beta'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                'platforms': {
                    'macosx64': {'task_id': 'abc'},
                    'win32': {'task_id': 'def'},
                    'win64': {'task_id': 'ghi'},
                    'linux': {'task_id': 'jkl'},
                    'linux64': {'task_id': 'mno'},
                }
            }
        })
        self.graph = make_task_graph(**test_kwargs)
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
