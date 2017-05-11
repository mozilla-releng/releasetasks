import unittest

from releasetasks.test.desktop import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import All, Length, Match, Schema, truth

EN_US_CONFIG = {
    "platforms": {
        "linux": {"unsigned_task_id": "xyz", "signed_task_id": "xxy"},
        "win32": {"unsigned_task_id": "xyz", "signed_task_id": "xxy"},
    }
}


class TestSourceBuilder(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "docker-worker:cache:tc-vcs",
                "docker-worker:image:taskcluster/builder:*",
                "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
                "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
                "docker-worker:cache:build-foo-release-workspace",
                "docker-worker:cache:tooltool-cache",
                "project:releng:signing:format:gpg",
                "project:releng:signing:cert:release-signing",
                "docker-worker:relengapi-proxy:tooltool.download.public",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'scopes': generate_scope_validator(scopes={
                    "docker-worker:cache:tc-vcs",
                    "docker-worker:image:taskcluster/builder:0.5.9",
                    "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                    "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
                    "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
                    "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
                    "docker-worker:cache:build-foo-release-workspace",
                    "docker-worker:cache:tooltool-cache",
                    "docker-worker:relengapi-proxy:tooltool.download.public",
                }),
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
                'payload': {
                    'artifacts': dict,
                    'command': list,
                    'cache': dict,
                    'image': Match(r'^rail/source-builder@sha256'),
                    'env': {
                        'MOZ_PKG_VERSION': '42.0b2',
                    }
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
                'payload': All({
                    'signingManifest': str,
                }, Length(1))
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'source_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "foo_source")
        self.signing_task = get_task_by_name(self.graph, "foo_source_signing")

    # Returns a validator for task dependencies
    def generate_task_requires_validator(self):
        requires = self.signing_task['requires'][0]

        @truth
        def validate_task_requires(task):
            return requires == task['taskId']

        return validate_task_requires

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_source_builder_task(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_source_builder_signing_task(self):
        verify(self.signing_task, self.signing_task_schema)


class TestSourceBuilderPushToMirrors(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'source_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'release_channels': ['foo', 'bar'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
        })
        self.graph = make_task_graph(**test_kwargs)

        self.push_to_mirrors = get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")
        self.foo_source_signing_beet = get_task_by_name(self.graph, "foo_source_signing_beet")
        self.foo_source_beet = get_task_by_name(self.graph, "foo_source_beet")

    def generate_source_dependency_validator(self):
        requires = self.push_to_mirrors['requires']

        @truth
        def validate_source_dependencies(task):
            return task['taskId'] in requires

        return validate_source_dependencies

    def generate_source_signing_dependency_validator(self):
        requires = self.push_to_mirrors['requires']

        @truth
        def validate_source_signing_dependencies(task):
            return task['taskId'] in requires

        return validate_source_signing_dependencies

    def test_source_task(self):
        verify(self.foo_source_beet, self.generate_source_dependency_validator())

    def test_source_signing_task(self):
        verify(self.foo_source_signing_beet, self.generate_source_signing_dependency_validator())
