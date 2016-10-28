import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestUpdates(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    props = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
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
        self.task = get_task_by_name(self.graph, "release-foo-firefox_updates")

    # Returns a task dependency validator
    def generate_task_dependency_validator(self):
        tmpl = "release-foo_firefox_{}_complete_en-US_beetmover_candidates"
        requires = [get_task_by_name(self.graph, tmpl.format(p))["taskId"] for p in ("linux", "linux64", "macosx64", "win32", "win64",)]

        @truth
        def validate_task_dependencies(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_updates_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())
