import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE

EN_US_CONFIG = {
    "platforms": {
        "macosx64": {"task_id": "xyz"},
        "win32": {"task_id": "xyy"}
    }
}


class TestSnapBuilder(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'snap_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'signing_pvt_key': PVT_KEY_FILE,
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task_def = get_task_by_name(self.graph, "foo_snap")
        self.task = self.task_def["task"]
        self.payload = self.task["payload"]
        self.signing_task_def = get_task_by_name(self.graph,
                                                 "foo_snap_signing")
        self.signing_task = self.signing_task_def["task"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner_id(self):
        assert self.task["provisionerId"] == "aws-provisioner-v1"

    def test_worker_type(self):
        assert self.task["workerType"] == "opt-linux64"

    def test_image_name(self):
        assert "firefox-snapcraft" in self.payload["image"]

    def test_artifacts_in_payload(self):
        assert "artifacts" in self.payload

    def test_env_in_payload(self):
        assert "env" in self.payload

    def test_command_in_payload(self):
        assert "command" in self.payload

    def test_graph_scopes(self):

        expected_graph_scopes = set([
            "docker-worker:image:taskcluster/builder:*",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64",
            "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
            "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
            "project:releng:signing:format:gpg",
            "project:releng:signing:cert:release-signing",
        ])
        assert expected_graph_scopes.issubset(self.graph["scopes"])

    def test_task_scopes(self):
        expected_task_scopes = set([
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64",
            "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
            "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
        ])
        assert expected_task_scopes.issubset(self.task["scopes"])

    def test_signing_task_requirements(self):
        assert self.signing_task_def["requires"][0] == self.task_def["taskId"]

    def test_signing_task_provisioner(self):
        assert self.signing_task["provisionerId"] == "signing-provisioner-v1"

    def test_signing_task_worker_type(self):
        assert self.signing_task["workerType"] == "signing-worker-v1"

    def test_signing_task_scopes(self):
        expected_task_scopes = set([
            "project:releng:signing:format:gpg",
            "project:releng:signing:cert:release-signing"
        ])
        assert expected_task_scopes.issubset(self.signing_task["scopes"])

    def test_signing_manifest(self):
        assert "signingManifest" in self.signing_task["payload"]

    def test_signing_task_payload_length(self):
        assert len(self.signing_task["payload"]) == 1

    def test_version_in_payload(self):
        self.assertEqual(self.payload["env"]["VERSION"], "42.0b2")
