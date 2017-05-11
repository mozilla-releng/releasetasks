import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestVersionBump(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

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
                        'next_version': '42.0b3',
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                    }
                }
            }
        }, extra=True, required=True)

        self.human_task_schema = Schema({
            'task': {
                'provisionerId': 'null-provisioner',
                'workerType': 'human-decision',
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'bouncer_enabled': True,
            'postrelease_version_bump_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_version_bump")
        self.human_task = get_task_by_name(self.graph, "publish_release_human_decision")

    def generate_task_dependency_validator(self):
        human_task_id = self.human_task['taskId']

        @truth
        def validate_task_dependencies(task):
            return human_task_id in task['requires']

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_version_bump_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())

    def test_version_bump_human_task(self):
        verify(self.human_task, self.human_task_schema)
