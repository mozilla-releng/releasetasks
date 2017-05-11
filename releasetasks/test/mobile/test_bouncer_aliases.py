import unittest

from releasetasks.test.mobile import make_task_graph, do_common_assertions, \
    get_task_by_name, create_fennec_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestBouncerAliases(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'}),
        }, required=True, extra=True)

        self.push_to_mirrors_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        self.uptake_monitoring_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge'
            }
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'product': 'fennec',
                        'version': '42.0b2',
                        'build_number': 3,
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                        'revision': 'abcdef123456',
                        'tuxedo_server_url': 'https://bouncer.real.allizom.org/api',
                    }
                }
            }
        }, required=True, extra=True)

        test_kwargs = create_fennec_test_args({
            'push_to_releases_enabled': True,
            'postrelease_bouncer_aliases_enabled': True,
            'release_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "android-4-0-armv7-api15": {"task_id": "abc"},
                    "android-4-2-x86": {"task_id": "def"},
                }
            },
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-fennec_bouncer_aliases")
        self.push_to_mirrors = get_task_by_name(self.graph, "release-foo-fennec_push_to_releases")
        self.uptake_monitoring = get_task_by_name(self.graph, "release-foo-fennec_uptake_monitoring")

    def generate_task_dependency_validator(self):
        push_to_mirrors_task_id = self.push_to_mirrors['taskId']
        uptake_monitoring_task_id = self.uptake_monitoring['taskId']

        @truth
        def validate_task_dependencies(task):
            deps = [push_to_mirrors_task_id, uptake_monitoring_task_id]
            return all([dep in task['requires'] for dep in deps])

        return validate_task_dependencies

    def test_task(self):
        verify(self.task, self.task_schema)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_push_to_mirrors(self):
        verify(self.push_to_mirrors, self.push_to_mirrors_schema)

    def test_uptake_monitoring(self):
        verify(self.uptake_monitoring, self.uptake_monitoring)
