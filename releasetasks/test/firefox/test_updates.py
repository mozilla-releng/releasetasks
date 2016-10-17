import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema
from voluptuous.humanize import validate_with_humanized_errors


class TestUpdates(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    props = None

    TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'buildbot-bridge',
            'workerType': 'buildbot-bridge',
            'payload': {
                'properties': {
                    'repo_path': 'releases/foo',
                    'script_repo_revision': 'abcd',
                    'partial_versions': '37.0build2, 38.0build1',
                    'balrog_api_root': 'https://balrog.real/api',
                    'platforms': 'linux, linux64, macosx64, win32, win64',
                    'channels': 'bar, foo',
                }
            }
        }
    }, extra=True, required=True)

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

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_updates_task(self):
        assert validate_with_humanized_errors(self.task, TestUpdates.TASK_SCHEMA)

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
