import unittest

from releasetasks.test.desktop import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import All, Length, Schema, truth

EN_US_CONFIG = {
    "platforms": {
        "macosx64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
        "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
    }
}


class TestSnapBuilder(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "docker-worker:image:taskcluster/builder:*",
                "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
                "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
                "project:releng:signing:format:gpg",
                "project:releng:signing:cert:release-signing",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'scopes': generate_scope_validator(scopes={
                    "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                    "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
                    "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
                    "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
                }),
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
                'payload': {
                    'image': str,
                    'command': list,
                    'artifacts': dict,
                    'env': {
                        'VERSION': '42.0b2',
                    },
                }
            }
        }, extra=True, required=True)

        self.signing_task_schema = Schema({
            'task': {
                'scopes': generate_scope_validator(scopes={
                    "project:releng:signing:format:gpg",
                    "project:releng:signing:cert:release-signing",
                }),
                'provisionerId': 'signing-provisioner-v1',
                'workerType': 'signing-worker-v1',
                'payload': All(Length(1), {
                    'signingManifest': str,
                })
            }

        }, required=True, extra=True)

        test_kwargs = create_firefox_test_args({
            'snap_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'signing_pvt_key': PVT_KEY_FILE,
        })

        self.graph = make_task_graph(**test_kwargs)

        self.task = get_task_by_name(self.graph, "foo_snap")
        self.signing_task = get_task_by_name(self.graph, "foo_snap_signing")

    @staticmethod
    @truth
    def validate_task_payload(task):
        return 'firefox-snapcraft' in task['task']['payload']['image']

    # Returns a validator for signing task dependencies
    def generate_signing_task_dependency_validator(self):
        requires = self.task['taskId']

        @truth
        def validate_signing_task_dependencies(signing_task):
            return requires in signing_task['requires']

        return validate_signing_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_task(self):
        verify(self.task, self.task_schema, TestSnapBuilder.validate_task_payload)

    def test_signing_task(self):
        verify(self.signing_task, self.signing_task_schema, self.generate_signing_task_dependency_validator())
