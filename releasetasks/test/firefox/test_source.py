import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args, scope_check_factory
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Match, Schema
from voluptuous.humanize import validate_with_humanized_errors

EN_US_CONFIG = {
    "platforms": {
        "linux": {"task_id": "xyz"},
        "win32": {"task_id": "xyy"}
    }
}


class TestSourceBuilder(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    SIGNING_TASK_SCHEMA = Schema({
        'scopes': scope_check_factory(scopes={
            "project:releng:signing:format:gpg",
            "project:releng:signing:cert:release-signing",
        }),
        'task': {
            'provisionerId': 'signing-provisioner-v1',
            'workerType': 'signing-worker-v1',
        }
    }, extra=True)

    GRAPH_SCHEMA = Schema({
        'scopes': scope_check_factory(scopes={
            "docker-worker:cache:tc-vcs",
            "docker-worker:image:taskcluster/builder:*",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64",
            "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
            "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
            "docker-worker:cache:build-foo-release-workspace",
            "docker-worker:cache:tooltool-cache",
            "project:releng:signing:format:gpg",
            "project:releng:signing:cert:release-signing",
            "docker-worker:relengapi-proxy:tooltool.download.public",
        })
    }, extra=True, required=True)

    TASK_SCHEMA = Schema({
        'scopes': scope_check_factory(scopes={
            "docker-worker:cache:tc-vcs",
            "docker-worker:image:taskcluster/builder:0.5.9",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64",
            "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
            "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
            "docker-worker:cache:build-foo-release-workspace",
            "docker-worker:cache:tooltool-cache",
            "docker-worker:relengapi-proxy:tooltool.download.public",
        }),
        'task': {
            'provisionerId': 'opt-linux64',
            'workerType': 'aws-provisioner-v1',
            'payload': {
                'image': Match(r'^rail/source-builder@sha256'),
                'env': {
                    'MOZ_PKG_VERSION': '42.0b2',
                }
            }
        }
    }, extra=True)

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'source_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task_def = get_task_by_name(self.graph, "foo_source")
        self.task = self.task_def["task"]
        self.payload = self.task["payload"]
        self.signing_task_def = get_task_by_name(self.graph,
                                                 "foo_source_signing")
        self.signing_task = self.signing_task_def["task"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_source_builder_task(self):
        assert validate_with_humanized_errors(self.task, TestSourceBuilder.TASK_SCHEMA)

    def test_source_builder_signing_task(self):
        assert validate_with_humanized_errors(self.signing_task, TestSourceBuilder.SIGNING_TASK_SCHEMA)

    def test_cache_in_payload(self):
        assert "cache" in self.payload

    def test_artifacts_in_payload(self):
        assert "artifacts" in self.payload

    def test_env_in_payload(self):
        assert "env" in self.payload

    def test_command_in_payload(self):
        assert "command" in self.payload

    def test_signing_task_requirements(self):
        assert self.signing_task_def["requires"][0] == self.task_def["taskId"]

    def test_signing_manifest(self):
        assert "signingManifest" in self.signing_task["payload"]

    def test_signing_task_payload_length(self):
        assert len(self.signing_task["payload"]) == 1


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

    def test_source_required_by_push_to_mirrors(self):
        push_to_mirrors = get_task_by_name(
            self.graph, "release-foo_firefox_push_to_releases")
        foo_source_beet = get_task_by_name(self.graph, "foo_source_beet")
        self.assertIn(foo_source_beet["taskId"], push_to_mirrors["requires"])

    def test_source_sig_required_by_push_to_mirrors(self):
        push_to_mirrors = get_task_by_name(
            self.graph, "release-foo_firefox_push_to_releases")
        foo_source_signing_beet = get_task_by_name(self.graph,
                                                   "foo_source_signing_beet")
        self.assertIn(foo_source_signing_beet["taskId"],
                      push_to_mirrors["requires"])
