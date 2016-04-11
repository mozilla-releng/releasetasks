import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph
from releasetasks.test import PVT_KEY_FILE


class TestSourceBuilder(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        self.graph = make_task_graph(
            product="firefox",
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=True,
            checksums_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=False,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )
        self.task_def = get_task_by_name(self.graph, "foo_source")
        self.task = self.task_def["task"]
        self.payload = self.task["payload"]
        self.signing_task_def = get_task_by_name(self.graph,
                                                 "foo_source_signing")
        self.signing_task = self.signing_task_def["task"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner_id(self):
        assert self.task["provisionerId"] == "aws-provisioner-v1"

    def test_worker_type(self):
        assert self.task["workerType"] == "opt-linux64"

    def test_image_name(self):
        assert self.payload["image"].startswith("taskcluster/desktop-build:")

    def test_cache_in_payload(self):
        assert "cache" in self.payload

    def test_artifacts_in_payload(self):
        assert "artifacts" in self.payload

    def test_env_in_payload(self):
        assert "env" in self.payload

    def test_command_in_payload(self):
        assert "command" in self.payload

    def test_graph_scopes(self):

        expected_graph_scopes = set([
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
            "docker-worker:relengapi-proxy:tooltool.download.public"
        ])
        assert expected_graph_scopes.issubset(self.graph["scopes"])

    def test_task_scopes(self):
        expected_task_scopes = set([
            "docker-worker:cache:tc-vcs",
            "docker-worker:image:taskcluster/builder:0.5.9",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64",
            "queue:define-task:aws-provisioner-v1/build-c4-2xlarge",
            "queue:create-task:aws-provisioner-v1/build-c4-2xlarge",
            "docker-worker:cache:build-foo-release-workspace",
            "docker-worker:cache:tooltool-cache",
            "docker-worker:relengapi-proxy:tooltool.download.public",
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

    def test_pkg_version_in_payload(self):
        self.assertEqual(self.payload["env"]["MOZ_PKG_VERSION"], "42.0b2")


class TestSourceBuilderPushToMirrors(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        self.graph = make_task_graph(
            product="firefox",
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=True,
            checksums_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            push_to_releases_automatic=True,
            release_channels=["foo", "bar"],
            balrog_api_root="https://balrog.real/api",
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )

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
